from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from users.models import UserProfile
from recommendation.models import Destination


class SystemTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        # =========================================================
        # CREATE TEST USER
        # =========================================================
        self.user = User.objects.create_user(
            username="systemuser",
            password="system123"
        )

        # =========================================================
        # CREATE USER PROFILE
        # =========================================================
        UserProfile.objects.create(
            user=self.user,
            budget=50000,
            preferred_duration=5,
            preferred_season="Winter",
            latitude=27.7172,
            longitude=85.3240,
        )

        # =========================================================
        # CREATE TEST DESTINATION
        # =========================================================
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

    # =============================================================
    # COMPLETE RECOMMENDATION SYSTEM TEST
    # =============================================================

    def test_complete_recommendation_system(self):
        """
        Test the complete recommendation workflow:

        User
            ↓
        User Profile
            ↓
        Recommendation API
            ↓
        Recommendation Engine
            ↓
        Destination Results
        """

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

        # Response should be successful
        self.assertEqual(
            response.status_code,
            200
        )

        # Response should contain destination results
        self.assertIn(
            "destination_results",
            response.data
        )

        # At least one destination should be recommended
        self.assertGreater(
            len(response.data["destination_results"]),
            0
        )

        # Verify basic structure of recommendation
        first_destination = response.data["destination_results"][0]

        self.assertIn(
            "name",
            first_destination
        )

        self.assertIn(
            "distance_km",
            first_destination
        )

        self.assertIn(
            "final_score",
            first_destination
        )

    # =============================================================
    # DESTINATION SEARCH SYSTEM TEST
    # =============================================================

    def test_destination_search_system(self):
        """
        Test the destination search workflow.

        The search endpoint requires authentication.
        """

        # Authenticate user
        self.client.force_authenticate(
            user=self.user
        )

        # Search for Pokhara
        response = self.client.get(
            "/api/destination/search/",
            {
                "q": "Pokhara"
            }
        )

        print("\nDESTINATION SEARCH RESPONSE:")
        print(response.data)

        # Request should succeed
        self.assertEqual(
            response.status_code,
            200
        )

        # Response should contain results
        self.assertIn(
            "results",
            response.data
        )

        # Response should contain count
        self.assertIn(
            "count",
            response.data
        )

        # At least one result should be returned
        self.assertGreaterEqual(
            response.data["count"],
            1
        )

        # Verify that Pokhara is in the search results
        names = [
            item.get("name")
            for item in response.data["results"]
        ]

        self.assertIn(
            "Pokhara",
            names
        )

    # =============================================================
    # DESTINATION GEOCODING SYSTEM TEST
    # =============================================================

    def test_destination_geocode_system(self):
        """
        Test the destination geocoding endpoint.

        The API returns geocoding results in the following form:

        {
            "results": [
                {
                    "display_name": "...",
                    "latitude": ...,
                    "longitude": ...,
                    ...
                }
            ]
        }

        Depending on the external geocoding service, the endpoint
        may return:

            200 - coordinates/results found
            404 - destination not found
            503 - geocoding service unavailable
        """

        response = self.client.get(
            "/api/destination/geocode/",
            {
                "name": "Pokhara"
            }
        )

        print("\nDESTINATION GEOCODE RESPONSE:")
        print(response.data)

        # ---------------------------------------------------------
        # Check valid response status
        # ---------------------------------------------------------

        self.assertIn(
            response.status_code,
            [200, 404, 503]
        )

        # ---------------------------------------------------------
        # If geocoding succeeds, validate result structure
        # ---------------------------------------------------------

        if response.status_code == 200:

            # The API should return "results"
            self.assertIn(
                "results",
                response.data
            )

            # There should be at least one geocoding result
            self.assertGreater(
                len(response.data["results"]),
                0
            )

            # Get first geocoding result
            first_result = response.data["results"][0]

            # Latitude should exist
            self.assertIn(
                "latitude",
                first_result
            )

            # Longitude should exist
            self.assertIn(
                "longitude",
                first_result
            )

            # Display name should exist
            self.assertIn(
                "display_name",
                first_result
            )

            # Coordinates should be numeric
            self.assertIsNotNone(
                first_result["latitude"]
            )

            self.assertIsNotNone(
                first_result["longitude"]
            )

    # =============================================================
    # PROVINCE API AUTHENTICATION TEST
    # =============================================================

    def test_province_api_requires_authentication(self):
        """
        Verify that the province API requires authentication.
        """

        # Explicitly remove authentication
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/destination/provinces/"
        )

        # DRF may return either 401 or 403 depending on the
        # authentication and permission configuration.
        self.assertIn(
            response.status_code,
            [401, 403]
        )