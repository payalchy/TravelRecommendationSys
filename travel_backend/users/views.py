from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import UserProfile, TravelStyle, UserProfileHistory
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    TravelStyleSerializer
)


# =========================
# REGISTER
# =========================
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email
        }, status=status.HTTP_201_CREATED)


# =========================
# PROFILE 
# =========================
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # reload DB 
        instance.refresh_from_db()

        # convert travel styles → string 
        travel_styles = ", ".join(
            [t.name for t in instance.preferred_travel_style.all()]
        )

        # SAVE HISTORY 
        UserProfileHistory.objects.create(
            user=request.user,
            budget=instance.budget,
            preferred_duration=instance.preferred_duration,
            preferred_season=instance.preferred_season,
            travel_styles=travel_styles
        )

        return Response({
            "message": "Profile updated successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


# =========================
# TRAVEL STYLE LIST
# =========================
class TravelStyleListView(generics.ListAPIView):
    queryset = TravelStyle.objects.all()
    serializer_class = TravelStyleSerializer
    permission_classes = [permissions.AllowAny]


# =========================
# PROFILE HISTORY VIEW
# =========================
class UserProfileHistoryView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfileHistory.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        history = self.get_queryset()

        return Response([
            {
                "id": h.id,
                "budget": h.budget,
                "duration": h.preferred_duration,
                "season": h.preferred_season,
                "travel_styles": h.travel_styles,
                "created_at": h.created_at
            }
            for h in history
        ])