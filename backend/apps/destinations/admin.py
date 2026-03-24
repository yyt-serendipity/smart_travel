from django.contrib import admin

from apps.destinations.models import Attraction, Destination, TravelCity


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country", "best_season", "estimated_budget", "rating")
    search_fields = ("name", "city", "country", "tagline")
    list_filter = ("country", "best_season")


@admin.register(TravelCity)
class TravelCityAdmin(admin.ModelAdmin):
    list_display = ("name", "province", "destination_type", "attraction_count", "average_rating", "is_featured")
    search_fields = ("name", "province", "overview", "travel_highlights")
    list_filter = ("destination_type", "is_featured", "province")


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "rating", "suggested_play_time", "source_page", "imported_from_excel")
    search_fields = ("name", "city__name", "address", "description")
    list_filter = ("city", "imported_from_excel")
