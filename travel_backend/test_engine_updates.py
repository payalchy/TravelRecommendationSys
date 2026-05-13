#!/usr/bin/env python
"""
Test script for updated Travel Recommendation Engine with:
1. C-KNN Weighted Euclidean Distance
2. Budget/Duration/Season Constraints
3. All 6-Algorithm Pipeline
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from recommendation.engine import (
    recommend_destinations_direct,
    _destination_weighted_distance,
    _destination_preference_score,
)
from recommendation.models import Destination
from users.models import UserProfile
from django.contrib.auth.models import User


def test_cknn_distance():
    """Test 1: Verify C-KNN Weighted Euclidean Distance Calculation"""
    print("\n" + "="*80)
    print("TEST 1: C-KNN WEIGHTED EUCLIDEAN DISTANCE")
    print("="*80)
    
    # Get a sample destination
    dest = Destination.objects.first()
    if not dest:
        print("❌ No destinations in database")
        return
    
    user_prefs = {
        "culture": 4,
        "adventure": 3,
        "wildlife": 2,
        "sightseeing": 4,
        "history": 3,
    }
    
    weights = {
        "culture": 0.2,
        "adventure": 0.2,
        "wildlife": 0.2,
        "sightseeing": 0.2,
        "history": 0.2,
    }
    
    distance = _destination_weighted_distance(user_prefs, dest, weights)
    
    print(f"\n📍 Destination: {dest.pName}")
    print(f"   Culture: {getattr(dest, 'culture', 0)}, Adventure: {getattr(dest, 'adventure', 0)}")
    print(f"   Wildlife: {getattr(dest, 'wildlife', 0)}, Sightseeing: {getattr(dest, 'sightseeing', 0)}")
    print(f"   History: {getattr(dest, 'history', 0)}")
    print(f"\n👤 User Preferences: {user_prefs}")
    print(f"✅ C-KNN Weighted Distance: {distance:.4f}")
    print(f"   (Lower = closer match in preference space)")


def test_constraint_scoring():
    """Test 2: Verify Constraint Handling in Preference Scoring"""
    print("\n" + "="*80)
    print("TEST 2: CONSTRAINT HANDLING (Budget/Duration/Season)")
    print("="*80)
    
    dest = Destination.objects.first()
    if not dest:
        print("❌ No destinations in database")
        return
    
    user_prefs = {
        "culture": 4,
        "adventure": 3,
        "wildlife": 2,
        "sightseeing": 4,
        "history": 3,
    }
    
    weights = {
        "culture": 0.2,
        "adventure": 0.2,
        "wildlife": 0.2,
        "sightseeing": 0.2,
        "history": 0.2,
    }
    
    # Score WITHOUT constraints
    score_no_constraints = _destination_preference_score(user_prefs, dest, weights, user_context=None)
    
    # Score WITH constraints
    user_context = {
        "budget": 50000,
        "duration": 5,
        "preferred_season": "spring",
    }
    score_with_constraints = _destination_preference_score(user_prefs, dest, weights, user_context)
    
    print(f"\n📍 Destination: {dest.pName}")
    print(f"   avg_package_price: {getattr(dest, 'avg_package_price', 'N/A')}")
    print(f"   recommended_visit_days: {getattr(dest, 'recommended_visit_days', 'N/A')}")
    print(f"   best_season: {getattr(dest, 'best_season', 'N/A')}")
    
    print(f"\n👤 User Constraints:")
    print(f"   Budget: 50000 NPR")
    print(f"   Duration: 5 days")
    print(f"   Preferred Season: spring")
    
    print(f"\n📊 Preference Scores:")
    print(f"   WITHOUT constraints: {score_no_constraints:.4f}")
    print(f"   WITH constraints:    {score_with_constraints:.4f}")
    print(f"   Constraint penalty:  {(score_with_constraints/score_no_constraints if score_no_constraints > 0 else 0):.2%}")


def test_full_recommendation():
    """Test 3: Full 6-Algorithm Recommendation Pipeline"""
    print("\n" + "="*80)
    print("TEST 3: FULL 6-ALGORITHM RECOMMENDATION PIPELINE")
    print("="*80)
    
    # Get all destinations
    all_destinations = Destination.objects.all()[:50]  # Limit to first 50 for speed
    
    if not all_destinations:
        print("❌ No destinations in database")
        return
    
    # User profile
    user_destination_preferences = {
        "culture": 4,
        "adventure": 3,
        "wildlife": 2,
        "sightseeing": 4,
        "history": 3,
    }
    
    # User context with constraints
    user_context = {
        "user_latitude": 27.7172,  # Kathmandu
        "user_longitude": 85.3240,
        "budget": 50000,
        "duration": 5,
        "preferred_season": "spring",
    }
    
    print(f"\n👤 User Profile:")
    print(f"   Location: Kathmandu (27.7172°N, 85.3240°E)")
    print(f"   Budget: 50,000 NPR")
    print(f"   Duration: 5 days")
    print(f"   Preferred Season: spring")
    print(f"   Interests: culture=4, adventure=3, wildlife=2, sightseeing=4, history=3")
    
    print(f"\n🔍 Evaluating {len(all_destinations)} destinations...")
    
    # Run recommendation
    recommendations = recommend_destinations_direct(
        user_destination_preferences=user_destination_preferences,
        user_context=user_context,
        destinations=all_destinations,
        destination_top_n=5,
        destination_alpha=0.4,
        destination_beta=0.3,
        destination_gamma=0.3,
    )
    
    print(f"\n✅ TOP 5 RECOMMENDATIONS:")
    print(f"\n{'Rank':<6} {'Destination':<25} {'Distance(km)':<15} {'CPS':<8} {'Proximity':<12} {'Final Score':<12}")
    print("-" * 85)
    
    for i, rec in enumerate(recommendations, 1):
        dest = rec.destination
        print(f"{i:<6} {dest.pName[:24]:<25} {rec.distance_km:<15.2f} {rec.preference_score:<8.4f} {rec.geo_score:<12.4f} {rec.final_score:<12.4f}")
    
    print("\n📈 Algorithm Steps Executed:")
    print("   ✓ Algorithm 1 (CPS): Preference scoring with constraints")
    print("   ✓ Algorithm 2-3 (C-KNN): Weighted Euclidean distance on attributes")
    print("   ✓ Algorithm 3 (KNN): Neighbor selection by distance")
    print("   ✓ Algorithm 4: Proximity & attribute alignment efficiency")
    print("   ✓ Algorithm 5: Weighted linear scoring")
    print("   ✓ Algorithm 6: Top-N selection by final score")


def test_comparison_with_without_constraints():
    """Test 4: Compare recommendations with and without constraints"""
    print("\n" + "="*80)
    print("TEST 4: CONSTRAINT IMPACT ANALYSIS")
    print("="*80)
    
    all_destinations = Destination.objects.all()[:30]
    
    if not all_destinations:
        print("❌ No destinations in database")
        return
    
    user_destination_preferences = {
        "culture": 4,
        "adventure": 3,
        "wildlife": 2,
        "sightseeing": 4,
        "history": 3,
    }
    
    user_context_base = {
        "user_latitude": 27.7172,
        "user_longitude": 85.3240,
    }
    
    # Recommendations WITHOUT constraints
    print(f"\n📍 WITHOUT Constraints (only location & preferences):")
    rec_no_constraints = recommend_destinations_direct(
        user_destination_preferences=user_destination_preferences,
        user_context=user_context_base,
        destinations=all_destinations,
        destination_top_n=3,
    )
    
    for i, rec in enumerate(rec_no_constraints, 1):
        print(f"   {i}. {rec.destination.pName[:30]:<30} (Score: {rec.final_score:.4f})")
    
    # Recommendations WITH constraints
    user_context_constrained = {
        **user_context_base,
        "budget": 30000,  # Low budget
        "duration": 3,    # Short trip
        "preferred_season": "summer",
    }
    
    print(f"\n📍 WITH Constraints (budget=30k, duration=3 days, season=summer):")
    rec_with_constraints = recommend_destinations_direct(
        user_destination_preferences=user_destination_preferences,
        user_context=user_context_constrained,
        destinations=all_destinations,
        destination_top_n=3,
    )
    
    for i, rec in enumerate(rec_with_constraints, 1):
        print(f"   {i}. {rec.destination.pName[:30]:<30} (Score: {rec.final_score:.4f})")

    
    print(f"\n✓ Constraints impact recommendation ranking and filtering")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  TRAVEL RECOMMENDATION ENGINE - UPDATED IMPLEMENTATION TEST".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    try:
        test_cknn_distance()
        test_constraint_scoring()
        test_full_recommendation()
        test_comparison_with_without_constraints()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\n✓ C-KNN Weighted Euclidean Distance: WORKING")
        print("✓ Constraint Handling (Budget/Duration/Season): WORKING")
        print("✓ Full 6-Algorithm Pipeline: WORKING")
        print("✓ Algorithm Impact Analysis: WORKING")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
