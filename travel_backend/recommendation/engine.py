"""
Travel Recommendation Engine - Multi-Algorithm Approach (UPDATED)

KEY UPDATE:
- distance2 is now based on ITINERARY distance instead of geo distance
"""

import math
from dataclasses import dataclass

EPSILON = 1e-9


# =========================
# DATA CLASSES
# =========================

@dataclass
class ScoredPackage:
    package: object
    cps: float
    distance: float
    computed_distance_km: float
    cost_efficiency: float
    time_efficiency: float
    final_score: float


@dataclass
class ScoredDestination:
    destination: object
    distance_km: float
    preference_score: float
    geo_score: float
    package_support_score: float
    final_score: float


# =========================
# SAFE HELPERS
# =========================

def _safe_positive(value, default=0.0):
    try:
        v = float(value)
        return v if v >= 0 else float(default)
    except:
        return float(default)


def _safe_float(value, default=None):
    try:
        return float(value)
    except:
        return default


def _normalize_weights(weights):
    total = sum(float(v) for v in weights.values() if v is not None)
    if total <= 0:
        return {k: 1.0 / len(weights) for k in weights}
    return {k: float(v) / total for k, v in weights.items()}


# =========================
# ITINERARY DISTANCE (distance2 FIX)
# =========================

def _itinerary_distance_km(package):
    """
    distance2 SOURCE:
    Uses itinerary-based travel distance instead of geo distance.
    """

    # 1. Direct stored itinerary distance (BEST)
    if hasattr(package, "itinerary_total_distance_km") and package.itinerary_total_distance_km:
        return _safe_positive(package.itinerary_total_distance_km)

    # 2. Step-based itinerary calculation
    if hasattr(package, "itinerary") and package.itinerary:
        try:
            return sum(
                _safe_positive(step.distance_km)
                for step in package.itinerary
            )
        except:
            pass

    # 3. fallback
    return 50.0


# =========================
# SIMILARITY
# =========================

def _preference_similarity(user_value, item_value):
    u = _safe_positive(user_value)
    i = _safe_positive(item_value)
    scale = max(u, i, 1.0)
    return max(0.0, 1.0 - abs(u - i) / scale)


def _travel_type_similarity(user_type, package_type):
    if not user_type or not package_type:
        return 0.5

    user_types = [t.strip().lower() for t in str(user_type).split(",")]
    package_type = str(package_type).lower()

    return 1.0 if any(ut in package_type for ut in user_types) else 0.2


# =========================
# PACKAGE SCORING
# =========================

def compute_cps(user_context, package, weights, distance2):
    """
    CPS now uses itinerary distance (distance2)
    """
    return (
        weights["budget"] * _preference_similarity(user_context.get("budget"), package.budget)
        + weights["distance"] * _preference_similarity(user_context.get("distance"), distance2)
        + weights["duration"] * _preference_similarity(user_context.get("duration"), package.days)
        + weights["travel_type"] * _travel_type_similarity(user_context.get("travel_type"), package.package_type)
    )


def compute_weighted_distance(user_context, package, weights, distance2):
    """
    KNN distance using itinerary-based distance2
    """

    budget_d = _safe_positive(user_context.get("budget")) - _safe_positive(package.budget)
    distance_d = _safe_positive(user_context.get("distance")) - _safe_positive(distance2)
    duration_d = _safe_positive(user_context.get("duration")) - _safe_positive(package.days)

    return math.sqrt(
        weights["budget"] * budget_d ** 2 +
        weights["distance"] * distance_d ** 2 +
        weights["duration"] * duration_d ** 2
    )


# =========================
# COST & TIME EFFICIENCY (UPDATED CORE FIX)
# =========================

def compute_efficiencies(package, distance2):
    """
    UPDATED FORMULA:
    cost_efficiency = cost / (distance + distance2)
    """

    distance2 = max(_safe_positive(distance2), EPSILON)
    cost = _safe_positive(package.budget)
    duration = max(_safe_positive(package.days), EPSILON)

    cost_efficiency = cost / (distance + distance2)

    time_efficiency = (distance + distance2) / duration

    return cost_efficiency, time_efficiency


# =========================
# PACKAGE RECOMMENDATION
# =========================

def recommend_packages(user_context, packages, k=5, top_n=5):

    preference_weights = _normalize_weights({
        "budget": 0.3,
        "distance": 0.3,
        "duration": 0.2,
        "travel_type": 0.2,
    })

    context_weights = _normalize_weights({
        "budget": 0.4,
        "distance": 0.3,
        "duration": 0.3,
    })

    blend = _normalize_weights({"alpha": 0.4, "beta": 0.4, "gamma": 0.2})

    scored = []

    for package in packages:

        # distance2 = itinerary distance (CORE CHANGE)
        distance2 = _itinerary_distance_km(package)

        cps = compute_cps(user_context, package, preference_weights, distance2)

        dist = compute_weighted_distance(user_context, package, context_weights, distance2)

        ce, te = compute_efficiencies(package, distance2)

        scored.append((package, cps, dist, distance2, ce, te))

    scored.sort(key=lambda x: x[2])
    neighbors = scored[:max(1, k)]

    results = []

    for package, cps, dist, distance2, ce, te in neighbors:

        final_score = (
            blend["alpha"] * cps +
            blend["beta"] * (1 / max(dist, EPSILON)) +
            blend["gamma"] * (1 / max(ce + te, EPSILON))
        )

        results.append(
            ScoredPackage(
                package, cps, dist, distance2, ce, te, final_score
            )
        )

    results.sort(key=lambda x: x.final_score, reverse=True)
    return results[:max(1, top_n)]


# =========================
# DESTINATION SCORING (UPDATED distance2)
# =========================

def _destination_distance2(destination):
    """
    destination-level itinerary distance aggregation
    """

    if hasattr(destination, "itinerary_total_distance_km"):
        return _safe_positive(destination.itinerary_total_distance_km)

    return 50.0


def recommend_destinations_direct(user_prefs, user_context, destinations, top_n=5):
    """
    Recommend destinations based on user preferences and proximity.
    
    user_prefs: dict with keys [culture, adventure, wildlife, sightseeing, history] on 0-5 scale
    user_context: dict with user location (user_latitude, user_longitude)
    destinations: QuerySet of Destination objects
    top_n: number of results to return
    """

    user_lat = _safe_float(user_context.get("user_latitude"))
    user_lon = _safe_float(user_context.get("user_longitude"))

    results = []

    for d in destinations:
        # Calculate preference score: average match across all attributes
        # Each attribute on 0-5 scale, so similarity will be 0-1
        pref_scores = [
            _preference_similarity(user_prefs.get("culture", 1.0), d.culture or 0),
            _preference_similarity(user_prefs.get("adventure", 1.0), d.adventure or 0),
            _preference_similarity(user_prefs.get("wildlife", 1.0), d.wildlife or 0),
            _preference_similarity(user_prefs.get("sightseeing", 1.0), d.sightseeing or 0),
            _preference_similarity(user_prefs.get("history", 1.0), d.history or 0),
        ]
        
        # Average preference score across all attributes (0-1 scale)
        pref = sum(pref_scores) / len(pref_scores)

        # Geographic distance from user to destination (in km)
        if d.latitude and d.longitude and user_lat is not None and user_lon is not None:
            lat_diff = math.radians(_safe_float(d.latitude) - user_lat)
            lon_diff = math.radians(_safe_float(d.longitude) - user_lon)
            
            # Haversine formula
            a = math.sin(lat_diff / 2) ** 2 + math.cos(math.radians(user_lat)) * math.cos(math.radians(_safe_float(d.latitude))) * math.sin(lon_diff / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            distance_km = 6371 * c  # Earth radius in km
        else:
            distance_km = 100.0  # Default distance if coordinates missing

        # FILTER: Only include destinations within 100 km radius
        if distance_km > 100.0:
            continue

        # Geo score: closer is better (inverted distance formula)
        # At 0km: geo_score = 1.0
        # At 50km: geo_score = 0.67
        # At 200km: geo_score = 0.2
        geo_score = 1.0 / (1.0 + distance_km / 50.0)

        # Final score: 50% proximity, 50% preference
        # This ensures nearby destinations rank higher
        final = 0.5 * pref + 0.5 * geo_score

        results.append(
            ScoredDestination(
                d, distance_km, pref, geo_score, 0.0, final
            )
        )

    results.sort(key=lambda x: x.final_score, reverse=True)
    return results[:max(1, top_n)]