from rest_framework import serializers

from apps.planner.models import TravelPlan
from apps.destinations.serializers import TravelCityListSerializer


class TravelPlanSerializer(serializers.ModelSerializer):
    city_detail = TravelCityListSerializer(source="city", read_only=True)

    class Meta:
        model = TravelPlan
        fields = (
            "id",
            "user",
            "city",
            "city_detail",
            "title",
            "departure_city",
            "duration_days",
            "budget_level",
            "companions",
            "interests",
            "summary",
            "estimated_budget",
            "itinerary",
            "status",
            "created_at",
        )
        read_only_fields = ("user",)
