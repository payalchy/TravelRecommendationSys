from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, TravelStyle, SearchHistory


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
# TRAVEL STYLE SERIALIZER 
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

    #  return full objects 
    preferred_travel_style = TravelStyleSerializer(many=True, read_only=True)

    preferred_travel_style_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TravelStyle.objects.all(),
        source='preferred_travel_style',
        required=False,
    )

    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

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
            'preferred_travel_style_ids',
            'latitude',
            'longitude',
        ]

    def validate(self, attrs):
        styles_payload = attrs.get("preferred_travel_style")
        if styles_payload is not None and len(styles_payload) == 0:
            raise serializers.ValidationError(
                {"preferred_travel_style_ids": "Select at least one travel style."}
            )
        return attrs

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = "__all__"