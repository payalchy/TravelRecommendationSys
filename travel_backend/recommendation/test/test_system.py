from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from users.models import UserProfile
from recommendation.models import Destination


class SystemTest(TestCase):

    def setUp(self):

        self.client = APIClient()

        # Create User
        self.user = User.objects.create_user(
            username="systemuser",
            password="system123"
        )

        # Create User Profile
        UserProfile.objects.create(
            user=self.user,
            budget=50000,
            preferred_duration=5,
            preferred_season="Winter",
            latitude=27.7172,
            longitude=85.3240,
        )

        # Create Destination
        Destination.objects.create(
            pName="Pokhara",
            province="Gandaki",
            latitude=28.2096,
            longitude=83.9856,
            culture=4,
            adventure=5,
            wildlife=3,
            sightseeing=5,
            history=2,
        )

    def test_complete_recommendation_system(self):

        # Authenticate user
        self.client.force_authenticate(
            user=self.user
        )

        # Call recommendation API
        response = self.client.post(
            "/api/recommend/",
            {
                "budget": 40000,
                "duration": 4,
                "preferred_season": "Winter",
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            format="json"
        )

        print("\nSYSTEM TEST RESPONSE:")
        print(response.data)

        # Check response success
        self.assertEqual(response.status_code, 200)

        # Check recommendation results exist
        self.assertIn(
            "destination_results",
            response.data
        )

        # Check at least one destination returned
        self.assertTrue(
            len(response.data["destination_results"]) > 0
        )

    def test_destination_search_system(self):

        response = self.client.get(
            "/api/destination/search/",
            {"q": "Pokhara"}
        )

        self.assertEqual(response.status_code, 200)

    def test_destination_geocode_system(self):

        response = self.client.get(
            "/api/destination/geocode/",
            {"name": "Pokhara"}
        )

        self.assertIn(
            response.status_code,
            [200, 404, 503]
        )

    def test_province_api_requires_authentication(self):

        response = self.client.get(
            "/api/destination/provinces/"
        )

        self.assertIn(
            response.status_code,
            [401, 403]
        )