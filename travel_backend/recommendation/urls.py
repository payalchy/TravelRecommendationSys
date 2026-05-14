from django.urls import path

from .views import (
    DestinationGeocodeAPIView,
    DestinationProvinceListAPIView,
    RecommendationAPIView,
    DestinationPackagesAPIView,
    DestinationSearchAPIView,
)


urlpatterns = [
    path("recommend/", RecommendationAPIView.as_view(), name="recommend-packages"),
    path("destination/search/", DestinationSearchAPIView.as_view(), name="destination-search"),
    path("destination/geocode/", DestinationGeocodeAPIView.as_view(), name="destination-geocode"),
    path("destination/provinces/", DestinationProvinceListAPIView.as_view(), name="destination-provinces"),
    path("destinations/<int:destination_id>/packages/", DestinationPackagesAPIView.as_view(), name="destination-packages"),
]
