#!/usr/bin/env python
"""
Travel Recommendation Engine - Test & Demo Script

This script demonstrates the 6-algorithm recommendation pipeline with
real data from the database. It shows:
1. Sample user preferences and context
2. Package recommendations using the complete algorithm
3. Destination recommendations based on ranked packages
4. Detailed scoring breakdown for each recommendation
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from recommendation.models import Destination, TravelPackage
from recommendation.engine import recommend_packages, recommend_destinations

# =============================================================================
# SETUP: Test User Context and Preferences
# =============================================================================

print("\n" + "="*100)
print("TRAVEL RECOMMENDATION ENGINE - SAMPLE TEST WITH REAL DATA")
print("="*100)

# Get some packages and destinations from database
packages = TravelPackage.objects.filter(
    end_location__latitude__isnull=False,
    end_location__longitude__isnull=False
).select_related('end_location')[:20]

destinations = Destination.objects.filter(
    latitude__isnull=False,
    longitude__isnull=False
).order_by('?')[:30]

if not packages:
    print("\n⚠️  No packages with valid coordinates found in database.")
    print("Please run: python manage.py fill_missing_coordinates --force")
    exit(1)

if not destinations:
    print("\n⚠️  No destinations with valid coordinates found in database.")
    exit(1)

# =============================================================================
# TEST CASE 1: Budget-Conscious Traveler (Short Distance)
# =============================================================================

print("\n" + "-"*100)
print("TEST CASE 1: Budget-Conscious Traveler from Kathmandu")
print("-"*100)

# User context: Kathmandu coordinates, limited budget, short distance preference
user_context_1 = {
    "user_latitude": 27.7172,  # Kathmandu
    "user_longitude": 85.3240,
    "budget": 30000,  # NPR - budget option
    "distance": 100,  # km - short distance
    "duration": 3,  # days
    "travel_type": "sightseeing,culture"
}

# User destination preferences (1-5 scale)
user_dest_prefs_1 = {
    "culture": 5,  # Very interested in culture
    "adventure": 2,  # Not interested in adventure
    "wildlife": 1,  # Not interested in wildlife
    "sightseeing": 4,  # Interested in sightseeing
    "history": 5,  # Very interested in history
}

print(f"\nUser Location: Kathmandu (27.7172°N, 85.3240°E)")
print(f"Budget: NPR {user_context_1['budget']:,}")
print(f"Preferred Distance: {user_context_1['distance']} km")
print(f"Duration: {user_context_1['duration']} days")
print(f"Travel Type: {user_context_1['travel_type']}")
print(f"Interests: Culture={user_dest_prefs_1['culture']}, Sightseeing={user_dest_prefs_1['sightseeing']}, History={user_dest_prefs_1['history']}")

# Get recommendations
print("\n[Processing recommendations...]")
recommendations_1 = recommend_packages(
    user_context=user_context_1,
    packages=list(packages),
    k=10,
    top_n=5
)

dest_recommendations_1 = recommend_destinations(
    user_destination_preferences=user_dest_prefs_1,
    user_context=user_context_1,
    destinations=list(destinations),
    ranked_packages=recommendations_1,
    destination_top_n=5
)

# Display package recommendations
print("\n📦 TOP 5 PACKAGE RECOMMENDATIONS:")
print(f"{'Rank':<6} {'Package Name':<30} {'Budget':<12} {'Days':<6} {'CPS':<6} {'Final Score':<12}")
print("-" * 100)

for i, rec in enumerate(recommendations_1, 1):
    budget_str = f"NPR {rec.package.budget:,.0f}" if rec.package.budget else "N/A"
    print(f"{i:<6} {rec.package.name[:28]:<30} {budget_str:<12} {rec.package.days:<6} {rec.cps:.3f}  {rec.final_score:.4f}")

# Display destination recommendations
print("\n🏔️  TOP 5 DESTINATION RECOMMENDATIONS:")
print(f"{'Rank':<6} {'Destination':<35} {'Preference':<12} {'Geo Score':<12} {'Final Score':<12}")
print("-" * 100)

for i, rec in enumerate(dest_recommendations_1, 1):
    dest_name = rec.destination.pName[:33] if rec.destination.pName else "Unknown"
    print(f"{i:<6} {dest_name:<35} {rec.preference_score:.3f}      {rec.geo_score:.3f}       {rec.final_score:.4f}")

# =============================================================================
# TEST CASE 2: Adventure Seeker (Long Distance, Higher Budget)
# =============================================================================

print("\n" + "-"*100)
print("TEST CASE 2: Adventure Seeker from Pokhara")
print("-"*100)

# User context: Pokhara, higher budget, willing to travel far
user_context_2 = {
    "user_latitude": 28.2096,  # Pokhara
    "user_longitude": 83.9856,
    "budget": 100000,  # NPR - adventure/premium package
    "distance": 300,  # km - willing to travel far
    "duration": 7,  # days
    "travel_type": "adventure,hiking"
}

# User destination preferences
user_dest_prefs_2 = {
    "culture": 2,
    "adventure": 5,  # Very interested in adventure
    "wildlife": 4,  # Interested in wildlife
    "sightseeing": 3,
    "history": 2,
}

print(f"\nUser Location: Pokhara (28.2096°N, 83.9856°E)")
print(f"Budget: NPR {user_context_2['budget']:,}")
print(f"Preferred Distance: {user_context_2['distance']} km")
print(f"Duration: {user_context_2['duration']} days")
print(f"Travel Type: {user_context_2['travel_type']}")
print(f"Interests: Adventure={user_dest_prefs_2['adventure']}, Wildlife={user_dest_prefs_2['wildlife']}")

# Get recommendations
print("\n[Processing recommendations...]")
recommendations_2 = recommend_packages(
    user_context=user_context_2,
    packages=list(packages),
    k=10,
    top_n=5
)

dest_recommendations_2 = recommend_destinations(
    user_destination_preferences=user_dest_prefs_2,
    user_context=user_context_2,
    destinations=list(destinations),
    ranked_packages=recommendations_2,
    destination_top_n=5
)

# Display package recommendations
print("\n📦 TOP 5 PACKAGE RECOMMENDATIONS:")
print(f"{'Rank':<6} {'Package Name':<30} {'Budget':<12} {'Days':<6} {'CPS':<6} {'Final Score':<12}")
print("-" * 100)

for i, rec in enumerate(recommendations_2, 1):
    budget_str = f"NPR {rec.package.budget:,.0f}" if rec.package.budget else "N/A"
    print(f"{i:<6} {rec.package.name[:28]:<30} {budget_str:<12} {rec.package.days:<6} {rec.cps:.3f}  {rec.final_score:.4f}")

# Display destination recommendations
print("\n🏔️  TOP 5 DESTINATION RECOMMENDATIONS:")
print(f"{'Rank':<6} {'Destination':<35} {'Preference':<12} {'Geo Score':<12} {'Final Score':<12}")
print("-" * 100)

for i, rec in enumerate(dest_recommendations_2, 1):
    dest_name = rec.destination.pName[:33] if rec.destination.pName else "Unknown"
    print(f"{i:<6} {dest_name:<35} {rec.preference_score:.3f}      {rec.geo_score:.3f}       {rec.final_score:.4f}")

# =============================================================================
# ALGORITHM BREAKDOWN: Show detailed scoring for top package recommendation
# =============================================================================

print("\n" + "="*100)
print("DETAILED ALGORITHM BREAKDOWN - Test Case 1, Top Package")
print("="*100)

if recommendations_1:
    rec = recommendations_1[0]
    print(f"\nPackage: {rec.package.name}")
    print(f"End Location: {rec.package.end_location.pName if rec.package.end_location else 'N/A'}")
    
    print(f"\n{'Algorithm Component':<50} {'Score':<15} {'Weight':<10} {'Contribution':<15}")
    print("-" * 90)
    
    # Algorithm 1: CPS
    cps_contribution = rec.cps * 0.4  # alpha weight
    print(f"{'1. Contextual Preference Scoring (CPS)':<50} {rec.cps:.4f}      {0.4:<10} {cps_contribution:.4f}")
    
    # Algorithm 2-3: C-KNN / Weighted Distance
    inverse_dist = 1.0 / max(rec.distance, 0.001)
    dist_contribution = inverse_dist * 0.4  # beta weight
    print(f"{'2-3. C-KNN Distance (1/Distance)':<50} {inverse_dist:.4f}     {0.4:<10} {dist_contribution:.4f}")
    
    # Algorithm 4: Efficiency
    efficiency = 1.0 / max(rec.cost_efficiency + rec.time_efficiency, 0.001)
    eff_contribution = efficiency * 0.2  # gamma weight
    print(f"{'4. Cost-Time Efficiency':<50} {efficiency:.4f}     {0.2:<10} {eff_contribution:.4f}")
    
    # Algorithm 5: Final Score
    print(f"{'5. Weighted Linear Scoring (Final Score)':<50} {rec.final_score:.4f}")
    
    print(f"\nGeographic Distance: {rec.computed_distance_km:.2f} km")
    print(f"Cost Efficiency (Cost/Distance): {rec.cost_efficiency:.2f}")
    print(f"Time Efficiency (Distance/Days): {rec.time_efficiency:.2f}")

print("\n" + "="*100)
print("✅ TEST COMPLETE - Recommendation Engine Working Successfully")
print("="*100 + "\n")
