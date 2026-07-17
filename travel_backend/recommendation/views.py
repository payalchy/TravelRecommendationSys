from collections import defaultdict

from django.db.models import Q
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination, TravelPackage, PackageItinerary, Booking
from .engine import recommend_destinations_direct, recommend_packages
from .serializers import BookingSerializer
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
        normalized = str(provinces).strip()
        if not normalized:
            return []

        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, list):
                return [str(p).strip() for p in parsed if str(p).strip()]
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

        if normalized.startswith("[") and normalized.endswith("]"):
            return []

        return [normalized]
    
    return []


def _normalize_province_value(value):
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _province_filter_query(provinces):
    query = Q()
    for province in provinces:
        normalized = _normalize_province_value(province)
        if normalized:
            query |= Q(province__iexact=normalized)
    return query


def _destination_payload(destination, **extra):
    payload = {
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
    payload.update(extra)
    return payload


def _profile_destination_preferences(profile):
    preferences = {
        "culture": 1.0,
        "adventure": 1.0,
        "wildlife": 1.0,
        "sightseeing": 1.0,
        "history": 1.0,
    }

    styles = profile.preferred_travel_style.all()
    for style in styles:
        name = str(style.name).strip().lower()
        if name in preferences:
            preferences[name] = 4.0

    return preferences


def _destination_reason_label(source_flags, matched_query=None):
    if matched_query:
        if str(matched_query).startswith("Based on your recent search for"):
            return str(matched_query)

        return f'Based on your recent search for "{matched_query}"'

    if source_flags == {"history", "profile"}:
        return "Based on your recent searches and preferences"

    if source_flags == {"history"}:
        return "Based on your recent searches"

    return "Matches your preferences"


def _normalize_text_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return []

        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

        if "," in normalized:
            return [part.strip() for part in normalized.split(",") if part.strip()]

        return [normalized]

    return []


def _package_similarity_score(expected, actual):
    expected_value = _safe_float(expected)
    actual_value = _safe_float(actual)

    if expected_value is None or actual_value is None:
        return 0.5

    scale = max(abs(expected_value), abs(actual_value), 1.0)
    return max(0.0, 1.0 - abs(expected_value - actual_value) / scale)


def _package_style_score(profile_styles, package_type):
    if not profile_styles or not package_type:
        return 0.5

    package_type_text = str(package_type).strip().lower()
    normalized_styles = [str(style).strip().lower() for style in profile_styles if str(style).strip()]

    if not normalized_styles:
        return 0.5

    if any(style in package_type_text for style in normalized_styles):
        return 1.0

    return 0.25


def _package_match_reasons(package, profile, preferred_provinces=None):
    reasons = []

    budget = _safe_float(getattr(profile, "budget", None)) if profile else None
    duration = _safe_float(getattr(profile, "preferred_duration", None)) if profile else None
    selected_styles = [style.name for style in profile.preferred_travel_style.all()] if profile else []

    package_budget = _safe_float(getattr(package, "budget", None))
    package_days = _safe_float(getattr(package, "days", None))
    package_type = getattr(package, "package_type", None)
    province = getattr(getattr(package, "end_location", None), "province", None)

    if budget is not None and package_budget is not None:
        if package_budget <= budget:
            reasons.append("Within your budget")
        elif package_budget <= budget * 1.15:
            reasons.append("Close to your budget")

    if duration is not None and package_days is not None:
        if package_days == duration:
            reasons.append("Matches your preferred trip length")
        elif abs(package_days - duration) <= 1:
            reasons.append("Near your preferred trip length")

    if selected_styles and package_type:
        package_type_text = str(package_type).strip().lower()
        if any(str(style).strip().lower() in package_type_text for style in selected_styles):
            reasons.append("Matches your travel style")

    if preferred_provinces and province:
        normalized_province = str(province).strip().lower()
        normalized_preferences = {
            str(item).strip().lower()
            for item in preferred_provinces
            if str(item).strip()
        }
        if normalized_province in normalized_preferences:
            reasons.append(f"In your preferred province: {province}")

    if getattr(package, "distance_km", None) is not None and package.distance_km <= 250:
        reasons.append("Good route length for a short trip")

    if not reasons:
        reasons.append("Popular package match")

    seen = set()
    unique_reasons = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            unique_reasons.append(reason)

    return unique_reasons[:3]


def _package_match_score(package, profile, preferred_provinces=None):
    budget_score = _package_similarity_score(
        getattr(profile, "budget", None) if profile else None,
        getattr(package, "budget", None),
    )

    duration_score = _package_similarity_score(
        getattr(profile, "preferred_duration", None) if profile else None,
        getattr(package, "days", None),
    )

    selected_styles = [style.name for style in profile.preferred_travel_style.all()] if profile else []
    style_score = _package_style_score(selected_styles, getattr(package, "package_type", None))

    province_score = 0.5
    province = getattr(getattr(package, "end_location", None), "province", None)
    if preferred_provinces and province:
        normalized_preferences = {
            str(item).strip().lower()
            for item in preferred_provinces
            if str(item).strip()
        }
        province_score = 1.0 if str(province).strip().lower() in normalized_preferences else 0.25

    route_distance = _safe_float(getattr(package, "distance_km", None))
    distance_score = 0.5 if route_distance is None else 1.0 / (1.0 + max(route_distance, 0.0) / 250.0)

    return (
        0.35 * budget_score
        + 0.25 * duration_score
        + 0.20 * style_score
        + 0.10 * province_score
        + 0.10 * distance_score
    )


def _gather_recent_search_suggestions(user, limit=5, max_histories=8):
    histories = list(
        SearchHistory.objects.filter(user=user)
        .exclude(destination_results__isnull=True)
        .order_by("-created_at")[:max_histories]
    )

    scored = defaultdict(
        lambda: {
            "score": 0.0,
            "matched_queries": [],
            "source_flags": set(),
        }
    )

    for history_index, history in enumerate(histories):
        history_weight = 1.0 / (history_index + 1)
        results = history.destination_results or []

        if isinstance(results, list):
            for result_index, result in enumerate(results):
                destination_id = result.get("destination_id")
                if destination_id is None:
                    continue

                result_weight = history_weight * (1.0 / (result_index + 1))
                bucket = scored[int(destination_id)]
                bucket["score"] += result_weight
                bucket["source_flags"].add("history")

                query_text = str(history.query or "").strip()
                if query_text and query_text != "recommendation_search":
                    bucket["matched_queries"].append(query_text)

    if scored:
        destination_ids = list(scored.keys())
        destinations = Destination.objects.filter(id__in=destination_ids)
        destination_map = {destination.id: destination for destination in destinations}

        ranked = []
        for destination_id, bucket in scored.items():
            destination = destination_map.get(destination_id)
            if destination is None:
                continue

            top_query = bucket["matched_queries"][0] if bucket["matched_queries"] else None
            ranked.append(
                {
                    **_destination_payload(
                        destination,
                        recommendation_reason=_destination_reason_label(bucket["source_flags"], top_query),
                        recommendation_score=round(bucket["score"], 6),
                        recommendation_sources=["history"],
                    )
                }
            )

        ranked.sort(key=lambda item: item.get("recommendation_score", 0.0), reverse=True)
        return ranked[:limit]

    return []


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
        save_history = request.data.get("save_history", True)

        if isinstance(save_history, str):
            save_history = save_history.strip().lower() not in {"false", "0", "no", "off"}
        else:
            save_history = bool(save_history)

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
            provinces_to_filter.extend(
                filter(None, (_normalize_province_value(p) for p in request_provinces))
            )
        
        # Add user's saved provinces
        user_provinces = profile.get_preferred_provinces() if hasattr(profile, 'get_preferred_provinces') else []
        if user_provinces:
            provinces_to_filter.extend(
                filter(None, (_normalize_province_value(p) for p in user_provinces))
            )
        
        # If request had single preferred_province, add it
        if preferred_province:
            normalized_province = _normalize_province_value(preferred_province)
            if normalized_province:
                provinces_to_filter.append(normalized_province)
        
        # Remove duplicates and filter
        if provinces_to_filter:
            unique_provinces = list({p.lower(): p for p in provinces_to_filter}.values())
            destinations = destinations.filter(_province_filter_query(unique_provinces))

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

        if save_history:
            SearchHistory.objects.create(
                user=request.user,
                query="recommendation_search",
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


class YouMightAlsoLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            profile = user.userprofile
        except Exception:
            from users.models import UserProfile

            profile, _ = UserProfile.objects.get_or_create(user=user)

        top_n = _safe_float(request.query_params.get("top_n"), 6)
        top_n = int(top_n) if top_n else 6
        top_n = max(1, min(top_n, 12))

        user_context = {
            "budget": profile.budget,
            "duration": profile.preferred_duration,
            "travel_type": (
                profile.preferred_travel_style.first().name
                if profile.preferred_travel_style.exists()
                else ""
            ),
            "user_latitude": profile.latitude if profile.latitude is not None else 27.7172,
            "user_longitude": profile.longitude if profile.longitude is not None else 85.3240,
        }

        user_preferences = _profile_destination_preferences(profile)
        candidate_scores = defaultdict(
            lambda: {
                "score": 0.0,
                "source_flags": set(),
                "matched_queries": [],
            }
        )

        profile_ranked = recommend_destinations_direct(
            user_prefs=user_preferences,
            user_context=user_context,
            destinations=Destination.objects.all(),
            top_n=max(6, top_n),
        )

        for item in profile_ranked:
            destination = item.destination
            bucket = candidate_scores[destination.id]
            bucket["score"] += float(item.final_score)
            bucket["source_flags"].add("profile")

        recent_history_candidates = _gather_recent_search_suggestions(user, limit=max(6, top_n))
        for item in recent_history_candidates:
            destination_id = item["destination_id"]
            bucket = candidate_scores[destination_id]
            bucket["score"] += float(item.get("recommendation_score", 0.0)) * 1.5
            bucket["source_flags"].add("history")
            reason = item.get("recommendation_reason")
            if reason:
                bucket["matched_queries"].append(reason)

        if not candidate_scores:
            return Response({"results": []}, status=status.HTTP_200_OK)

        destination_ids = list(candidate_scores.keys())
        destinations = Destination.objects.filter(id__in=destination_ids)
        destination_map = {destination.id: destination for destination in destinations}

        max_score = max((bucket["score"] for bucket in candidate_scores.values()), default=1.0)
        results = []

        for destination_id, bucket in candidate_scores.items():
            destination = destination_map.get(destination_id)
            if destination is None:
                continue

            normalized_score = bucket["score"] / max_score if max_score else bucket["score"]
            matched_reason = None
            for candidate_reason in bucket["matched_queries"]:
                if candidate_reason.startswith("Based on your recent search for"):
                    matched_reason = candidate_reason
                    break

            results.append(
                _destination_payload(
                    destination,
                    recommendation_reason=_destination_reason_label(
                        bucket["source_flags"],
                        matched_reason,
                    ),
                    recommendation_score=round(normalized_score, 6),
                    recommendation_sources=sorted(bucket["source_flags"]),
                )
            )

        results.sort(key=lambda item: item.get("recommendation_score", 0.0), reverse=True)

        return Response(
            {
                "results": results[:top_n],
                "section_title": "You Might Also Like",
                "section_subtitle": "A blend of your recent searches and profile preferences.",
            },
            status=status.HTTP_200_OK,
        )


class RecommendedPackagesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        try:
            profile = user.userprofile
        except Exception:
            from users.models import UserProfile

            profile, _ = UserProfile.objects.get_or_create(user=user)

        request_budget = _safe_float(request.data.get("budget"))
        request_duration = _safe_float(request.data.get("duration"))
        request_provinces = _coerce_preferred_provinces(request)

        user_budget = request_budget if request_budget is not None else profile.budget
        user_duration = request_duration if request_duration is not None else profile.preferred_duration

        preferred_provinces = request_provinces
        if not preferred_provinces and hasattr(profile, "get_preferred_provinces"):
            preferred_provinces = profile.get_preferred_provinces()

        top_n = _safe_float(request.data.get("top_n"), 6)
        top_n = int(top_n) if top_n else 6
        top_n = max(1, min(top_n, 12))

        packages = (
            TravelPackage.objects.select_related("start_location", "end_location")
            .all()
        )

        if not packages.exists():
            return Response(
                {
                    "package_count": 0,
                    "packages": [],
                    "constraints_applied": {
                        "budget_npr": user_budget,
                        "duration_days": user_duration,
                    },
                },
                status=status.HTTP_200_OK,
            )

        ranked_packages = []

        for package in packages:
            match_score = _package_match_score(package, profile, preferred_provinces)
            reasons = _package_match_reasons(package, profile, preferred_provinces)

            package_image = None
            if package.image:
                package_image = request.build_absolute_uri(package.image.url)

            ranked_packages.append(
                {
                    "package_id": package.id,
                    "name": package.name,
                    "description": package.description,
                    "days": package.days,
                    "budget": package.budget,
                    "transport_mode": package.transport_mode,
                    "package_type": package.package_type,
                    "number_of_travelers": package.number_of_travelers,
                    "start_location": (
                        package.start_location.pName
                        if package.start_location
                        else None
                    ),
                    "destination_id": (
                        package.end_location.id
                        if package.end_location
                        else None
                    ),
                    "destination_name": (
                        package.end_location.pName
                        if package.end_location
                        else None
                    ),
                    "province": (
                        package.end_location.province
                        if package.end_location
                        else None
                    ),
                    "image": package_image,
                    "includes": _normalize_text_list(package.includes),
                    "excludes": _normalize_text_list(package.excludes),
                    "distance_km": round(package.distance_km, 2),
                    "match_score": round(match_score, 6),
                    "recommendation_reason": reasons[0],
                    "recommendation_reasons": reasons,
                }
            )

        ranked_packages.sort(
            key=lambda item: (
                item.get("match_score", 0.0),
                -float(item.get("budget") or 0.0),
            ),
            reverse=True,
        )

        return Response(
            {
                "package_count": len(ranked_packages[:top_n]),
                "packages": ranked_packages[:top_n],
                "constraints_applied": {
                    "budget_npr": user_budget,
                    "duration_days": user_duration,
                    "preferred_provinces": preferred_provinces,
                },
                "section_title": "Recommended Packages",
                "section_subtitle": "Packages ranked from your saved preferences.",
            },
            status=status.HTTP_200_OK,
        )


class RecommendedPackageDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, package_id):
        try:
            package = TravelPackage.objects.select_related("start_location", "end_location").get(id=package_id)
        except TravelPackage.DoesNotExist:
            return Response(
                {"error": f"Package with id {package_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        itineraries = (
            PackageItinerary.objects.filter(package=package)
            .select_related("destination")
            .order_by("day_number")
        )

        itinerary_data = []
        for itinerary in itineraries:
            itinerary_data.append(
                {
                    "day_number": itinerary.day_number,
                    "destination": itinerary.destination.pName if itinerary.destination else None,
                    "description": itinerary.description,
                }
            )

        package_image = None
        if package.image:
            package_image = request.build_absolute_uri(package.image.url)

        return Response(
            {
                "package_id": package.id,
                "name": package.name,
                "description": package.description,
                "days": package.days,
                "budget": package.budget,
                "number_of_travelers": package.number_of_travelers,
                "transport_mode": package.transport_mode,
                "package_type": package.package_type,
                "start_location": package.start_location.pName if package.start_location else None,
                "end_location": package.end_location.pName if package.end_location else None,
                "start_coords": (
                    {
                        "lat": package.start_location.latitude,
                        "lng": package.start_location.longitude,
                    }
                    if package.start_location
                    and package.start_location.latitude is not None
                    and package.start_location.longitude is not None
                    else None
                ),
                "end_coords": (
                    {
                        "lat": package.end_location.latitude,
                        "lng": package.end_location.longitude,
                    }
                    if package.end_location
                    and package.end_location.latitude is not None
                    and package.end_location.longitude is not None
                    else None
                ),
                "image": package_image,
                "includes": _normalize_text_list(package.includes),
                "excludes": _normalize_text_list(package.excludes),
                "itinerary": itinerary_data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------- DESTINATION PROVINCES API ----------------

class BookingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        booking = serializer.save(user=request.user)
        response_serializer = BookingSerializer(booking)
        return Response(
            {
                "message": "Booking request submitted successfully. Your booking is pending until admin updates the status.",
                "booking": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class BookingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user).select_related('package', 'package__end_location').order_by('-created_at')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
    permission_classes = [IsAuthenticated]

    def get(self, request):

        query = str(
            request.query_params.get("q", "")
        ).strip()
        limit = int(request.query_params.get("limit", 6))
        offset = int(request.query_params.get("offset", 0))

        if limit < 1:
            limit = 6
        if offset < 0:
            offset = 0

        # ---------------- EMPTY QUERY ----------------

        if not query:
            return Response(
                {
                    "results": [],
                    "count": 0,
                    "has_more": False,
                },
                status=status.HTTP_200_OK,
            )

        # ---------------- SEARCH DESTINATIONS ----------------

        destinations_qs = (
            Destination.objects.filter(
                Q(pName__icontains=query)
                | Q(province__icontains=query)
                | Q(city__icontains=query)
            )
            .order_by("pName")
            .distinct()
        )

        total_count = destinations_qs.count()
        destinations = destinations_qs[offset:offset + limit]

        results = []

        for destination in destinations:

            results.append(
                {
                    "destination_id": destination.id,
                    "name": destination.pName,
                    "province": destination.province,
                    "city": destination.city,
                    "latitude": destination.latitude,
                    "longitude": destination.longitude,
                    "image": (
                        request.build_absolute_uri(
                            destination.image.url
                        )
                        if destination.image
                        else None
                    ),
                    "culture": destination.culture,
                    "adventure": destination.adventure,
                    "wildlife": destination.wildlife,
                    "sightseeing": destination.sightseeing,
                    "history": destination.history,
                }
            )

        # ---------------- SAVE SEARCH HISTORY ----------------

        if request.user.is_authenticated and query:
            SearchHistory.objects.create(
                user=request.user,
                query=query,
                destination_results=results,
            )
        # ---------------- RESPONSE ----------------

        return Response(
            {
                "results": results,
                "count": total_count,
                "has_more": offset + len(results) < total_count,
            },
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
                "limit": 5,
                "addressdetails": 1,
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

        preferred = None
        for item in payload:
            display_name = str(item.get("display_name", "")).lower()
            if "nepal" not in display_name:
                continue

            if preferred is None:
                preferred = item
                continue

            if float(item.get("importance", 0) or 0) > float(preferred.get("importance", 0) or 0):
                preferred = item

        if preferred is None:
            preferred = payload[0]

        return Response(
            {
                "name": destination_name,
                "latitude": float(preferred.get("lat")),
                "longitude": float(preferred.get("lon")),
                "display_name": preferred.get("display_name"),
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
                itinerary__destination_id=destination_id
            )
            .select_related(
                "start_location",
                "end_location",
            )
            .distinct()
            .all()
        )

        package_data = []

        try:
            profile = request.user.userprofile
        except Exception:
            profile = None

        user_context = {
            "budget": getattr(profile, "budget", None) if profile else None,
            "distance": 100,
            "duration": getattr(profile, "preferred_duration", None) if profile else None,
            "travel_type": (
                profile.preferred_travel_style.first().name
                if profile and profile.preferred_travel_style.exists()
                else ""
            ),
        }

        ranked_packages = []
        if packages:
            ranked_packages = recommend_packages(
                user_context,
                list(packages),
                k=max(1, len(packages)),
                top_n=max(1, len(packages)),
            )

        package_items = [item.package for item in ranked_packages] if ranked_packages else list(packages)

        for pkg in package_items:

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
                itinerary_data.append(
                    {
                        "day_number": itinerary.day_number,
                        "destination": (
                            itinerary.destination.pName
                            if itinerary.destination
                            else None
                        ),
                        "description": itinerary.description,
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
                    "number_of_travelers": getattr(pkg, "number_of_travelers", None),
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
