from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
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
from .engine import recommend_destinations_direct, recommend_packages
from users.models import SearchHistory


# ---------------- HELPER FUNCTION ----------------

def convert_styles_to_preferences(profile):
    """
    Convert selected travel styles to preference values (0-5 scale).
    If user selects a style, set preference to 4.0 (high interest).
    If not selected, set to 1.0 (low interest).
    """
    styles = profile.preferred_travel_style.all()

    # Default: low interest in all categories
    preferences = {
        "culture": 1.0,
        "adventure": 1.0,
        "wildlife": 1.0,
        "sightseeing": 1.0,
        "history": 1.0,
    }

    # If user selected styles, set those to high interest (4.0)
    if styles:
        for style in styles:
            name = style.name.lower()
            if name in preferences:
                preferences[name] = 4.0

    return preferences


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


def _coerce_preferred_provinces(request):
    """Parse preferred_provinces from request (can be array or single value)"""
    payload = request.data if isinstance(request.data, dict) else {}
    provinces = payload.get("preferred_provinces")

    if provinces is None:
        return []
    
    if isinstance(provinces, list):
        # Filter out empty strings and normalize
        return [str(p).strip() for p in provinces if str(p).strip()]
    
    if isinstance(provinces, str):
        # Single province as string
        normalized = str(provinces).strip()
        return [normalized] if normalized else []
    
    return []


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
        "destination_changelist_url": reverse(
            "admin:recommendation_destination_changelist"
        ),
        "package_changelist_url": reverse(
            "admin:recommendation_travelpackage_changelist"
        ),
        "itinerary_changelist_url": reverse(
            "admin:recommendation_packageitinerary_changelist"
        ),
    }

    return render(request, "admin/custom_dashboard.html", context)


# ---------------- RECOMMENDATION API ----------------

class RecommendationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # ---------------- GET USER PROFILE ----------------

        user = request.user

        try:
            profile = user.userprofile
        except Exception:
            return Response(
                {"error": "UserProfile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        request_location, location_error = _coerce_request_location(request)

        if location_error:
            return Response(
                {"error": location_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        preferred_province = _coerce_preferred_province(request)
        request_provinces = _coerce_preferred_provinces(request)

        # ---------------- REQUEST OVERRIDES ----------------

        request_budget = _safe_float(request.data.get("budget"))
        request_duration = _safe_float(request.data.get("duration"))
        request_season = request.data.get("preferred_season")

        user_budget = (
            request_budget
            if request_budget is not None
            else profile.budget
        )

        user_duration = (
            request_duration
            if request_duration is not None
            else profile.preferred_duration
        )

        user_season = (
            request_season
            if request_season
            else profile.preferred_season or None
        )

        # ---------------- LOCATION ----------------

        profile_lat = (
            float(profile.latitude)
            if profile.latitude is not None
            else 27.7172
        )

        profile_lon = (
            float(profile.longitude)
            if profile.longitude is not None
            else 85.3240
        )

        resolved_lat, resolved_lon = (
            request_location
            if request_location
            else (profile_lat, profile_lon)
        )

        # ---------------- USER CONTEXT ----------------

        user_context = {
            "budget": user_budget,
            "distance": 100,
            "duration": user_duration,
            "travel_type": (
                profile.preferred_travel_style.first().name
                if profile.preferred_travel_style.exists()
                else ""
            ),
            "user_latitude": resolved_lat,
            "user_longitude": resolved_lon,
            "preferred_season": user_season,
        }

        # ---------------- DESTINATION PREFERENCES ----------------

        user_destination_preferences = convert_styles_to_preferences(profile)

        # ---------------- WEIGHTS ----------------

        destination_weights = {
            "culture": 0.2,
            "adventure": 0.2,
            "wildlife": 0.2,
            "sightseeing": 0.2,
            "history": 0.2,
        }

        # ---------------- PARAMETERS ----------------

        destination_top_n = 5

        destination_alpha = 0.45
        destination_beta = 0.25
        destination_gamma = 0.2
        destination_delta = 0.05
        destination_epsilon = 0.05

        # ---------------- DESTINATION QUERY ----------------

        destinations = Destination.objects.all()

        # Collect all provinces to filter by
        provinces_to_filter = []
        
        # Add request provinces if provided
        if request_provinces:
            provinces_to_filter.extend(request_provinces)
        
        # Add user's saved provinces
        user_provinces = profile.get_preferred_provinces() if hasattr(profile, 'get_preferred_provinces') else []
        if user_provinces:
            provinces_to_filter.extend(user_provinces)
        
        # If request had single preferred_province, add it
        if preferred_province:
            provinces_to_filter.append(preferred_province)
        
        # Remove duplicates and filter
        if provinces_to_filter:
            unique_provinces = list(set(provinces_to_filter))
            destinations = destinations.filter(province__in=unique_provinces)

        # ---------------- RECOMMENDATION ENGINE ----------------

        destination_ranked = recommend_destinations_direct(
            user_prefs=user_destination_preferences,
            user_context=user_context,
            destinations=destinations,
            top_n=destination_top_n,
        )

        # ---------------- RESPONSE DATA ----------------

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
                    "image": destination.image,
                    "culture": destination.culture,
                    "adventure": destination.adventure,
                    "wildlife": destination.wildlife,
                    "sightseeing": destination.sightseeing,
                    "history": destination.history,
                    "distance_km": round(item.distance_km, 6),
                    "preference_score": round(item.preference_score, 6),
                    "geo_score": round(item.geo_score, 6),
                    "attribute_alignment": round(
                        item.package_support_score, 6
                    ),
                    "final_score": round(item.final_score, 6),
                }
            )

        # ---------------- SAVE SEARCH HISTORY ----------------

        SearchHistory.objects.create(
            user=request.user,
            search_payload={
                "budget": user_budget,
                "duration": user_duration,
                "preferred_season": user_season,
                "preferred_province": preferred_province,
                "location": {
                    "latitude": resolved_lat,
                    "longitude": resolved_lon,
                },
            },
            destination_results=destination_data,
        )

        # ---------------- FINAL RESPONSE ----------------

        return Response(
            {
                "recommendation_type": "direct_destinations_6_algorithm",
                "pipeline": [
                    "CPS_with_constraints",
                    "C_KNN_weighted_euclidean",
                    "Proximity_efficiency",
                    "Weighted_scoring",
                ],
                "destination_count": len(destination_data),
                "used_user_location": {
                    "latitude": resolved_lat,
                    "longitude": resolved_lon,
                    "source": (
                        "request"
                        if request_location
                        else "profile"
                    ),
                },
                "constraints_applied": {
                    "budget_npr": user_budget,
                    "duration_days": user_duration,
                    "preferred_season": user_season,
                },
                "user_preferences": user_destination_preferences,
                "destination_results": destination_data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------- DESTINATION PROVINCES API ----------------

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

        return Response(
            list(provinces),
            status=status.HTTP_200_OK,
        )


# ---------------- DESTINATION SEARCH API ----------------

class DestinationSearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        query = str(request.query_params.get("q", "")).strip()

        if not query:
            return Response(
                {"results": []},
                status=status.HTTP_200_OK,
            )

        destinations = (
            Destination.objects.filter(
                Q(pName__icontains=query)
                | Q(province__icontains=query)
                | Q(tags__icontains=query)
            )
            .order_by("pName")
            .distinct()[:30]
        )

        results = []

        for destination in destinations:

            results.append(
                {
                    "destination_id": destination.id,
                    "name": destination.pName,
                    "province": destination.province,
                    "latitude": destination.latitude,
                    "longitude": destination.longitude,
                    "image": destination.image,
                    "culture": destination.culture,
                    "adventure": destination.adventure,
                    "wildlife": destination.wildlife,
                    "sightseeing": destination.sightseeing,
                    "history": destination.history,
                }
            )

        return Response(
            {"results": results},
            status=status.HTTP_200_OK,
        )


# ---------------- DESTINATION GEOCODE API ----------------

class DestinationGeocodeAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        destination_name = request.query_params.get(
            "name",
            "",
        ).strip()

        if not destination_name:
            return Response(
                {
                    "detail": "Query parameter 'name' is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = f"{destination_name}, Nepal"

        params = urlencode(
            {
                "q": query,
                "format": "json",
                "limit": 1,
            }
        )

        url = f"https://nominatim.openstreetmap.org/search?{params}"

        req = Request(
            url,
            headers={
                "User-Agent": "travel-backend/1.0"
            },
        )

        try:
            with urlopen(req, timeout=10) as response:
                payload = json.loads(
                    response.read().decode("utf-8")
                )

        except Exception:
            return Response(
                {
                    "detail": "Unable to fetch location right now."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not payload:
            return Response(
                {
                    "detail": "No location found for this destination in Nepal."
                },
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
# ---------------- DESTINATION PACKAGES API ----------------

class DestinationPackagesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, destination_id):

        try:
            destination = Destination.objects.get(id=destination_id)

        except Destination.DoesNotExist:
            return Response(
                {
                    "error": f"Destination with id {destination_id} not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        packages = (
            TravelPackage.objects.filter(
                end_location_id=destination_id
            )
            .select_related(
                "start_location",
                "end_location",
            )
            .all()
        )

        package_data = []

        for pkg in packages:

            # ---------------- SAFE FIELD ACCESS ----------------

            duration = getattr(pkg, "days", None)
            budget = getattr(pkg, "budget", None)
            transport_mode = getattr(pkg, "transport_mode", None)
            package_type = getattr(pkg, "package_type", None)

            # ---------------- ITINERARY ----------------

            itinerary_data = []

            itineraries = (
                PackageItinerary.objects.filter(package=pkg)
                .select_related("destination")
                .order_by("day_number")
            )

            for itinerary in itineraries:

                itinerary_image = None

                if itinerary.image:
                    itinerary_image = request.build_absolute_uri(
                        itinerary.image.url
                    )

                itinerary_data.append(
                    {
                        "day_number": itinerary.day_number,
                        "destination": (
                            itinerary.destination.pName
                            if itinerary.destination
                            else None
                        ),
                        "description": itinerary.description,
                        "image": itinerary_image,
                    }
                )

            # ---------------- PACKAGE IMAGE ----------------

            package_image = None

            if pkg.image:
                package_image = request.build_absolute_uri(
                    pkg.image.url
                )

            # ---------------- PACKAGE DATA ----------------

            package_data.append(
                {
                    "package_id": pkg.id,
                    "name": pkg.name,
                    "description": pkg.description,
                    "days": duration,
                    "budget": budget,
                    "transport_mode": transport_mode,
                    "package_type": package_type,
                    "start_location": (
                        pkg.start_location.pName
                        if pkg.start_location
                        else None
                    ),
                    "end_location": destination.pName,
                    "image": package_image,
                    "includes": pkg.includes,
                    "excludes": pkg.excludes,
                    "itinerary": itinerary_data,
                }
            )

        return Response(
            {
                "destination_id": destination.id,
                "destination_name": destination.pName,
                "province": destination.province,
                "packages_count": len(package_data),
                "packages": package_data,
            },
            status=status.HTTP_200_OK,
        )
