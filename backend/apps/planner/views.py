from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.activity import log_operation
from apps.destinations.serializers import TravelCityListSerializer
from apps.planner.models import TravelPlan
from apps.planner.serializers import TravelPlanSerializer
from apps.planner.services import build_ai_plan


def parse_interest_list(raw_value) -> list[str]:
    """把兴趣字段统一转成列表，便于 AI 规划服务使用。"""

    if isinstance(raw_value, list):
        return [str(item) for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    return []


class TravelPlanViewSet(viewsets.ModelViewSet):
    """GET/POST /api/plans/ 读取或保存用户自己的 AI 行程。"""

    serializer_class = TravelPlanSerializer
    permission_classes = [IsAuthenticated]
    queryset = TravelPlan.objects.select_related("city", "user").all()

    def get_queryset(self):
        queryset = TravelPlan.objects.select_related("city", "user").order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PlannerGenerateAPIView(APIView):
    """POST /api/planner/generate/ 生成景点级 AI 行程结果。"""

    permission_classes = [AllowAny]

    def post(self, request):
        payload = {
            "city_id": request.data.get("city_id"),
            "target_city": request.data.get("target_city", ""),
            "departure_city": request.data.get("departure_city", ""),
            "duration_days": request.data.get("duration_days", 3),
            "budget_level": request.data.get("budget_level", "balanced"),
            "companions": request.data.get("companions", "双人"),
            "interests": parse_interest_list(request.data.get("interests", [])),
            "season_hint": request.data.get("season_hint", ""),
        }
        result = build_ai_plan(payload)
        if not result.get("success", True):
            log_operation(
                request,
                "planner",
                "generate-plan",
                status="failed",
                target=result.get("city"),
                detail={
                    "target_city": result.get("matched_city_name", ""),
                    "failure_stage": result.get("failure_stage", ""),
                    "failure_reason": result.get("failure_reason", ""),
                },
            )
            return Response(
                {
                    "detail": result.get("failure_reason", "生成失败，请稍后重试。"),
                    "failure_reason": result.get("failure_reason", ""),
                    "failure_stage": result.get("failure_stage", ""),
                    "fallback_reason": result.get("fallback_reason", ""),
                    "matched_city_name": result.get("matched_city_name", ""),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        city = result["city"]
        response_payload = {
            "trip_title": result["trip_title"],
            "summary": result["summary"],
            "estimated_budget": result["estimated_budget"],
            "budget_breakdown": result["budget_breakdown"],
            "city": TravelCityListSerializer(city).data if city else None,
            "recommended_cities": TravelCityListSerializer(result["recommended_cities"], many=True).data,
            "must_visit_spots": result["must_visit_spots"],
            "packing_list": result["packing_list"],
            "itinerary": result["itinerary"],
            "planner_mode": result["planner_mode"],
            "planner_provider": result.get("planner_provider", "rule"),
            "planner_model": result.get("planner_model", ""),
            "matched_city_name": result["matched_city_name"],
            "failure_reason": result.get("failure_reason", ""),
            "failure_stage": result.get("failure_stage", ""),
            "fallback_reason": result.get("fallback_reason", ""),
            "used_fallback": result.get("used_fallback", False),
        }

        if request.user.is_authenticated and request.data.get("save_plan") and city:
            plan = TravelPlan.objects.create(
                user=request.user,
                city=city,
                title=result["trip_title"],
                departure_city=payload["departure_city"],
                duration_days=payload["duration_days"],
                budget_level=payload["budget_level"],
                companions=payload["companions"],
                interests=payload["interests"],
                summary=result["summary"],
                estimated_budget=result["estimated_budget"],
                itinerary=result["itinerary"],
            )
            response_payload["saved_plan"] = TravelPlanSerializer(plan).data
            log_operation(
                request,
                "planner",
                "generate-plan",
                target=plan,
                detail={"planner_mode": result["planner_mode"], "target_city": result["matched_city_name"]},
            )
        else:
            log_operation(
                request,
                "planner",
                "generate-plan",
                target=city,
                detail={"planner_mode": result["planner_mode"], "target_city": result["matched_city_name"]},
            )

        return Response(response_payload, status=status.HTTP_200_OK)
