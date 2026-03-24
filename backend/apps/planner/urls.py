from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.planner.views import PlannerGenerateAPIView, TravelPlanViewSet


router = DefaultRouter()
# 已保存的 AI 行程接口。
router.register("plans", TravelPlanViewSet, basename="travel-plan")

urlpatterns = [
    # 生成 AI 行程结果。
    path("planner/generate/", PlannerGenerateAPIView.as_view(), name="planner-generate"),
    path("", include(router.urls)),
]
