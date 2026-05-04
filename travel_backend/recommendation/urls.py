from django.urls import path

from .views import (
    DestinationGeocodeAPIView,
    DestinationProvinceListAPIView,
    RecommendationAPIView,
)


urlpatterns = [
    path("recommend/", RecommendationAPIView.as_view(), name="recommend-packages"),
    path("destination/geocode/", DestinationGeocodeAPIView.as_view(), name="destination-geocode"),
    path("destination/provinces/", DestinationProvinceListAPIView.as_view(), name="destination-provinces"),
]
