from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, TravelStyle


# =========================
# REGISTER SERIALIZER
# =========================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        # auto-create profile
        UserProfile.objects.create(user=user)
        return user


# =========================
# TRAVEL STYLE SERIALIZER (IMPORTANT FIX)
# =========================
class TravelStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelStyle
        fields = ['id', 'name']


# =========================
# USER PROFILE SERIALIZER
# =========================
class UserProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    #  return full objects (NOT just IDs)
    preferred_travel_style = TravelStyleSerializer(many=True, read_only=True)

    # write-only field for updating (IDs from frontend)
    preferred_travel_style_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TravelStyle.objects.all(),
        write_only=True,
        source='preferred_travel_style'
    )

    preferred_season = serializers.ChoiceField(
        choices=UserProfile.SEASON_CHOICES
    )

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'email',
            'budget',
            'preferred_duration',
            'preferred_season',
            'preferred_travel_style',
            'preferred_travel_style_ids'
        ]