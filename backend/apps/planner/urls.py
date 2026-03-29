from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.planner.views import AssistantChatAPIView, PlannerGenerateAPIView, TravelPlanViewSet


router = DefaultRouter()
router.register("plans", TravelPlanViewSet, basename="travel-plan")

urlpatterns = [
    path("planner/generate/", PlannerGenerateAPIView.as_view(), name="planner-generate"),
    path("assistant/chat/", AssistantChatAPIView.as_view(), name="assistant-chat"),
    path("", include(router.urls)),
]
