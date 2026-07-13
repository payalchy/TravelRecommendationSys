import math
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from recommendation.models import Destination, TravelPackage, PackageItinerary, StartLocation
from recommendation.engine import recommend_destinations_direct, recommend_packages
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

        self.start = StartLocation.objects.create(
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

        self.package_adventure = TravelPackage.objects.create(
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
        self.package_budget = TravelPackage.objects.create(
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

        PackageItinerary.objects.create(
            package=self.package_adventure,
            destination=self.end_1,
            day_number=1,
            description="Day 1 itinerary",
        )
        PackageItinerary.objects.create(
            package=self.package_budget,
            destination=self.end_1,
            day_number=1,
            description="Day 1 itinerary",
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

    def test_destination_packages_are_ranked_by_recommendation_engine(self):
        url = reverse("destination-packages", args=[self.end_1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_context = {
            "budget": self.profile.budget,
            "distance": 100,
            "duration": self.profile.preferred_duration,
            "travel_type": "adventure",
        }
        scored_packages = recommend_packages(
            user_context,
            [self.package_adventure, self.package_budget],
            top_n=5,
        )
        expected_order = [item.package.name for item in scored_packages]
        actual_order = [pkg["name"] for pkg in response.data["packages"]]

        self.assertEqual(actual_order, expected_order)

    def test_recommended_packages_endpoint_returns_match_reasons(self):
        url = reverse("recommended-packages")
        response = self.client.post(
            url,
            {
                "budget": 22000,
                "duration": 4,
                "preferred_provinces": ["Gandaki"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["package_count"], 1)
        self.assertGreaterEqual(len(response.data["packages"]), 1)

        first_package = response.data["packages"][0]
        self.assertIn("recommendation_reason", first_package)
        self.assertIn("recommendation_reasons", first_package)
        self.assertIn("match_score", first_package)
        self.assertIn("destination_id", first_package)

    def test_package_distance_includes_start_location_and_itinerary_path(self):
        package = TravelPackage.objects.create(
            name="Route Distance Test",
            package_type="tour",
            transport_mode="bus",
            start_location=self.start,
            end_location=self.end_1,
            budget=15000,
            distance_km=0,
            days=2,
            number_of_travelers=2,
            description="Distance test package",
        )

        PackageItinerary.objects.create(
            package=package,
            destination=self.end_1,
            day_number=1,
            description="Day 1 route",
        )
        PackageItinerary.objects.create(
            package=package,
            destination=self.end_2,
            day_number=2,
            description="Day 2 route",
        )

        package.refresh_from_db()

        def haversine_km(lat1, lon1, lat2, lon2):
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            return 6371 * c

        expected_total = (
            haversine_km(
                self.start.latitude,
                self.start.longitude,
                self.end_1.latitude,
                self.end_1.longitude,
            )
            + haversine_km(
                self.end_1.latitude,
                self.end_1.longitude,
                self.end_2.latitude,
                self.end_2.longitude,
            )
        )

        self.assertGreater(package.distance_km, 0)
        self.assertAlmostEqual(
            round(package.distance_km, 2),
            round(expected_total, 2),
            places=2,
        )

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

    def test_destination_constraints_and_season_weights_affect_scoring(self):
        # Two destinations with identical attribute ratings and location,
        # but different budget/season support.
        dest_match = Mock(
            culture=4.0,
            adventure=4.0,
            wildlife=4.0,
            sightseeing=4.0,
            history=4.0,
            avg_package_price=100.0,
            recommended_visit_days=5,
            best_season="summer",
            latitude=27.7172,
            longitude=85.3240,
        )
        dest_mismatch = Mock(
            culture=4.0,
            adventure=4.0,
            wildlife=4.0,
            sightseeing=4.0,
            history=4.0,
            avg_package_price=1000.0,
            recommended_visit_days=5,
            best_season="winter",
            latitude=27.7172,
            longitude=85.3240,
        )

        user_destination_preferences = {
            "culture": 4,
            "adventure": 4,
            "wildlife": 4,
            "sightseeing": 4,
            "history": 4,
        }
        user_context = {
            "user_latitude": 27.7172,
            "user_longitude": 85.3240,
            "budget": 100.0,
            "duration": 5,
            "preferred_season": "summer",
        }

        results = recommend_destinations_direct(
            user_destination_preferences=user_destination_preferences,
            user_context=user_context,
            destinations=[dest_match, dest_mismatch],
            destination_top_n=2,
            destination_weights={
                "culture": 0.2,
                "adventure": 0.2,
                "wildlife": 0.2,
                "sightseeing": 0.2,
                "history": 0.2,
            },
            destination_alpha=0.0,
            destination_beta=0.0,
            destination_gamma=0.0,
            destination_delta=0.5,
            destination_epsilon=0.5,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].destination, dest_match)
        self.assertGreater(results[0].final_score, results[1].final_score)
