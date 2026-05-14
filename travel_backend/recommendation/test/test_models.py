from django.test import TestCase

from recommendation.models import Destination


class DestinationModelTest(TestCase):

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

    def test_destination_created(self):

        self.assertEqual(
            self.destination.pName,
            "Pokhara"
        )

    def test_destination_province(self):

        self.assertEqual(
            self.destination.province,
            "Gandaki"
        )

    def test_destination_string(self):

        self.assertIn(
            "Pokhara",
            str(self.destination)
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