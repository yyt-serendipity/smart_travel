from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.destinations.views import (
    AttractionViewSet,
    HomeOverviewAPIView,
    ProvinceMapDetailAPIView,
    ProvinceMapOverviewAPIView,
    TravelCityViewSet,
)


router = DefaultRouter()
router.register("cities", TravelCityViewSet, basename="travel-city")
router.register("attractions", AttractionViewSet, basename="attraction")

urlpatterns = [
    path("overview/", HomeOverviewAPIView.as_view(), name="overview"),
    path("maps/provinces/overview/", ProvinceMapOverviewAPIView.as_view(), name="province-map-overview"),
    path("maps/provinces/detail/", ProvinceMapDetailAPIView.as_view(), name="province-map-detail"),
    path("", include(router.urls)),
]
