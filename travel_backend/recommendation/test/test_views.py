from unittest.mock import patch

from django.urls import reverse
from django.contrib.auth.models import User

from rest_framework.test import APITestCase

from recommendation.views import _get_payment_setting


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

    def test_payment_helper_reads_environment_values(self):
        with patch.dict('os.environ', {'KHALTI_SECRET_KEY': 'env-secret-key'}, clear=False):
            self.assertEqual(_get_payment_setting('KHALTI_SECRET_KEY', 'fallback'), 'env-secret-key')

    def test_payment_helper_reads_stripe_environment_values(self):
        with patch.dict('os.environ', {'STRIPE_SECRET_KEY': 'stripe-env-secret'}, clear=False):
            self.assertEqual(_get_payment_setting('STRIPE_SECRET_KEY', 'fallback'), 'stripe-env-secret')