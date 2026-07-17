from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from users.models import UserProfile
from recommendation.models import Destination


class RecommendationAPITest(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword"
        )

        UserProfile.objects.create(
            user=self.user,
            budget=50000,
            preferred_duration=5,
            preferred_season="Winter",
            latitude=27.7172,
            longitude=85.3240,
        )

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

        self.client.force_authenticate(
            user=self.user
        )

    def test_recommendation_api(self):

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

        self.assertIn(
            "destination_results",
            response.data
        )

    def test_destination_search_api(self):

        url = reverse("destination-search")

        response = self.client.get(
            url,
            {"q": "Pokhara", "limit": 1, "offset": 0}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertIn("has_more", response.data)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_destination_province_api(self):

        url = reverse("destination-provinces")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )