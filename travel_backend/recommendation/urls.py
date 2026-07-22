from django.urls import path

from .views import (
    DestinationGeocodeAPIView,
    DestinationProvinceListAPIView,
    RecommendationAPIView,
    YouMightAlsoLikeAPIView,
    RecommendedPackagesAPIView,
    RecommendedPackageDetailAPIView,
    PackageRatingAPIView,
    DestinationPackagesAPIView,
    DestinationSearchAPIView,
    BookingCreateAPIView,
    BookingListAPIView,
    PaymentInitiateAPIView,
    PaymentVerifyAPIView,
    PaymentStatusAPIView,
)


urlpatterns = [
    path("recommend/", RecommendationAPIView.as_view(), name="recommend-packages"),
    path("recommend/you-might-also-like/", YouMightAlsoLikeAPIView.as_view(), name="you-might-also-like"),
    path("recommend/available-packages/", RecommendedPackagesAPIView.as_view(), name="recommended-packages"),
    path("recommend/available-packages/<int:package_id>/", RecommendedPackageDetailAPIView.as_view(), name="recommended-package-detail"),
    path("recommend/available-packages/<int:package_id>/rate/", PackageRatingAPIView.as_view(), name="package-rate"),
    path("destination/search/", DestinationSearchAPIView.as_view(), name="destination-search"),
    path("destination/geocode/", DestinationGeocodeAPIView.as_view(), name="destination-geocode"),
    path("destination/provinces/", DestinationProvinceListAPIView.as_view(), name="destination-provinces"),
    path("destinations/<int:destination_id>/packages/", DestinationPackagesAPIView.as_view(), name="destination-packages"),
    path("recommend/bookings/", BookingCreateAPIView.as_view(), name="booking-create"),
    path("recommend/bookings/history/", BookingListAPIView.as_view(), name="booking-history"),
    path("payments/initiate/", PaymentInitiateAPIView.as_view(), name="payment-initiate"),
    path("payments/verify/", PaymentVerifyAPIView.as_view(), name="payment-verify"),
    path("payments/<int:booking_id>/status/", PaymentStatusAPIView.as_view(), name="payment-status"),
]
