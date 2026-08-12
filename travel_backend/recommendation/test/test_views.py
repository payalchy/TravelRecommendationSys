from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.test import APITestCase

from recommendation.views import _get_payment_setting


class ViewTest(APITestCase):
    """
    Tests for recommendation views and payment configuration helpers.
    """

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword"
        )

        # Authenticate by default because the recommendation endpoints
        # require authentication.
        self.client.force_authenticate(user=self.user)

    def test_destination_search_view(self):
        """
        Test the destination search endpoint for an authenticated user.
        """

        response = self.client.get(
            reverse("destination-search"),
            {"q": "Pokhara"}
        )

        print("DESTINATION SEARCH VIEW RESPONSE:")
        print(response.data)

        self.assertEqual(response.status_code, 200)

        # Verify that the endpoint returns the expected response structure.
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertIn("has_more", response.data)

    def test_destination_province_view_authenticated(self):
        """
        Test the destination province endpoint for an authenticated user.
        """

        response = self.client.get(
            reverse("destination-provinces")
        )

        print("DESTINATION PROVINCE VIEW RESPONSE:")
        print(response.data)

        self.assertEqual(response.status_code, 200)

        # The current endpoint returns a list directly.
        # Therefore, do not expect a {"provinces": ...} dictionary.
        self.assertIsInstance(response.data, list)

    def test_destination_geocode_view(self):
        """
        Test the destination geocoding endpoint.

        The endpoint uses an external geocoding service, so the response
        can vary depending on availability of that service.
        """

        response = self.client.get(
            reverse("destination-geocode"),
            {"name": "Pokhara"}
        )

        print("DESTINATION GEOCODE VIEW RESPONSE:")
        print(response.data)

        # Accept normal success, not-found, or service-unavailable responses.
        self.assertIn(
            response.status_code,
            [200, 404, 503]
        )

        # If the request succeeds, verify the response contains results.
        if response.status_code == 200:
            self.assertIn("results", response.data)

    def test_payment_helper_reads_environment_values(self):
        """
        Verify that _get_payment_setting reads the Khalti
        environment variable correctly.
        """

        with patch.dict(
            "os.environ",
            {
                "KHALTI_SECRET_KEY": "env-secret-key"
            },
            clear=False
        ):
            self.assertEqual(
                _get_payment_setting(
                    "KHALTI_SECRET_KEY",
                    "fallback"
                ),
                "env-secret-key"
            )

    def test_payment_helper_reads_stripe_environment_values(self):
        """
        Verify that _get_payment_setting reads the Stripe
        environment variable correctly.
        """

        with patch.dict(
            "os.environ",
            {
                "STRIPE_SECRET_KEY": "stripe-env-secret"
            },
            clear=False
        ):
            self.assertEqual(
                _get_payment_setting(
                    "STRIPE_SECRET_KEY",
                    "fallback"
                ),
                "stripe-env-secret"
            )