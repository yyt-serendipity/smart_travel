from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.destinations.views import (
    AttractionViewSet,
    HomeOverviewAPIView,
    TravelCityViewSet,
)


router = DefaultRouter()
router.register("cities", TravelCityViewSet, basename="travel-city")
router.register("attractions", AttractionViewSet, basename="attraction")

urlpatterns = [
    path("overview/", HomeOverviewAPIView.as_view(), name="overview"),
    path("", include(router.urls)),
]
