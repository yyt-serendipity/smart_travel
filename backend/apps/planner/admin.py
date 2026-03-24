from django.contrib import admin

from apps.planner.models import TravelPlan, TripPlan


@admin.register(TripPlan)
class TripPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "traveler_name", "destination_name", "duration_days", "status", "created_at")
    search_fields = ("title", "traveler_name", "destination_name")
    list_filter = ("status", "travel_style", "budget_level")


@admin.register(TravelPlan)
class TravelPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "city", "duration_days", "budget_level", "status", "created_at")
    search_fields = ("title", "user__username", "city__name")
    list_filter = ("status", "budget_level", "companions")
