from django.urls import path
from .views import ( RegisterView, UserProfileView, TravelStyleListView, UserProfileHistoryView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('travel-styles/', TravelStyleListView.as_view(), name='travel-styles'),
    path("profile/history/", UserProfileHistoryView.as_view(), name='profile-history'),
]