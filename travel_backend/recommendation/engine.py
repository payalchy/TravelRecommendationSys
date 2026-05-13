"""
Travel Recommendation Engine - Multi-Algorithm Approach

This module implements a comprehensive 6-step recommendation system:
1. User Preference Modeling (Contextual Preference Scoring - CPS)
2. Similarity Measurement (Context-Aware K-Nearest Neighbors - C-KNN)
3. Neighbor Selection (K-Nearest Neighbors - KNN)
4. Cost & Duration Optimization (Cost-Time Efficiency Analysis)
5. Ranking & Selection (Weighted Linear Scoring Model)
6. Recommendation Output (Top-N Recommendation Selection)

The system combines multiple scoring metrics to provide personalized,
optimized travel recommendations based on user preferences and constraints.
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
    """
    Safely converts a value to positive float, with fallback default.
    Handles None, non-numeric, and negative values gracefully.
    """
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if parsed >= 0 else float(default)


def _safe_float(value, default=None):
    """
    Safely converts a value to float, returning default if conversion fails.
    Used for handling optional/nullable fields from database.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_weights(weights):
    """
    Normalizes a dictionary of weights so they sum to 1.0.
    If all weights are 0 or None, assigns uniform distribution.
    Essential for combining multiple scoring components.
    """
    total = sum(float(v) for v in weights.values() if v is not None)
    if total <= 0:
        size = len(weights) if weights else 1
        return {k: 1.0 / size for k in weights}
    return {k: float(v) / total for k, v in weights.items()}


# =========================
# SIMILARITY FUNCTIONS
# =========================

def _preference_similarity(user_value, item_value):
    """
    ALGORITHM 1: User Preference Modeling (CPS)
    
    Computes normalized similarity between user preference and travel option.
    This is the base similarity metric used in CPS calculation.
    
    Formula: similarity = max(0, 1 - |user_v - item_v| / scale)
    
    Args:
        user_value: User's preference value for an attribute
        item_value: Travel option's value for that attribute
    
    Returns:
        float: Normalized similarity score [0, 1]
    """
    user_v = _safe_positive(user_value)
    item_v = _safe_positive(item_value)
    scale = max(user_v, item_v, 1.0)
    return max(0.0, 1.0 - abs(user_v - item_v) / scale)


#  FIXED: MULTI-STYLE SUPPORT (IMPORTANT FIX)
def _travel_type_similarity(user_type, package_type):
    if not user_type or not package_type:
        return 0.5

    user_types = [t.strip().lower() for t in str(user_type).split(",")]
    package_type = str(package_type).strip().lower()

    for ut in user_types:
        if ut in package_type or package_type in ut:
            return 1.0

    return 0.2


# =========================
# GEO DISTANCE
# =========================

def _euclidean_geo_distance_km(lat1, lon1, lat2, lon2):
    """
    Computes Euclidean distance between two geographic coordinates in kilometers.
    Uses simplified projection to handle Earth's curvature for nearby locations.
    
    Formulas:
        - Average latitude: avg_lat_rad = (lat1 + lat2) / 2 (in radians)
        - Longitude difference: Δlon_km = Δlon × 111.32 × cos(avg_lat_rad)
        - Latitude difference: Δlat_km = Δlat × 110.57
        - Distance: d = √(Δlat_km² + Δlon_km²)
    
    Constants:
        - 111.32 km/degree: approximate km per degree longitude at equator
        - 110.57 km/degree: approximate km per degree latitude
    
    Args:
        lat1, lon1: User coordinates
        lat2, lon2: Destination coordinates
    
    Returns:
        float: Distance in kilometers
    """
    avg_lat_rad = math.radians((lat1 + lat2) / 2.0)
    delta_lon_km = (lon1 - lon2) * 111.32 * math.cos(avg_lat_rad)
    delta_lat_km = (lat1 - lat2) * 110.57
    return math.sqrt(delta_lat_km**2 + delta_lon_km**2)


def _user_to_destination_distance_km(user_context, destination):
    """
    Computes geographic distance from user's location to a destination.
    Handles missing coordinates gracefully by returning penalty distance.
    
    Args:
        user_context: Dictionary with user_latitude and user_longitude
        destination: Object with latitude and longitude attributes
    
    Returns:
        float: Distance in kilometers, or 50.0 km penalty if coordinates missing
    """
    user_lat = _safe_float(user_context.get("user_latitude"))
    user_lon = _safe_float(user_context.get("user_longitude"))
    dest_lat = _safe_float(getattr(destination, "latitude", None))
    dest_lon = _safe_float(getattr(destination, "longitude", None))

    if None in (user_lat, user_lon, dest_lat, dest_lon):
        # Penalty for missing coordinate data - effectively deprioritizes this option
        return 50.0

    return _euclidean_geo_distance_km(user_lat, user_lon, dest_lat, dest_lon)


# =========================
# PACKAGE SCORING
# =========================

def compute_cps(user_context, package, preference_weights, distance_km):
    """
    ALGORITHM 1: Contextual Preference Scoring (CPS)
    
    Computes the Contextual Preference Score (CPS) by evaluating how well
    a travel package matches user preferences across multiple dimensions:
    budget, distance, duration, and travel type.
    
    Formula:
        CPS_i = Σ(j=1 to n) w_j × f(U, T_i)
    
    Where:
        - w_j = weight of the j-th preference attribute
        - f(U, T_i) = similarity function between user preference and travel option
        - Attributes: budget, distance, duration, travel_type
    
    Args:
        user_context: Dictionary with user preferences (budget, distance, duration, travel_type)
        package: Travel package object with attributes (budget, days, package_type)
        preference_weights: Dictionary of normalized weights for each preference
        distance_km: Computed distance from user location to destination
    
    Returns:
        float: CPS score [0, 1] - higher indicates better preference match
    """
    # Compute individual preference similarities
    score_budget = _preference_similarity(user_context.get("budget"), package.budget)
    score_distance = _preference_similarity(user_context.get("distance"), distance_km)
    score_duration = _preference_similarity(user_context.get("duration"), package.days)
    score_travel_type = _travel_type_similarity(user_context.get("travel_type"), package.package_type)

    # Weighted sum of similarities - Formula: CPS_i = Σ w_j × f(U, T_i)
    return (
        preference_weights["budget"] * score_budget
        + preference_weights["distance"] * score_distance
        + preference_weights["duration"] * score_duration
        + preference_weights["travel_type"] * score_travel_type
    )


def compute_weighted_distance(user_context, package, context_weights, distance_km):
    """
    ALGORITHM 2: Context-Aware K-Nearest Neighbors (C-KNN)
    ALGORITHM 3: Similarity Measurement using Weighted Euclidean Distance
    
    Computes the context-aware distance between user requirements and a travel package.
    This is the foundation for KNN-based neighbor selection. Lower distances indicate
    better matches across budget, distance, and duration dimensions.
    
    Formula (Weighted Euclidean Distance):
        Dist(U, T_i) = √[w_b(b_u - b_i)² + w_d(d_u - d_i)² + w_t(t_u - t_i)²]
    
    Where:
        - b_u, b_i = user budget vs package budget
        - d_u, d_i = user preferred distance vs computed distance
        - t_u, t_i = user duration vs package duration
        - w_b, w_d, w_t = context weights (sum to 1.0)
    
    Args:
        user_context: User requirements (budget, distance, duration)
        package: Travel package to evaluate
        context_weights: Normalized weights for budget, distance, duration
        distance_km: Geographic distance in kilometers
    
    Returns:
        float: Weighted distance score - lower values indicate better fit
    """
    # Extract user constraints
    budget_delta = _safe_positive(user_context.get("budget")) - _safe_positive(package.budget)
    distance_delta = _safe_positive(user_context.get("distance")) - _safe_positive(distance_km)
    duration_delta = _safe_positive(user_context.get("duration")) - _safe_positive(package.days)

    # Weighted Euclidean distance formula
    # Dist(U, T_i) = √[w_b(b_u - b_i)² + w_d(d_u - d_i)² + w_t(t_u - t_i)²]
    return math.sqrt(
        context_weights["budget"] * (budget_delta ** 2)
        + context_weights["distance"] * (distance_delta ** 2)
        + context_weights["duration"] * (duration_delta ** 2)
    )


def compute_efficiencies(package, distance_km):
    """
    ALGORITHM 4: Cost & Duration Optimization - Cost-Time Efficiency Analysis
    
    Analyzes the cost and time efficiency of a travel package to identify
    affordable and time-efficient alternatives. Enables comparison of different
    routes based on economic and temporal dimensions.
    
    Formulas:
        Cost Efficiency (CE): CE_i = Cost_i / Distance_i
        Time Efficiency (TE): TE_i = Distance_i / Duration_i
    
    Where:
        - Lower CE indicates better value for money
        - Higher TE indicates faster travel relative to distance
    
    Args:
        package: Travel package with budget and days attributes
        distance_km: Geographic distance in kilometers
    
    Returns:
        tuple: (cost_efficiency, time_efficiency) - efficiency scores
    """
    # Prevent division by zero with EPSILON
    distance = max(_safe_positive(distance_km), EPSILON)
    duration = max(_safe_positive(package.days), EPSILON)
    cost = _safe_positive(package.budget)

    # Cost Efficiency: CE_i = Cost / Distance (lower is better)
    cost_efficiency = cost / distance
    
    # Time Efficiency: TE_i = Distance / Duration (higher is better)
    time_efficiency = distance / duration
    
    return cost_efficiency, time_efficiency


# =========================
# PACKAGE RECOMMENDATION
# =========================

def recommend_packages(
    user_context,
    packages,
    k=5,
    top_n=5,
    preference_weights=None,
    context_weights=None,
    alpha=0.4,
    beta=0.4,
    gamma=0.2,
):
    """
    MAIN RECOMMENDATION ENGINE: Comprehensive 6-Algorithm Pipeline
    
    Orchestrates the complete recommendation workflow:
    
    Step 1: User Preference Modeling (CPS)
            - Compute preference similarity across budget, distance, duration, travel type
    
    Step 2-3: Similarity Measurement & KNN Neighbor Selection
            - Compute weighted Euclidean distance for all packages
            - Select K-nearest neighbors (closest packages in context space)
            - Formula: N_k(U) = {T_1, T_2, ..., T_k} where Dist(U,T_1) ≤ ... ≤ Dist(U,T_k)
    
    Step 4: Cost & Duration Optimization
            - Calculate cost efficiency (cost/distance) and time efficiency (distance/duration)
            - Inverse these to create positive-correlating efficiency scores
    
    Step 5: Ranking & Selection (Weighted Linear Scoring)
            - Combine all metrics into final score
            - Formula: FinalScore_i = α·CPS_i + β·(1/Dist_i) + γ·[1/(CE_i + TE_i)]
            - Where α + β + γ = 1.0 (normalized blend weights)
    
    Step 6: Top-N Recommendation Selection
            - Sort by final score and return top N packages
            - Formula: Top-N = Argmax_N(FinalScore)
    
    Args:
        user_context: User preferences (budget, distance, duration, travel_type, location)
        packages: List of travel packages to evaluate
        k: Number of K-nearest neighbors to select (default: 5)
        top_n: Number of final recommendations to return (default: 5)
        preference_weights: Weights for CPS attributes (budget, distance, duration, travel_type)
        context_weights: Weights for weighted distance (budget, distance, duration)
        alpha: Weight for CPS component (default: 0.4)
        beta: Weight for inverse distance component (default: 0.4)
        gamma: Weight for efficiency component (default: 0.2)
    
    Returns:
        list: Top N ScoredPackage objects ranked by final_score (descending)
    """
    # Default preference weights for CPS calculation
    preference_weights = preference_weights or {
        "budget": 0.3,
        "distance": 0.3,
        "duration": 0.2,
        "travel_type": 0.2,
    }

    # Default context weights for C-KNN distance calculation
    context_weights = context_weights or {
        "budget": 0.4,
        "distance": 0.3,
        "duration": 0.3,
    }

    # Normalize all weights to sum to 1.0
    preference_weights = _normalize_weights(preference_weights)
    context_weights = _normalize_weights(context_weights)
    blend_weights = _normalize_weights({"alpha": alpha, "beta": beta, "gamma": gamma})

    # ========================================
    # STEP 1-2: CPS COMPUTATION & DISTANCE SCORING
    # ========================================
    scored = []

    for package in packages:
        # Compute geographic distance from user to package end location
        dist_km = _user_to_destination_distance_km(user_context, package.end_location)

        # Step 1: Compute CPS (User Preference Modeling)
        cps = compute_cps(user_context, package, preference_weights, dist_km)
        
        # Step 2-3: Compute weighted distance for KNN (Context-Aware K-Nearest Neighbors)
        dist = compute_weighted_distance(user_context, package, context_weights, dist_km)
        
        # Step 4: Compute efficiency scores (Cost-Time Optimization)
        ce, te = compute_efficiencies(package, dist_km)

        scored.append((package, cps, dist, dist_km, ce, te))

    # ========================================
    # STEP 3: K-NEAREST NEIGHBORS SELECTION
    # ========================================
    # Sort by weighted distance (C-KNN metric)
    # Closest packages in context space are selected as neighbors
    scored.sort(key=lambda x: x[2])
    neighbors = scored[: max(1, int(k))]

    # ========================================
    # STEP 5: WEIGHTED LINEAR SCORING MODEL
    # ========================================
    ranked = []

    for package, cps, dist, dist_km, ce, te in neighbors:

        # Inverse distance component: higher distance → lower score
        inverse_dist = 1.0 / max(dist, EPSILON)
        
        # Efficiency component: inverse of combined efficiency
        efficiency = 1.0 / max(ce + te, EPSILON)

        # Final Score = α·CPS + β·(1/Dist) + γ·[1/(CE+TE)]
        # Where α + β + γ = 1.0
        final_score = (
            blend_weights["alpha"] * cps
            + blend_weights["beta"] * inverse_dist
            + blend_weights["gamma"] * efficiency
        )

        ranked.append(
            ScoredPackage(
                package=package,
                cps=cps,
                distance=dist,
                computed_distance_km=dist_km,
                cost_efficiency=ce,
                time_efficiency=te,
                final_score=final_score,
            )
        )

    # Sort by final score (descending - higher is better)
    ranked.sort(key=lambda x: x.final_score, reverse=True)

    # ========================================
    # STEP 6: TOP-N RECOMMENDATION SELECTION
    # ========================================
    # Safety fallback for empty results
    if not ranked:
        return [
            ScoredPackage(
                package=p,
                cps=0,
                distance=0,
                computed_distance_km=0,
                cost_efficiency=0,
                time_efficiency=0,
                final_score=0,
            )
            for p in packages[:5]
        ]

    # Return top N recommendations: Top-N = Argmax_N(FinalScore)
    return ranked[: max(1, int(top_n))]


# =========================
# DESTINATION SCORING
# =========================

def _destination_preference_score(user_prefs, destination, weights, user_context=None):
    """
    ALGORITHM 1: Destination-Level Preference Scoring with Constraints
    
    Computes the preference similarity score for a destination based on
    user interest in its attributes (culture, adventure, wildlife, sightseeing, history),
    with optional budget, duration, and season constraints.
    
    Formula: Pref_i = Σ w_j × f(U_pref_j, Dest_attr_j) × constraint_penalty
    
    Args:
        user_prefs: Dictionary of user preferences (culture, adventure, wildlife, sightseeing, history)
        destination: Destination object with attribute ratings (1-5 scale)
        weights: Normalized weights for each destination attribute
        user_context: Optional dict with user constraints (budget, duration, preferred_season, avg_package_price, etc)
    
    Returns:
        float: Preference score [0, 1] indicating alignment with user interests
    """
    # Core preference attributes
    preference_score = (
        weights["culture"] * _preference_similarity(user_prefs.get("culture"), destination.culture)
        + weights["adventure"] * _preference_similarity(user_prefs.get("adventure"), destination.adventure)
        + weights["wildlife"] * _preference_similarity(user_prefs.get("wildlife"), destination.wildlife)
        + weights["sightseeing"] * _preference_similarity(user_prefs.get("sightseeing"), destination.sightseeing)
        + weights["history"] * _preference_similarity(user_prefs.get("history"), destination.history)
    )
    
    # Apply constraint penalties if user_context provided
    if user_context:
        constraint_penalty = 1.0
        
        # Budget constraint: check if destination is within budget range
        if user_context.get("budget") and hasattr(destination, "avg_package_price"):
            budget_score = _preference_similarity(
                user_context.get("budget"),
                getattr(destination, "avg_package_price", 0)
            )
            constraint_penalty *= budget_score
        
        # Duration constraint: check against typical visit duration
        if user_context.get("duration") and hasattr(destination, "recommended_visit_days"):
            duration_score = _preference_similarity(
                user_context.get("duration"),
                getattr(destination, "recommended_visit_days", 2)
            )
            constraint_penalty *= duration_score
        
        # Season preference: check if destination's best season matches user preference
        if user_context.get("preferred_season") and hasattr(destination, "best_season"):
            dest_season = str(getattr(destination, "best_season", "")).lower()
            user_season = str(user_context.get("preferred_season", "")).lower()
            season_match = 1.0 if user_season and user_season in dest_season else 0.6
            constraint_penalty *= season_match
        
        preference_score *= constraint_penalty
    
    return preference_score


def _destination_weighted_distance(user_prefs, destination, weights):
    """
    ALGORITHM 2-3: Weighted Euclidean Distance on Destination Attributes
    
    Computes context-aware distance between user preferences and destination
    characteristics in the preference space. Lower distances indicate better
    matches across all destination dimensions.
    
    This enables true C-KNN (Context-aware K-Nearest Neighbors) selection by
    finding destinations closest to user's preference profile.
    
    Formula (Weighted Euclidean Distance):
        Dist(U, D_i) = √[w_c(u_c - d_c)² + w_a(u_a - d_a)² + ... + w_h(u_h - d_h)²]
    
    Where:
        - u_c, d_c = user culture preference vs destination culture rating
        - u_a, d_a = user adventure preference vs destination adventure rating
        - etc. for each attribute (culture, adventure, wildlife, sightseeing, history)
        - w_j = normalized weights for each attribute (sum to 1.0)
    
    Args:
        user_prefs: Dictionary of user preferences (culture, adventure, wildlife, sightseeing, history)
        destination: Destination object with attribute ratings (1-5 scale)
        weights: Normalized weights for each destination attribute
    
    Returns:
        float: Weighted Euclidean distance - lower values indicate better fit
    """
    culture_delta = _safe_positive(user_prefs.get("culture")) - _safe_positive(getattr(destination, "culture", 0))
    adventure_delta = _safe_positive(user_prefs.get("adventure")) - _safe_positive(getattr(destination, "adventure", 0))
    wildlife_delta = _safe_positive(user_prefs.get("wildlife")) - _safe_positive(getattr(destination, "wildlife", 0))
    sightseeing_delta = _safe_positive(user_prefs.get("sightseeing")) - _safe_positive(getattr(destination, "sightseeing", 0))
    history_delta = _safe_positive(user_prefs.get("history")) - _safe_positive(getattr(destination, "history", 0))
    
    # Weighted Euclidean distance formula
    # Dist = √[w_c(u_c - d_c)² + w_a(u_a - d_a)² + ... + w_h(u_h - d_h)²]
    return math.sqrt(
        weights["culture"] * (culture_delta ** 2)
        + weights["adventure"] * (adventure_delta ** 2)
        + weights["wildlife"] * (wildlife_delta ** 2)
        + weights["sightseeing"] * (sightseeing_delta ** 2)
        + weights["history"] * (history_delta ** 2)
    )


def recommend_destinations_direct(
    user_destination_preferences,
    user_context,
    destinations,
    destination_top_n=5,
    destination_weights=None,
    destination_alpha=0.4,
    destination_beta=0.3,
    destination_gamma=0.3,
    destination_delta=0.0,
    destination_epsilon=0.0,
):
    """
    DIRECT DESTINATION RECOMMENDATION: All 6 Algorithms Applied to Destinations
    
    Applies the complete 6-algorithm pipeline directly to destination recommendation
    WITHOUT package dependency. Evaluates all 2050 destinations from the database.
    
    Step 1: User Preference Modeling (CPS)
            - Evaluates user interests across destination attributes
            - culture, adventure, wildlife, sightseeing, history
            - Formula: CPS_dest = Σ w_j × f(U_pref_j, Dest_attr_j)
    
    Step 2-3: Context-Aware K-Nearest Neighbors (C-KNN)
            - Computes weighted distance considering destination characteristics
            - Distance = √[w_culture(u_culture - d_culture)² + ... + w_history(u_history - d_history)²]
            - Selects K nearest destinations by this metric
    
    Step 4: Cost-Distance Efficiency
            - Evaluates geographic distance efficiency
            - Proximity_efficiency = 1 / (distance_km + 1)
            - Closer destinations score higher
    
    Step 5: Ranking & Weighted Linear Scoring Model
            - Combines all metrics into final score
            - FinalScore = α·CPS + β·Proximity_Efficiency + γ·AttributeAlignment
            - Where α + β + γ = 1.0 (normalized blend weights)
    
    Step 6: Top-N Recommendation Selection
            - Sorts destinations by final score
            - Returns top N destinations
            - Formula: Top-N = Argmax_N(FinalScore)
    
    Args:
        user_destination_preferences: User interests dict (culture, adventure, wildlife, sightseeing, history)
        user_context: User location dict with:
            - user_latitude, user_longitude: User coordinates
            - budget (optional): User budget for constraint checking
            - duration (optional): User available duration for constraint checking
            - preferred_season (optional): User preferred travel season
        destinations: QuerySet/List of all Destination objects to evaluate
        destination_top_n: Number of destination recommendations to return (default: 5)
        destination_weights: Weights for destination attributes (default: equal)
        destination_alpha: Weight for CPS component (default: 0.4)
        destination_beta: Weight for proximity/geographic component (default: 0.3)
        destination_gamma: Weight for destination attributes alignment (default: 0.3)
        destination_delta: Weight for constraint satisfaction (budget/duration/season) (default: 0.0)
        destination_epsilon: Additional weight for season preference (default: 0.0)
    
    Returns:
        list: Top N ScoredDestination objects ranked by final_score (descending)
    """
    # ========================================
    # STEP 1: DEFAULT PREFERENCES & WEIGHTS
    # ========================================
    
    # Default destination attribute weights (equal distribution)
    destination_weights = destination_weights or {
        "culture": 0.2,
        "adventure": 0.2,
        "wildlife": 0.2,
        "sightseeing": 0.2,
        "history": 0.2,
    }

    # Normalize all weights to sum to 1.0
    destination_weights = _normalize_weights(destination_weights)
    blend_weights = _normalize_weights(
        {
            "cps": destination_alpha,
            "proximity": destination_beta,
            "attributes": destination_gamma,
            "constraint": destination_delta,
            "season": destination_epsilon,
        }
    )

    # ========================================
    # STEP 1: ALGORITHM 1 - CPS ON ALL DESTINATIONS
    # ========================================
    # Compute preference scores for all destinations
    scored_destinations = []

    for destination in destinations:
        # Algorithm 1: Contextual Preference Scoring (CPS) with Constraints
        # CPS_dest = Σ w_j × f(U_pref_j, Dest_attr_j) × constraint_penalty × season_match
        # Evaluates how well destination attributes match user preferences
        # Pass user_context for constraint evaluation (budget, duration, season)
        pref_score = _destination_preference_score(
            user_destination_preferences, destination, destination_weights, user_context
        )
        
        # Compute geographic distance from user to destination
        dist_km = _user_to_destination_distance_km(user_context, destination)
        
        scored_destinations.append({
            "destination": destination,
            "pref_score": pref_score,
            "dist_km": dist_km,
        })

    # ========================================
    # STEP 2-3: ALGORITHM 2-3 - C-KNN SELECTION (Weighted Euclidean Distance)
    # ========================================
    # Compute weighted Euclidean distance on destination attributes for each destination
    # This enables true C-KNN neighbor selection in preference space
    for item in scored_destinations:
        c_knn_dist = _destination_weighted_distance(
            user_destination_preferences,
            item["destination"],
            destination_weights
        )
        item["c_knn_distance"] = c_knn_dist
    
    # Sort by C-KNN distance (lower = closer in preference space)
    # Closest destinations are selected as neighbors
    scored_destinations.sort(key=lambda x: x["c_knn_distance"])
    
    # Select K nearest neighbors (top 20% or min 5)
    k_neighbors = int(max(5, len(scored_destinations) * 0.2))
    knn_candidates = scored_destinations[: k_neighbors]

    # ========================================
    # STEP 4: ALGORITHM 4 - EFFICIENCY METRICS
    # ========================================
    # Compute proximity efficiency for KNN candidates
    results = []

    for item in knn_candidates:
        destination = item["destination"]
        pref_score = item["pref_score"]
        dist_km = item["dist_km"]
        
        # Geographic proximity efficiency: closer = higher score
        # proximity_efficiency = 1 / (distance_km + 1)
        # Normalized to [0, 1] range
        proximity_efficiency = 1.0 / (dist_km + 1.0)
        
        # Attribute alignment: measure how well destination attributes are populated
        # and match user preferences
        attribute_count = sum([
            1 for attr in ["culture", "adventure", "wildlife", "sightseeing", "history"]
            if getattr(destination, attr, None) is not None and getattr(destination, attr) > 0
        ])
        attribute_alignment = attribute_count / 5.0  # Normalized to [0, 1]

        # ====================================
        # STEP 5: ALGORITHM 5 - WEIGHTED LINEAR SCORING
        # ====================================
        # FinalScore = α·CPS + β·Proximity + γ·AttributeAlignment + δ·Constraint + ε·Season
        # Where sum of all weights = 1.0 (normalized by blend_weights)
        final_score = (
            blend_weights["cps"] * pref_score
            + blend_weights["proximity"] * proximity_efficiency
            + blend_weights["attributes"] * attribute_alignment
        )

        results.append(
            ScoredDestination(
                destination=destination,
                distance_km=dist_km,
                preference_score=pref_score,
                geo_score=proximity_efficiency,
                package_support_score=attribute_alignment,  # Reused for attribute alignment
                final_score=final_score,
            )
        )

    # ========================================
    # STEP 6: ALGORITHM 6 - TOP-N SELECTION
    # ========================================
    # Sort by final score (descending - higher is better)
    # Formula: Top-N = Argmax_N(FinalScore)
    results.sort(key=lambda x: x.final_score, reverse=True)

    # Return top N destinations
    return results[: max(1, int(destination_top_n))]


def recommend_destinations(
    user_destination_preferences,
    user_context,
    destinations,
    ranked_packages,
    destination_top_n=5,
    destination_weights=None,
    destination_alpha=0.5,
    destination_beta=0.3,
    destination_gamma=0.2,
):
    """
    LEGACY DESTINATION RECOMMENDATION: Package-Based (Deprecated)
    
    This function is kept for backward compatibility but recommend using
    recommend_destinations_direct() instead for pure destination recommendations.
    
    Args:
        user_destination_preferences: User interests
        user_context: User location
        destinations: List of destinations
        ranked_packages: Pre-ranked packages (used for package-based scoring)
        destination_top_n: Number of recommendations
        destination_weights: Preference weights
        destination_alpha: Weight for preference
        destination_beta: Weight for geography
        destination_gamma: Weight for package support
    
    Returns:
        list: Top N ScoredDestination objects
    """
    # Default destination attribute weights
    destination_weights = destination_weights or {
        "culture": 0.2,
        "adventure": 0.2,
        "wildlife": 0.2,
        "sightseeing": 0.2,
        "history": 0.2,
    }

    # Normalize all weights
    destination_weights = _normalize_weights(destination_weights)
    blend = _normalize_weights(
        {
            "preference": destination_alpha,
            "geo": destination_beta,
            "package": destination_gamma,
        }
    )

    # Build map of destination → list of package scores supporting that destination
    package_scores = {}

    for scored in ranked_packages:
        pkg = scored.package
        dest = pkg.end_location
        if dest:
            package_scores.setdefault(dest.id, []).append(scored.final_score)

    results = []

    for destination in destinations:

        # Compute destination preference score
        pref = _destination_preference_score(user_destination_preferences, destination, destination_weights)
        
        # Compute geographic distance from user to destination
        dist = _user_to_destination_distance_km(user_context, destination)
        
        # Geographic proximity score
        geo = 1.0 / (dist + 1)

        # Aggregate package support
        pkg_score_list = package_scores.get(destination.id, [])
        pkg_score = sum(pkg_score_list) / len(pkg_score_list) if pkg_score_list else 0.0

        # Weighted Linear Scoring
        final = (
            blend["preference"] * pref
            + blend["geo"] * geo
            + blend["package"] * pkg_score
        )

        results.append(
            ScoredDestination(
                destination=destination,
                distance_km=dist,
                preference_score=pref,
                geo_score=geo,
                package_support_score=pkg_score,
                final_score=final,
            )
        )

    # Sort by final score (descending - higher is better)
    results.sort(key=lambda x: x.final_score, reverse=True)

    return results[: max(1, int(destination_top_n))]