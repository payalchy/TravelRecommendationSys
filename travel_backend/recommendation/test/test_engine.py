from django.test import TestCase

from recommendation.engine import recommend_destinations_direct
from recommendation.models import Destination


class EngineTest(TestCase):

    def setUp(self):
        self.destination = Destination.objects.create(
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

    def test_recommend_destinations_direct(self):
        """
        Test that the recommendation engine returns
        at least one destination.
        """

        destinations = Destination.objects.all()

        user_preferences = {
            "culture": 4,
            "adventure": 5,
            "wildlife": 3,
            "sightseeing": 5,
            "history": 2,
        }

        user_context = {
            "user_latitude": 27.7172,
            "user_longitude": 85.3240,
        }

        results = recommend_destinations_direct(
            user_prefs=user_preferences,
            user_context=user_context,
            destinations=destinations,
            top_n=5,
        )

        self.assertTrue(len(results) > 0)

    def test_recommendation_returns_scored_destination(self):
        """
        Test that the recommendation result contains
        the expected scoring information.
        """

        results = recommend_destinations_direct(
            user_prefs={
                "culture": 4,
                "adventure": 5,
                "wildlife": 3,
                "sightseeing": 5,
                "history": 2,
            },
            user_context={
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            destinations=Destination.objects.all(),
            top_n=5,
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        self.assertEqual(result.destination, self.destination)

        self.assertGreaterEqual(result.preference_score, 0.0)
        self.assertLessEqual(result.preference_score, 1.0)

        self.assertGreaterEqual(result.geo_score, 0.0)
        self.assertLessEqual(result.geo_score, 1.0)

        self.assertGreaterEqual(result.final_score, 0.0)
        self.assertLessEqual(result.final_score, 1.0)

    def test_destination_distance_is_calculated(self):
        """
        Test that geographic distance is calculated from
        the user's latitude/longitude to the destination.
        """

        results = recommend_destinations_direct(
            user_prefs={
                "culture": 4,
                "adventure": 5,
                "wildlife": 3,
                "sightseeing": 5,
                "history": 2,
            },
            user_context={
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            destinations=Destination.objects.all(),
            top_n=5,
        )

        result = results[0]

        # Kathmandu -> Pokhara should be greater than zero
        self.assertGreater(result.distance_km, 0)

        # The distance should be a reasonable value for Kathmandu-Pokhara
        self.assertGreater(result.distance_km, 100)
        self.assertLess(result.distance_km, 250)

    def test_destination_preference_score(self):
        """
        Test that destination preference matching produces
        a score between 0 and 1.
        """

        results = recommend_destinations_direct(
            user_prefs={
                "culture": 4,
                "adventure": 5,
                "wildlife": 3,
                "sightseeing": 5,
                "history": 2,
            },
            user_context={
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            destinations=Destination.objects.all(),
            top_n=5,
        )

        result = results[0]

        self.assertGreaterEqual(result.preference_score, 0.0)
        self.assertLessEqual(result.preference_score, 1.0)

    def test_destination_geo_score(self):
        """
        Test that a destination closer to the user receives
        a higher geographic score.
        """

        close_destination = Destination.objects.create(
            pName="Nearby Destination",
            province="Bagmati",
            latitude=27.8,
            longitude=85.4,
            culture=4,
            adventure=4,
            wildlife=4,
            sightseeing=4,
            history=4,
        )

        results = recommend_destinations_direct(
            user_prefs={
                "culture": 4,
                "adventure": 4,
                "wildlife": 4,
                "sightseeing": 4,
                "history": 4,
            },
            user_context={
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            destinations=Destination.objects.all(),
            top_n=5,
        )

        nearby_result = next(
            result
            for result in results
            if result.destination == close_destination
        )

        pokhara_result = next(
            result
            for result in results
            if result.destination == self.destination
        )

        self.assertLess(
            nearby_result.distance_km,
            pokhara_result.distance_km,
        )

        self.assertGreater(
            nearby_result.geo_score,
            pokhara_result.geo_score,
        )

    def test_final_score_combines_preference_and_geo_score(self):
        """
        Test the current engine formula:

        Final Score =
            0.5 * Preference Score +
            0.5 * Geographic Score
        """

        results = recommend_destinations_direct(
            user_prefs={
                "culture": 4,
                "adventure": 5,
                "wildlife": 3,
                "sightseeing": 5,
                "history": 2,
            },
            user_context={
                "user_latitude": 27.7172,
                "user_longitude": 85.3240,
            },
            destinations=Destination.objects.all(),
            top_n=5,
        )

        result = results[0]

        expected_score = (
            0.5 * result.preference_score
            + 0.5 * result.geo_score
        )

        self.assertAlmostEqual(
            result.final_score,
            expected_score,
            places=6,
        )

    def test_destination_name(self):
        """
        Test destination name.
        """

        self.assertEqual(
            self.destination.pName,
            "Pokhara"
        )

    def test_destination_province(self):
        """
        Test destination province.
        """

        self.assertEqual(
            self.destination.province,
            "Gandaki"
        )

    def test_destination_coordinates(self):
        """
        Test destination latitude and longitude.
        """

        self.assertEqual(
            float(self.destination.latitude),
            28.2096
        )

        self.assertEqual(
            float(self.destination.longitude),
            83.9856
        )

    def test_destination_scores(self):
        """
        Test destination preference attributes.
        """

        self.assertEqual(
            self.destination.culture,
            4
        )

        self.assertEqual(
            self.destination.adventure,
            5
        )

        self.assertEqual(
            self.destination.wildlife,
            3
        )

        self.assertEqual(
            self.destination.sightseeing,
            5
        )

        self.assertEqual(
            self.destination.history,
            2
        )