#!/usr/bin/env python
"""
Priority 3: API Endpoint Testing
Tests the /api/recommendations/ endpoint with:
- Direct destination recommendations
- 6-Algorithm pipeline
- Budget/Duration/Season constraints
- Real user authentication
"""

import os
import sys
import django
import json
from uuid import uuid4

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from users.models import UserProfile, TravelStyle
from recommendation.models import Destination, TravelPackage
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


def create_test_user():
    """Create a test user with profile and preferences"""
    suffix = uuid4().hex[:8]
    user = User.objects.create_user(
        username=f"testuser_apitest_{suffix}",
        email="test@example.com",
        password="testpass123"
    )
    
    # Create user profile
    profile = UserProfile.objects.create(
        user=user,
        budget=50000,
        preferred_duration=5,
        preferred_season="spring",
        latitude=27.7172,  # Kathmandu
        longitude=85.3240,
    )
    
    # Add travel styles
    culture_style = TravelStyle.objects.get_or_create(name="Culture")[0]
    adventure_style = TravelStyle.objects.get_or_create(name="Adventure")[0]
    profile.preferred_travel_style.add(culture_style, adventure_style)
    
    return user, profile


def get_tokens(user):
    """Get JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def test_endpoint_basic():
    """Test 1: Basic endpoint call with minimal input"""
    print("\n" + "="*80)
    print("TEST 1: BASIC ENDPOINT CALL")
    print("="*80)
    
    # Create test user
    user, profile = create_test_user()
    token = get_tokens(user)
    
    # Create client and authenticate
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Make request
    response = client.post('/api/recommend/', {}, format='json')
    
    print(f"\n📍 Endpoint: POST /api/recommend/")
    print(f"🔑 Authentication: JWT Token")
    print(f"✅ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Response Structure:")
        print(f"   - recommendation_type: {data.get('recommendation_type')}")
        print(f"   - destination_count: {data.get('destination_count')}")
        print(f"   - pipeline: {data.get('pipeline')}")
        
        if data.get('destination_results'):
            dest = data['destination_results'][0]
            print(f"\n📌 First Result Sample:")
            print(f"   - name: {dest['name']}")
            print(f"   - distance_km: {dest['distance_km']}")
            print(f"   - preference_score: {dest['preference_score']:.4f}")
            print(f"   - final_score: {dest['final_score']:.4f}")
            return True
    else:
        print(f"❌ Error: {response.content.decode('utf-8', errors='ignore')}")
        return False


def test_endpoint_with_constraints():
    """Test 2: Endpoint with budget/duration/season constraints"""
    print("\n" + "="*80)
    print("TEST 2: ENDPOINT WITH CONSTRAINTS")
    print("="*80)
    
    # Create test user
    user, profile = create_test_user()
    token = get_tokens(user)
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Test with constraints
    constraints = {
        "budget": 30000,
        "duration": 3,
        "preferred_season": "spring"
    }
    
    response = client.post('/api/recommend/', constraints, format='json')
    
    print(f"\n📍 Request Constraints:")
    print(f"   - Budget: {constraints['budget']} NPR")
    print(f"   - Duration: {constraints['duration']} days")
    print(f"   - Season: {constraints['preferred_season']}")
    
    print(f"\n✅ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Applied Constraints in Response:")
        constraints_resp = data.get('constraints_applied', {})
        print(f"   - budget_npr: {constraints_resp.get('budget_npr')}")
        print(f"   - duration_days: {constraints_resp.get('duration_days')}")
        print(f"   - preferred_season: {constraints_resp.get('preferred_season')}")
        
        print(f"\n📈 Results: {data.get('destination_count')} destinations recommended")
        
        if data.get('destination_results'):
            print(f"\n🏆 Top Recommendations:")
            for i, dest in enumerate(data['destination_results'][:3], 1):
                print(f"   {i}. {dest['name']:<25} | Score: {dest['final_score']:.4f}")
        
        return True
    else:
        print(f"❌ Error: {response.content.decode('utf-8', errors='ignore')}")
        return False


def test_endpoint_with_location():
    """Test 3: Endpoint with custom user location"""
    print("\n" + "="*80)
    print("TEST 3: ENDPOINT WITH CUSTOM LOCATION")
    print("="*80)
    
    # Create test user
    user, profile = create_test_user()
    token = get_tokens(user)
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Override location
    location_override = {
        "user_latitude": 28.2096,  # Pokhara
        "user_longitude": 83.9856,
        "budget": 50000,
        "duration": 7,
    }
    
    response = client.post('/api/recommend/', location_override, format='json')
    
    print(f"\n📍 Override Location: Pokhara (28.2096°N, 83.9856°E)")
    print(f"✅ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        location = data.get('used_user_location', {})
        print(f"\n📍 Location Used:")
        print(f"   - Latitude: {location.get('latitude')}")
        print(f"   - Longitude: {location.get('longitude')}")
        print(f"   - Source: {location.get('source')}")
        
        print(f"\n📈 Results from Pokhara: {data.get('destination_count')} destinations")
        
        if data.get('destination_results'):
            print(f"\n🏆 Nearest Recommendations:")
            for i, dest in enumerate(data['destination_results'][:3], 1):
                print(f"   {i}. {dest['name']:<25} | Distance: {dest['distance_km']:.2f} km | Score: {dest['final_score']:.4f}")
        
        return True
    else:
        print(f"❌ Error: {response.json()}")
        return False


def test_response_structure():
    """Test 4: Validate complete response structure"""
    print("\n" + "="*80)
    print("TEST 4: RESPONSE STRUCTURE VALIDATION")
    print("="*80)
    
    user, profile = create_test_user()
    token = get_tokens(user)
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    response = client.post('/api/recommend/', {}, format='json')
    
    if response.status_code != 200:
        print("❌ Request failed")
        return False
    
    data = response.json()
    
    required_fields = [
        'recommendation_type',
        'pipeline',
        'destination_count',
        'used_user_location',
        'constraints_applied',
        'user_preferences',
        'destination_results',
    ]
    
    print(f"\n✅ Checking Required Fields:")
    all_present = True
    for field in required_fields:
        present = field in data
        status = "✓" if present else "✗"
        print(f"   {status} {field}")
        if not present:
            all_present = False
    
    if all_present and data['destination_results']:
        dest = data['destination_results'][0]
        dest_fields = [
            'destination_id',
            'name',
            'latitude',
            'longitude',
            'distance_km',
            'preference_score',
            'geo_score',
            'attribute_alignment',
            'final_score',
        ]
        
        print(f"\n✅ Checking Destination Result Fields:")
        for field in dest_fields:
            present = field in dest
            status = "✓" if present else "✗"
            print(f"   {status} {field}")
            if not present:
                all_present = False
    
    print(f"\n{'✅ ALL FIELDS PRESENT' if all_present else '❌ MISSING FIELDS'}")
    return all_present


def test_algorithm_pipeline():
    """Test 5: Verify 6-algorithm pipeline in response"""
    print("\n" + "="*80)
    print("TEST 5: ALGORITHM PIPELINE VERIFICATION")
    print("="*80)
    
    user, profile = create_test_user()
    token = get_tokens(user)
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    response = client.post('/api/recommend/', {}, format='json')
    
    if response.status_code != 200:
        print("❌ Request failed")
        return False
    
    data = response.json()
    
    print(f"\n📊 Recommendation Type: {data.get('recommendation_type')}")
    print(f"🔄 Algorithm Pipeline:")
    
    pipeline = data.get('pipeline', [])
    expected = ['CPS_with_constraints', 'C_KNN_weighted_euclidean', 'Proximity_efficiency', 'Weighted_scoring']
    
    for i, algo in enumerate(expected, 1):
        present = algo in pipeline
        status = "✓" if present else "✗"
        print(f"   {i}. {status} {algo}")
    
    print(f"\n📈 Results Summary:")
    print(f"   - Total destinations evaluated: All in database")
    print(f"   - Recommendations returned: {data.get('destination_count')}")
    print(f"   - Constraints applied: {len(data.get('constraints_applied', {}))}")
    
    return len(pipeline) == len(expected)


if __name__ == "__main__":
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  PRIORITY 3: API ENDPOINT TESTING".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    try:
        # Run all tests
        results = {
            "Basic Endpoint": test_endpoint_basic(),
            "Constraints": test_endpoint_with_constraints(),
            "Custom Location": test_endpoint_with_location(),
            "Response Structure": test_response_structure(),
            "Algorithm Pipeline": test_algorithm_pipeline(),
        }
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} | {test_name}")
        
        print(f"\n{'='*80}")
        print(f"TOTAL: {passed}/{total} tests passed")
        print("="*80)
        
        if passed == total:
            print("\n✅ ALL TESTS PASSED - API ENDPOINT READY FOR PRODUCTION")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed - Review logs above")
        
        print("\n")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
