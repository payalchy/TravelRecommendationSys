from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from recommendation.models import Destination, TravelPackage
from users.models import TravelStyle, UserProfile


class RecommendationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="recommend-user",
            email="recommend@example.com",
            password="strong-pass-123",
        )
        self.style = TravelStyle.objects.create(name="adventure")
        self.profile = UserProfile.objects.create(
            user=self.user,
            budget=22000,
            preferred_duration=4,
            preferred_season="spring",
            latitude=27.7172,
            longitude=85.3240,
        )
        self.profile.preferred_travel_style.add(self.style)

        self.client.force_authenticate(user=self.user)

        self.start = Destination.objects.create(
            pName="Kathmandu",
            province="Bagmati",
            latitude=27.7172,
            longitude=85.3240,
        )
        self.end_1 = Destination.objects.create(
            pName="Pokhara",
            province="Gandaki",
            latitude=28.2096,
            longitude=83.9856,
            culture=4.0,
            adventure=4.8,
            wildlife=3.0,
            sightseeing=4.6,
            history=3.5,
        )
        self.end_2 = Destination.objects.create(
            pName="Chitwan",
            province="Bagmati",
            latitude=27.5291,
            longitude=84.3542,
            culture=3.5,
            adventure=3.0,
            wildlife=4.9,
            sightseeing=3.4,
            history=2.8,
        )

        TravelPackage.objects.create(
            name="Balanced Adventure",
            package_type="adventure",
            transport_mode="bus",
            start_location=self.start,
            end_location=self.end_1,
            budget=20000,
            distance_km=210,
            days=4,
            number_of_travelers=2,
            description="A balanced route",
        )
        TravelPackage.objects.create(
            name="Budget Tour",
            package_type="tour",
            transport_mode="bus",
            start_location=self.start,
            end_location=self.end_2,
            budget=12000,
            distance_km=155,
            days=3,
            number_of_travelers=2,
            description="Affordable package",
        )

    def test_recommendation_uses_request_location_and_returns_destinations(self):
        url = reverse("recommend-packages")
        response = self.client.post(
            url,
            {"user_latitude": 27.65, "user_longitude": 85.28},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("used_user_location", response.data)
        self.assertEqual(response.data["used_user_location"]["source"], "request")
        self.assertGreaterEqual(response.data["destination_count"], 1)
        self.assertGreaterEqual(len(response.data["destination_results"]), 1)

    def test_recommendation_uses_profile_location_when_request_missing(self):
        url = reverse("recommend-packages")
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["used_user_location"]["source"], "profile")
        self.assertEqual(response.data["used_user_location"]["latitude"], 27.7172)
        self.assertEqual(response.data["used_user_location"]["longitude"], 85.324)

    def test_recommendation_rejects_incomplete_location_payload(self):
        url = reverse("recommend-packages")
        response = self.client.post(url, {"user_latitude": 27.6}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("recommendation.views.urlopen")
    def test_destination_geocode_endpoint_returns_coordinates(self, mock_urlopen):
        mock_response = Mock()
        mock_response.read.return_value = (
            b'[{"lat":"27.7172","lon":"85.3240","display_name":"Kathmandu, Nepal"}]'
        )
        mock_urlopen.return_value.__enter__.return_value = mock_response

        url = reverse("destination-geocode")
        response = self.client.get(url, {"name": "Kathmandu"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Kathmandu")
        self.assertEqual(response.data["latitude"], 27.7172)
        self.assertEqual(response.data["longitude"], 85.324)
