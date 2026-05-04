from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import TravelStyle, UserProfile, UserProfileHistory


class UserProfileAPITests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username="profile-user",
			email="profile@example.com",
			password="strong-pass-123",
		)
		self.style_adventure = TravelStyle.objects.create(name="adventure")
		self.style_culture = TravelStyle.objects.create(name="culture")
		self.profile = UserProfile.objects.create(
			user=self.user,
			budget=10000,
			preferred_duration=3,
			preferred_season="summer",
		)
		self.profile.preferred_travel_style.add(self.style_adventure)

		self.client.force_authenticate(user=self.user)
		self.profile_url = reverse("profile")

	def test_profile_payload_supports_completion_check_fields(self):
		response = self.client.get(self.profile_url, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("budget", response.data)
		self.assertIn("preferred_duration", response.data)
		self.assertIn("preferred_travel_style", response.data)
		self.assertGreaterEqual(len(response.data["preferred_travel_style"]), 1)

	def test_profile_update_rejects_empty_travel_style_list(self):
		response = self.client.put(
			self.profile_url,
			{
				"preferred_travel_style_ids": [],
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("preferred_travel_style_ids", response.data)

	def test_profile_update_persists_and_creates_history_record(self):
		response = self.client.put(
			self.profile_url,
			{
				"budget": 25000,
				"preferred_duration": 6,
				"preferred_season": "winter",
				"preferred_travel_style_ids": [self.style_culture.id],
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)

		self.profile.refresh_from_db()
		self.assertEqual(float(self.profile.budget), 25000.0)
		self.assertEqual(self.profile.preferred_duration, 6)
		self.assertEqual(self.profile.preferred_season, "winter")
		self.assertEqual(self.profile.preferred_travel_style.count(), 1)
		self.assertEqual(self.profile.preferred_travel_style.first().name, "culture")

		self.assertEqual(UserProfileHistory.objects.filter(user=self.user).count(), 1)
