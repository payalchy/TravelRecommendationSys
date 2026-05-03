from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
import json
from django.shortcuts import render
from django.urls import reverse
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination, TravelPackage, PackageItinerary
from .engine import recommend_destinations, recommend_packages


# ---------------- HELPER FUNCTION ----------------

def convert_styles_to_weights(profile):
    styles = profile.preferred_travel_style.all()

    weights = {
        "culture": 0,
        "adventure": 0,
        "wildlife": 0,
        "sightseeing": 0,
        "history": 0,
    }

    if not styles:
        return {k: 0.2 for k in weights}

    weight_value = 1 / styles.count()

    for style in styles:
        name = style.name.lower()
        if name in weights:
            weights[name] = weight_value

    return weights


def _safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_request_location(request):
    payload = request.data if isinstance(request.data, dict) else {}

    latitude = _safe_float(payload.get("user_latitude"))
    longitude = _safe_float(payload.get("user_longitude"))

    if latitude is None and longitude is None:
        return None, None

    if latitude is None or longitude is None:
        return None, "Both user_latitude and user_longitude are required together."

    if latitude < -90 or latitude > 90:
        return None, "user_latitude must be between -90 and 90."

    if longitude < -180 or longitude > 180:
        return None, "user_longitude must be between -180 and 180."

    return (latitude, longitude), None


def _coerce_preferred_province(request):
    payload = request.data if isinstance(request.data, dict) else {}
    province = payload.get("preferred_province")
    if province is None:
        return None

    normalized = str(province).strip()
    return normalized or None


# ---------------- ADMIN DASHBOARD ----------------

@staff_member_required
def admin_dashboard(request):
    recent_packages = (
        TravelPackage.objects.select_related("start_location", "end_location")
        .order_by("-id")[:8]
    )

    context = {
        **admin.site.each_context(request),
        "total_destinations": Destination.objects.count(),
        "total_packages": TravelPackage.objects.count(),
        "total_itineraries": PackageItinerary.objects.count(),
        "recent_packages": recent_packages,
        "destination_changelist_url": reverse("admin:recommendation_destination_changelist"),
        "package_changelist_url": reverse("admin:recommendation_travelpackage_changelist"),
        "itinerary_changelist_url": reverse("admin:recommendation_packageitinerary_changelist"),
    }
    return render(request, "admin/custom_dashboard.html", context)


# ---------------- RECOMMENDATION API ----------------

class RecommendationAPIView(APIView):
    permission_classes = [IsAuthenticated]   # LOGIN REQUIRED

    def post(self, request):

        # ---------------- GET USER PROFILE ----------------
        user = request.user

        try:
            profile = user.userprofile
        except:
            return Response({"error": "UserProfile not found"}, status=404)

        request_location, location_error = _coerce_request_location(request)
        if location_error:
            return Response({"error": location_error}, status=status.HTTP_400_BAD_REQUEST)

        preferred_province = _coerce_preferred_province(request)

        profile_lat = float(profile.latitude) if profile.latitude is not None else 27.7172
        profile_lon = float(profile.longitude) if profile.longitude is not None else 85.3240
        resolved_lat, resolved_lon = request_location if request_location else (profile_lat, profile_lon)

        # ---------------- USER CONTEXT FROM PROFILE ----------------
        user_context = {
            "budget": profile.budget,
            "distance": 100,  # default fallback
            "duration": profile.preferred_duration,
            "travel_type": (
                profile.preferred_travel_style.first().name
                if profile.preferred_travel_style.exists()
                else ""
            ),
            "user_latitude": resolved_lat,
            "user_longitude": resolved_lon,
        }

        # ---------------- DESTINATION PREFERENCES (AUTO) ----------------
        user_destination_preferences = convert_styles_to_weights(profile)

        # ---------------- DEFAULT WEIGHTS ----------------
        preference_weights = {
            "budget": 0.3,
            "distance": 0.3,
            "duration": 0.2,
            "travel_type": 0.2,
        }

        context_weights = {
            "budget": 0.4,
            "distance": 0.3,
            "duration": 0.3,
        }

        destination_weights = {
            "culture": 0.2,
            "adventure": 0.2,
            "wildlife": 0.2,
            "sightseeing": 0.2,
            "history": 0.2,
        }

        # ---------------- PARAMETERS ----------------
        k = 5
        top_n = 5
        destination_top_n = 5

        alpha = 0.4
        beta = 0.4
        gamma = 0.2

        destination_alpha = 0.5
        destination_beta = 0.3
        destination_gamma = 0.2

        # ---------------- DATA ----------------
        packages = TravelPackage.objects.select_related("start_location", "end_location").all()
        destinations = Destination.objects.all()

        if preferred_province:
            packages = packages.filter(end_location__province__iexact=preferred_province)
            destinations = destinations.filter(province__iexact=preferred_province)

        # ---------------- PACKAGE RANKING ----------------
        ranked = recommend_packages(
            user_context=user_context,
            packages=packages,
            k=k,
            top_n=top_n,
            preference_weights=preference_weights,
            context_weights=context_weights,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
        )

        data = []
        for item in ranked:
            package = item.package
            data.append(
                {
                    "package_id": package.id,
                    "name": package.name,
                    "package_type": package.package_type,
                    "transport_mode": package.transport_mode,
                    "budget": float(package.budget),
                    "image": request.build_absolute_uri(package.image.url) if package.image else None,
                    "description": package.description,
                    "computed_distance_km": round(item.computed_distance_km, 6),
                    "duration_days": int(package.days),
                    "start_location": package.start_location.pName if package.start_location else None,
                    "end_location": package.end_location.pName if package.end_location else None,
                    "itinerary": [
                        {
                            "day": i.day_number,
                            "destination": i.destination.pName,
                            "description": i.description,
                        }
                        for i in package.itinerary.all()
                    ],
                    "cps": round(item.cps, 6),
                    "distance_score": round(item.distance, 6),
                    "cost_efficiency": round(item.cost_efficiency, 6),
                    "time_efficiency": round(item.time_efficiency, 6),
                    "final_score": round(item.final_score, 6),
                }
            )

        # ---------------- DESTINATION RANKING ----------------
        destination_ranked = recommend_destinations(
            user_destination_preferences=user_destination_preferences,
            user_context=user_context,
            destinations=destinations,
            ranked_packages=ranked,
            destination_top_n=destination_top_n,
            destination_weights=destination_weights,
            destination_alpha=destination_alpha,
            destination_beta=destination_beta,
            destination_gamma=destination_gamma,
        )

        destination_data = []
        for item in destination_ranked:
            destination = item.destination
            destination_data.append(
                {
                    "destination_id": destination.id,
                    "name": destination.pName,
                    "province": destination.province,
                    "latitude": destination.latitude,
                    "longitude": destination.longitude,
                    "culture": destination.culture,
                    "adventure": destination.adventure,
                    "wildlife": destination.wildlife,
                    "sightseeing": destination.sightseeing,
                    "history": destination.history,
                    "distance_km": round(item.distance_km, 6),
                    "preference_score": round(item.preference_score, 6),
                    "geo_score": round(item.geo_score, 6),
                    "package_support_score": round(item.package_support_score, 6),
                    "final_score": round(item.final_score, 6),
                }
            )

        return Response(
            {
                "package_count": len(data),
                "destination_count": len(destination_data),
                "used_user_location": {
                    "latitude": resolved_lat,
                    "longitude": resolved_lon,
                    "source": "request" if request_location else "profile",
                },
                "package_results": data,
                "destination_results": destination_data,
            },
            status=status.HTTP_200_OK,
        )


class DestinationProvinceListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        provinces = (
            Destination.objects.exclude(province__isnull=True)
            .exclude(province__exact="")
            .values_list("province", flat=True)
            .distinct()
            .order_by("province")
        )
        return Response({"provinces": list(provinces)}, status=status.HTTP_200_OK)


# ---------------- GEOCODE API ----------------

class DestinationGeocodeAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        destination_name = request.query_params.get("name", "").strip()
        if not destination_name:
            return Response(
                {"detail": "Query parameter 'name' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = f"{destination_name}, Nepal"
        params = urlencode({"q": query, "format": "json", "limit": 1})
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        req = Request(url, headers={"User-Agent": "travel-backend/1.0"})

        try:
            with urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return Response(
                {"detail": "Unable to fetch location right now."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not payload:
            return Response(
                {"detail": "No location found for this destination in Nepal."},
                status=status.HTTP_404_NOT_FOUND,
            )

        first = payload[0]
        return Response(
            {
                "name": destination_name,
                "latitude": float(first.get("lat")),
                "longitude": float(first.get("lon")),
                "display_name": first.get("display_name"),
            },
            status=status.HTTP_200_OK,
        )