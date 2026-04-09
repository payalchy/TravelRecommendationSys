from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, TravelStyle

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        # Automatically create user profile
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    # Show username and email from related user
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    preferred_travel_style = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TravelStyle.objects.all(),
        style={'base_template': 'select_multiple.html'}
    )

    preferred_season = serializers.ChoiceField(
        choices=UserProfile.SEASON_CHOICES,
        style={'base_template': 'select.html'}
    )

    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'preferred_travel_style', 
            'preferred_season', 'budget_preference', 'preferred_duration'
        ]