from django.urls import reverse
from django.contrib.auth.models import User

from rest_framework.test import APITestCase


class ViewTest(APITestCase):

    def setUp(self):

        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword"
        )

    def test_destination_search_view(self):

        response = self.client.get(
            reverse("destination-search"),
            {"q": "Pokhara"}
        )

        self.assertEqual(response.status_code, 200)

    def test_destination_province_view_authenticated(self):

        # IMPORTANT FIX
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("destination-provinces")
        )

        self.assertEqual(response.status_code, 200)

    def test_destination_geocode_view(self):

        response = self.client.get(
            reverse("destination-geocode"),
            {"name": "Pokhara"}
        )

        # External API responses may vary
        self.assertIn(
            response.status_code,
            [200, 404, 503]
        )