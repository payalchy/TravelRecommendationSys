from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from users.models import UserProfile, SearchHistory
from recommendation.models import Destination


class RecommendationAPITest(APITestCase):
    """
    API tests for the recommendation system.
    """

    def setUp(self):
        """
        Create a test user, profile, and destination dataset.
        """

        # ---------------------------------------------------------
        # CREATE TEST USER
        # ---------------------------------------------------------
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword"
        )

        # ---------------------------------------------------------
        # CREATE USER PROFILE
        # ---------------------------------------------------------
        UserProfile.objects.create(
            user=self.user,
            budget=50000,
            preferred_duration=5,
            preferred_season="Winter",
            latitude=27.7172,
            longitude=85.3240,
        )

        # ---------------------------------------------------------
        # CREATE TEST DESTINATIONS
        # ---------------------------------------------------------
        destination_rows = [
            {
                "pName": "Pokhara",
                "province": "Gandaki",
                "latitude": 28.2096,
                "longitude": 83.9856,
                "culture": 4,
                "adventure": 5,
                "wildlife": 3,
                "sightseeing": 5,
                "history": 2,
            },
            {
                "pName": "Kathmandu",
                "province": "Bagmati",
                "latitude": 27.7172,
                "longitude": 85.3240,
                "culture": 5,
                "adventure": 2,
                "wildlife": 1,
                "sightseeing": 5,
                "history": 5,
            },
            {
                "pName": "Lalitpur",
                "province": "Bagmati",
                "latitude": 27.6644,
                "longitude": 85.3188,
                "culture": 4,
                "adventure": 2,
                "wildlife": 1,
                "sightseeing": 4,
                "history": 4,
            },
            {
                "pName": "Bhaktapur",
                "province": "Bagmati",
                "latitude": 27.6710,
                "longitude": 85.4298,
                "culture": 5,
                "adventure": 1,
                "wildlife": 1,
                "sightseeing": 4,
                "history": 5,
            },
            {
                "pName": "Chitwan",
                "province": "Bagmati",
                "latitude": 27.5291,
                "longitude": 84.3542,
                "culture": 3,
                "adventure": 4,
                "wildlife": 5,
                "sightseeing": 4,
                "history": 2,
            },
            {
                "pName": "Bandipur",
                "province": "Gandaki",
                "latitude": 27.9382,
                "longitude": 84.4165,
                "culture": 5,
                "adventure": 3,
                "wildlife": 1,
                "sightseeing": 4,
                "history": 4,
            },
            {
                "pName": "Lumbini",
                "province": "Lumbini",
                "latitude": 27.4670,
                "longitude": 83.2758,
                "culture": 5,
                "adventure": 1,
                "wildlife": 1,
                "sightseeing": 4,
                "history": 5,
            },
            {
                "pName": "Dhulikhel",
                "province": "Bagmati",
                "latitude": 27.6200,
                "longitude": 85.5418,
                "culture": 3,
                "adventure": 3,
                "wildlife": 1,
                "sightseeing": 4,
                "history": 3,
            },
        ]

        for row in destination_rows:
            Destination.objects.create(**row)

        # ---------------------------------------------------------
        # AUTHENTICATE TEST CLIENT
        # ---------------------------------------------------------
        self.client.force_authenticate(
            user=self.user
        )

    # ============================================================
    # RECOMMENDATION API TEST
    # ============================================================

    def test_recommendation_api(self):
        """
        Test the main recommendation API.
        """

        url = reverse("recommend-packages")

        payload = {
            "budget": 40000,
            "duration": 4,
            "preferred_season": "Winter",
            "user_latitude": 27.7172,
            "user_longitude": 85.3240,
        }

        response = self.client.post(
            url,
            payload,
            format="json"
        )

        print("\nAPI RESPONSE:")
        print(response.data)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Current API returns destination recommendations.
        self.assertIn(
            "destination_results",
            response.data
        )

        # At least one destination should be returned.
        self.assertGreater(
            len(response.data["destination_results"]),
            0
        )

    # ============================================================
    # RECOMMENDATION API PAGINATION
    # ============================================================

    def test_recommendation_api_pagination(self):
        """
        Test pagination of destination recommendations.
        """

        url = reverse("recommend-packages")

        payload = {
            "budget": 40000,
            "duration": 4,
            "preferred_season": "Winter",
            "user_latitude": 27.7172,
            "user_longitude": 85.3240,
            "limit": 5,
            "offset": 0,
            "save_history": False,
        }

        # ---------------------------------------------------------
        # FIRST PAGE
        # ---------------------------------------------------------
        first_response = self.client.post(
            url,
            payload,
            format="json"
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "batch_key",
            first_response.data
        )

        self.assertIn(
            "has_more",
            first_response.data
        )

        self.assertIn(
            "next_offset",
            first_response.data
        )

        self.assertIn(
            "destination_results",
            first_response.data
        )

        self.assertLessEqual(
            len(first_response.data["destination_results"]),
            5
        )

        # ---------------------------------------------------------
        # SECOND PAGE
        # ---------------------------------------------------------
        second_response = self.client.post(
            url,
            {
                **payload,
                "offset": first_response.data["next_offset"],
                "batch_key": first_response.data["batch_key"],
            },
            format="json"
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            second_response.data["batch_key"],
            first_response.data["batch_key"]
        )

        self.assertIn(
            "destination_results",
            second_response.data
        )

        self.assertLessEqual(
            len(second_response.data["destination_results"]),
            5
        )

    # ============================================================
    # PROVINCE-FILTERED PAGINATION
    # ============================================================

    def test_province_filtered_recommendation_pagination(self):
        """
        Test recommendation pagination when a province filter
        is applied.

        This replaces the old test that expected a non-existent
        'packages' response key.
        """

        url = reverse("recommend-packages")

        payload = {
            "budget": 40000,
            "duration": 4,
            "preferred_season": "Winter",
            "preferred_provinces": ["Bagmati"],
            "user_latitude": 27.7172,
            "user_longitude": 85.3240,
            "offset": 0,
            "limit": 6,
        }

        # ---------------------------------------------------------
        # FIRST PAGE
        # ---------------------------------------------------------
        first_response = self.client.post(
            url,
            payload,
            format="json"
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "batch_key",
            first_response.data
        )

        self.assertIn(
            "has_more",
            first_response.data
        )

        self.assertIn(
            "next_offset",
            first_response.data
        )

        self.assertIn(
            "destination_results",
            first_response.data
        )

        self.assertLessEqual(
            len(first_response.data["destination_results"]),
            6
        )

        # ---------------------------------------------------------
        # VERIFY PROVINCE FILTER
        # ---------------------------------------------------------
        for destination in first_response.data["destination_results"]:
            self.assertEqual(
                destination["province"],
                "Bagmati"
            )

        # ---------------------------------------------------------
        # SECOND PAGE
        # ---------------------------------------------------------
        if first_response.data["has_more"]:
            second_response = self.client.post(
                url,
                {
                    **payload,
                    "offset": first_response.data["next_offset"],
                    "batch_key": first_response.data["batch_key"],
                },
                format="json"
            )

            self.assertEqual(
                second_response.status_code,
                status.HTTP_200_OK
            )

            self.assertEqual(
                second_response.data["batch_key"],
                first_response.data["batch_key"]
            )

            self.assertIn(
                "destination_results",
                second_response.data
            )

            self.assertLessEqual(
                len(second_response.data["destination_results"]),
                6
            )

            for destination in second_response.data["destination_results"]:
                self.assertEqual(
                    destination["province"],
                    "Bagmati"
                )

    # ============================================================
    # YOU MIGHT ALSO LIKE
    # ============================================================

    def test_you_might_also_like_api_pagination(self):
        """
        Test pagination of the 'You Might Also Like' API.
        """

        url = reverse("you-might-also-like")

        response = self.client.get(
            url,
            {
                "offset": 0,
                "limit": 6
            }
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "results",
            response.data
        )

        self.assertIn(
            "count",
            response.data
        )

        self.assertIn(
            "has_more",
            response.data
        )

        self.assertIn(
            "next_offset",
            response.data
        )

        self.assertLessEqual(
            len(response.data["results"]),
            6
        )

        self.assertGreaterEqual(
            response.data["count"],
            len(response.data["results"])
        )

    # ============================================================
    # SEARCH HISTORY
    # ============================================================

    def test_search_history_list_api_returns_recommendation_rows(self):
        """
        Test that search history returns recommendation records.
        """

        SearchHistory.objects.create(
            user=self.user,
            query="recommendation_search",
            search_payload={
                "budget": 40000
            },
            destination_results=[
                {
                    "destination_id": 1,
                    "name": "Pokhara"
                }
            ],
        )

        url = reverse("search-history")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertGreaterEqual(
            len(response.data),
            1
        )

        self.assertTrue(
            any(
                item.get("query") == "recommendation_search"
                for item in response.data
            )
        )

    # ============================================================
    # DESTINATION SEARCH
    # ============================================================

    def test_destination_search_api_does_not_write_history(self):
        """
        Test that destination search does not create a SearchHistory
        record.
        """

        url = reverse("destination-search")

        before_count = SearchHistory.objects.filter(
            user=self.user
        ).count()

        response = self.client.get(
            url,
            {
                "q": "Pokhara",
                "limit": 1,
                "offset": 0
            }
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "results",
            response.data
        )

        self.assertIn(
            "count",
            response.data
        )

        self.assertIn(
            "has_more",
            response.data
        )

        self.assertGreaterEqual(
            response.data["count"],
            1
        )

        after_count = SearchHistory.objects.filter(
            user=self.user
        ).count()

        self.assertEqual(
            after_count,
            before_count
        )

    def test_destination_search_api(self):
        """
        Test destination search API.
        """

        url = reverse("destination-search")

        response = self.client.get(
            url,
            {
                "q": "Pokhara",
                "limit": 1,
                "offset": 0
            }
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "results",
            response.data
        )

        self.assertIn(
            "count",
            response.data
        )

        self.assertIn(
            "has_more",
            response.data
        )

        self.assertGreaterEqual(
            response.data["count"],
            1
        )

    # ============================================================
    # DESTINATION PROVINCES
    # ============================================================

    def test_destination_province_api(self):
        """
        Test destination province API.
        """

        url = reverse("destination-provinces")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # The endpoint may return either a list directly or a
        # dictionary containing province information.
        self.assertIsNotNone(
            response.data
        )