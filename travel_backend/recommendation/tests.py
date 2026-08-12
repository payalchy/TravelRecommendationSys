import math
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from recommendation.models import (
    Destination,
    TravelPackage,
    PackageItinerary,
    StartLocation,
)
from recommendation.engine import (
    recommend_destinations_direct,
    recommend_packages,
)
from users.models import TravelStyle, UserProfile


class RecommendationAPITests(APITestCase):

    def setUp(self):
        # ---------------------------------------------------------
        # USER AND PROFILE
        # ---------------------------------------------------------
        self.user = User.objects.create_user(
            username="recommend-user",
            email="recommend@example.com",
            password="strong-pass-123",
        )

        self.style = TravelStyle.objects.create(
            name="adventure"
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            budget=22000,
            preferred_duration=4,
            preferred_season="spring",
            latitude=27.7172,
            longitude=85.3240,
        )

        self.profile.preferred_travel_style.add(self.style)

        # Authenticate all API requests
        self.client.force_authenticate(user=self.user)

        # ---------------------------------------------------------
        # START LOCATION
        # ---------------------------------------------------------
        self.start = StartLocation.objects.create(
            pName="Kathmandu",
            province="Bagmati",
            latitude=27.7172,
            longitude=85.3240,
        )

        # ---------------------------------------------------------
        # DESTINATIONS
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # TRAVEL PACKAGES
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # ITINERARIES
        # ---------------------------------------------------------
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

    # =============================================================
    # RECOMMENDATION API TESTS
    # =============================================================

    def test_recommendation_uses_request_location_and_returns_destinations(self):
        """
        Verify that the recommendation endpoint uses the location
        supplied in the request.
        """

        url = reverse("recommend-packages")

        response = self.client.post(
            url,
            {
                "user_latitude": 27.65,
                "user_longitude": 85.28,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "used_user_location",
            response.data,
        )

        self.assertEqual(
            response.data["used_user_location"]["source"],
            "request",
        )

        self.assertGreaterEqual(
            response.data["destination_count"],
            1,
        )

        self.assertGreaterEqual(
            len(response.data["destination_results"]),
            1,
        )

    def test_recommendation_uses_profile_location_when_request_missing(self):
        """
        Verify that the user's saved profile location is used when
        latitude and longitude are not provided in the request.
        """

        url = reverse("recommend-packages")

        response = self.client.post(
            url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["used_user_location"]["source"],
            "profile",
        )

        self.assertEqual(
            response.data["used_user_location"]["latitude"],
            27.7172,
        )

        self.assertEqual(
            response.data["used_user_location"]["longitude"],
            85.324,
        )

    def test_recommendation_rejects_incomplete_location_payload(self):
        """
        Verify that supplying only one coordinate is rejected.
        """

        url = reverse("recommend-packages")

        response = self.client.post(
            url,
            {
                "user_latitude": 27.6,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "error",
            response.data,
        )

    # =============================================================
    # PACKAGE RANKING TEST
    # =============================================================

    def test_destination_packages_are_ranked_by_recommendation_engine(self):
        """
        Verify that the destination-packages endpoint returns
        packages in the same order produced by recommend_packages().
        """

        url = reverse(
            "destination-packages",
            args=[self.end_1.id],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        # Current recommendation engine context
        user_context = {
            "budget": self.profile.budget,
            "distance": 100,
            "duration": self.profile.preferred_duration,
            "travel_type": "adventure",
        }

        scored_packages = recommend_packages(
            user_context,
            [
                self.package_adventure,
                self.package_budget,
            ],
            top_n=5,
        )

        expected_order = [
            item.package.name
            for item in scored_packages
        ]

        actual_order = [
            package["name"]
            for package in response.data["packages"]
        ]

        self.assertEqual(
            actual_order,
            expected_order,
        )

    # =============================================================
    # RECOMMENDED PACKAGES ENDPOINT
    # =============================================================

    def test_recommended_packages_endpoint_returns_match_reasons(self):
        """
        Verify that the recommended-packages endpoint returns
        recommendation information for each package.
        """

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

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertGreaterEqual(
            response.data["package_count"],
            1,
        )

        self.assertGreaterEqual(
            len(response.data["packages"]),
            1,
        )

        first_package = response.data["packages"][0]

        self.assertIn(
            "recommendation_reason",
            first_package,
        )

        self.assertIn(
            "recommendation_reasons",
            first_package,
        )

        self.assertIn(
            "match_score",
            first_package,
        )

        self.assertIn(
            "destination_id",
            first_package,
        )

    # =============================================================
    # DISTANCE CALCULATION TEST
    # =============================================================

    def test_package_distance_includes_start_location_and_itinerary_path(self):
        """
        Verify that package distance is calculated using:

        Start Location
              ↓
        Itinerary Destination 1
              ↓
        Itinerary Destination 2
        """

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

        # ---------------------------------------------------------
        # Haversine helper used only for test verification
        # ---------------------------------------------------------
        def haversine_km(
            lat1,
            lon1,
            lat2,
            lon2,
        ):
            lat1, lon1, lat2, lon2 = map(
                math.radians,
                [
                    lat1,
                    lon1,
                    lat2,
                    lon2,
                ],
            )

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat1)
                * math.cos(lat2)
                * math.sin(dlon / 2) ** 2
            )

            c = 2 * math.asin(
                math.sqrt(a)
            )

            return 6371 * c

        # Kathmandu → Pokhara
        start_to_first = haversine_km(
            self.start.latitude,
            self.start.longitude,
            self.end_1.latitude,
            self.end_1.longitude,
        )

        # Pokhara → Chitwan
        first_to_second = haversine_km(
            self.end_1.latitude,
            self.end_1.longitude,
            self.end_2.latitude,
            self.end_2.longitude,
        )

        expected_total = (
            start_to_first
            + first_to_second
        )

        self.assertGreater(
            package.distance_km,
            0,
        )

        self.assertAlmostEqual(
            round(package.distance_km, 2),
            round(expected_total, 2),
            places=2,
        )

    # =============================================================
    # GEOCODING ENDPOINT TEST
    # =============================================================

    @patch("recommendation.views.urlopen")
    def test_destination_geocode_endpoint_returns_coordinates(
        self,
        mock_urlopen,
    ):
        """
        Verify that the destination geocoding endpoint correctly
        processes the geocoding response.
        """

        mock_response = Mock()

        mock_response.read.return_value = (
            b'[{"lat":"27.7172",'
            b'"lon":"85.3240",'
            b'"display_name":"Kathmandu, Nepal"}]'
        )

        mock_urlopen.return_value.__enter__.return_value = (
            mock_response
        )

        url = reverse(
            "destination-geocode"
        )

        response = self.client.get(
            url,
            {
                "name": "Kathmandu",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["name"],
            "Kathmandu",
        )

        self.assertEqual(
            response.data["latitude"],
            27.7172,
        )

        self.assertEqual(
            response.data["longitude"],
            85.324,
        )

    # =============================================================
    # DESTINATION ENGINE TEST
    # =============================================================

    def test_destination_engine_ranks_by_preference_and_proximity(self):
        """
        Verify the current destination recommendation algorithm.

        Current engine:
            preference score = average similarity of
            culture, adventure, wildlife, sightseeing and history

            geo score = 1 / (1 + distance / 50)

            final score = 0.5 * preference + 0.5 * geo score
        """

        # ---------------------------------------------------------
        # User preferences
        # ---------------------------------------------------------
        user_destination_preferences = {
            "culture": 4,
            "adventure": 4,
            "wildlife": 4,
            "sightseeing": 4,
            "history": 4,
        }

        # ---------------------------------------------------------
        # User location
        # ---------------------------------------------------------
        user_context = {
            "user_latitude": 27.7172,
            "user_longitude": 85.3240,
        }

        results = recommend_destinations_direct(
            user_prefs=user_destination_preferences,
            user_context=user_context,
            destinations=[
                self.end_1,
                self.end_2,
            ],
            top_n=2,
        )

        # Two destinations should be returned
        self.assertEqual(
            len(results),
            2,
        )

        # Every result should contain a destination
        for result in results:
            self.assertIsNotNone(
                result.destination
            )

        # Final scores should be in descending order
        self.assertGreaterEqual(
            results[0].final_score,
            results[1].final_score,
        )

        # Distance should be non-negative
        for result in results:
            self.assertGreaterEqual(
                result.distance_km,
                0,
            )

        # Preference and geographic scores should
        # be between 0 and 1.
        for result in results:
            self.assertGreaterEqual(
                result.preference_score,
                0,
            )

            self.assertLessEqual(
                result.preference_score,
                1,
            )

            self.assertGreaterEqual(
                result.geo_score,
                0,
            )

            self.assertLessEqual(
                result.geo_score,
                1,
            )

    # =============================================================
    # DESTINATION PREFERENCE SCORE TEST
    # =============================================================

    def test_destination_preference_score_is_calculated_correctly(self):
        """
        Verify that the destination preference score is the average
        similarity across the five preference attributes.
        """

        destination = Mock(
            culture=4.0,
            adventure=4.0,
            wildlife=4.0,
            sightseeing=4.0,
            history=4.0,
            latitude=27.7172,
            longitude=85.3240,
        )

        user_preferences = {
            "culture": 4,
            "adventure": 4,
            "wildlife": 4,
            "sightseeing": 4,
            "history": 4,
        }

        user_context = {
            "user_latitude": 27.7172,
            "user_longitude": 85.3240,
        }

        results = recommend_destinations_direct(
            user_prefs=user_preferences,
            user_context=user_context,
            destinations=[destination],
            top_n=1,
        )

        self.assertEqual(
            len(results),
            1,
        )

        result = results[0]

        # All user preferences exactly match
        # destination values, so similarity = 1.
        self.assertAlmostEqual(
            result.preference_score,
            1.0,
            places=5,
        )

        # Same coordinates mean zero distance.
        self.assertAlmostEqual(
            result.distance_km,
            0.0,
            places=5,
        )

        # At zero distance:
        # geo_score = 1 / (1 + 0/50) = 1
        self.assertAlmostEqual(
            result.geo_score,
            1.0,
            places=5,
        )

        # final = 0.5(1) + 0.5(1) = 1
        self.assertAlmostEqual(
            result.final_score,
            1.0,
            places=5,
        )

    # =============================================================
    # PACKAGE ITINERARY DISTANCE USED BY ENGINE
    # =============================================================

    def test_recommendation_engine_uses_itinerary_distance(self):
        """
        Verify that recommend_packages() uses the itinerary distance
        rather than only TravelPackage.distance_km.
        """

        package = TravelPackage.objects.create(
            name="Itinerary Distance Package",
            package_type="adventure",
            transport_mode="bus",
            start_location=self.start,
            end_location=self.end_1,
            budget=20000,
            distance_km=9999,
            days=4,
            number_of_travelers=2,
            description="Test itinerary distance",
        )

        PackageItinerary.objects.create(
            package=package,
            destination=self.end_1,
            day_number=1,
            description="Pokhara route",
        )

        # Calculate the expected itinerary distance
        package.refresh_from_db()

        expected_distance = package.calculate_distance_km()

        user_context = {
            "budget": 22000,
            "distance": 100,
            "duration": 4,
            "travel_type": "adventure",
        }

        results = recommend_packages(
            user_context,
            [package],
            k=1,
            top_n=1,
        )

        self.assertEqual(
            len(results),
            1,
        )

        result = results[0]

        # The engine's computed_distance_km should match
        # the itinerary-based distance.
        self.assertAlmostEqual(
            result.computed_distance_km,
            expected_distance,
            places=2,
        )

        # It should NOT simply use the manually supplied
        # distance_km value of 9999.
        self.assertNotEqual(
            result.computed_distance_km,
            9999,
        )

    # =============================================================
    # PACKAGE CPS TEST
    # =============================================================

    def test_package_cps_returns_valid_score(self):
        """
        Verify that CPS produces a score between 0 and 1.
        """

        user_context = {
            "budget": 22000,
            "distance": 100,
            "duration": 4,
            "travel_type": "adventure",
        }

        results = recommend_packages(
            user_context,
            [self.package_adventure],
            k=1,
            top_n=1,
        )

        self.assertEqual(
            len(results),
            1,
        )

        result = results[0]

        self.assertGreaterEqual(
            result.cps,
            0,
        )

        self.assertLessEqual(
            result.cps,
            1,
        )

    # =============================================================
    # PACKAGE FINAL SCORE TEST
    # =============================================================

    def test_package_final_score_is_calculated(self):
        """
        Verify that the package recommendation engine produces
        CPS, weighted distance, efficiency values and final score.
        """

        user_context = {
            "budget": 22000,
            "distance": 100,
            "duration": 4,
            "travel_type": "adventure",
        }

        results = recommend_packages(
            user_context,
            [
                self.package_adventure,
                self.package_budget,
            ],
            k=2,
            top_n=2,
        )

        self.assertEqual(
            len(results),
            2,
        )

        for result in results:

            self.assertIsNotNone(
                result.package
            )

            self.assertGreaterEqual(
                result.cps,
                0,
            )

            self.assertGreaterEqual(
                result.distance,
                0,
            )

            self.assertGreaterEqual(
                result.computed_distance_km,
                0,
            )

            self.assertGreaterEqual(
                result.cost_efficiency,
                0,
            )

            self.assertGreaterEqual(
                result.time_efficiency,
                0,
            )

            self.assertGreaterEqual(
                result.final_score,
                0,
            )

        # Results must be sorted by final score
        # from highest to lowest.
        self.assertGreaterEqual(
            results[0].final_score,
            results[1].final_score,
        )