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

        destinations = Destination.objects.all()

        user_preferences = {
            "culture": 0.2,
            "adventure": 0.2,
            "wildlife": 0.2,
            "sightseeing": 0.2,
            "history": 0.2,
        }

        user_context = {
            "budget": 50000,
            "distance": 100,
            "duration": 5,
            "travel_type": "Adventure",
            "user_latitude": 27.7172,
            "user_longitude": 85.3240,
            "preferred_season": "Winter",
        }

        destination_weights = {
            "culture": 0.2,
            "adventure": 0.2,
            "wildlife": 0.2,
            "sightseeing": 0.2,
            "history": 0.2,
        }

        results = recommend_destinations_direct(
            user_destination_preferences=user_preferences,
            user_context=user_context,
            destinations=destinations,
            destination_top_n=5,
            destination_weights=destination_weights,
            destination_alpha=0.45,
            destination_beta=0.25,
            destination_gamma=0.2,
            destination_delta=0.05,
            destination_epsilon=0.05,
        )

        self.assertTrue(len(results) > 0)

    def test_destination_name(self):

        self.assertEqual(
            self.destination.pName,
            "Pokhara"
        )

    def test_destination_province(self):

        self.assertEqual(
            self.destination.province,
            "Gandaki"
        )

    def test_destination_coordinates(self):

        self.assertEqual(
            float(self.destination.latitude),
            28.2096
        )

        self.assertEqual(
            float(self.destination.longitude),
            83.9856
        )

    def test_destination_scores(self):

        self.assertEqual(self.destination.culture, 4)
        self.assertEqual(self.destination.adventure, 5)
        self.assertEqual(self.destination.wildlife, 3)
        self.assertEqual(self.destination.sightseeing, 5)
        self.assertEqual(self.destination.history, 2)