from django.urls import path

from .views import (
    DestinationGeocodeAPIView,
    DestinationProvinceListAPIView,
    RecommendationAPIView,
    YouMightAlsoLikeAPIView,
    DestinationPackagesAPIView,
    DestinationSearchAPIView,
)


urlpatterns = [
    path("recommend/", RecommendationAPIView.as_view(), name="recommend-packages"),
    path("recommend/you-might-also-like/", YouMightAlsoLikeAPIView.as_view(), name="you-might-also-like"),
    path("destination/search/", DestinationSearchAPIView.as_view(), name="destination-search"),
    path("destination/geocode/", DestinationGeocodeAPIView.as_view(), name="destination-geocode"),
    path("destination/provinces/", DestinationProvinceListAPIView.as_view(), name="destination-provinces"),
    path("destinations/<int:destination_id>/packages/", DestinationPackagesAPIView.as_view(), name="destination-packages"),
]
