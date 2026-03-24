from rest_framework import serializers

from apps.core.tagging import normalize_public_tags
from apps.destinations.models import Attraction, TravelCity


class AttractionSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)

    def validate_tags(self, value):
        return normalize_public_tags(value)

    class Meta:
        model = Attraction
        fields = (
            "id",
            "city",
            "city_name",
            "name",
            "source_url",
            "address",
            "description",
            "opening_hours",
            "image_url",
            "rating",
            "suggested_play_time",
            "best_season",
            "ticket_info",
            "tips",
            "source_page",
            "tags",
            "source_file",
            "imported_from_excel",
        )


class TravelCityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelCity
        fields = (
            "id",
            "name",
            "province",
            "destination_type",
            "short_intro",
            "cover_image",
            "best_season",
            "recommended_days",
            "average_rating",
            "average_ticket",
            "attraction_count",
            "tags",
            "is_featured",
        )


class AttractionDetailSerializer(serializers.ModelSerializer):
    city_detail = TravelCityListSerializer(source="city", read_only=True)

    class Meta:
        model = Attraction
        fields = (
            "id",
            "city",
            "city_detail",
            "name",
            "source_url",
            "address",
            "description",
            "opening_hours",
            "image_url",
            "rating",
            "suggested_play_time",
            "best_season",
            "ticket_info",
            "tips",
            "source_page",
            "tags",
            "source_file",
            "imported_from_excel",
        )


class TravelCityDetailSerializer(serializers.ModelSerializer):
    attractions = AttractionSerializer(many=True, read_only=True)

    class Meta:
        model = TravelCity
        fields = (
            "id",
            "name",
            "province",
            "destination_type",
            "short_intro",
            "overview",
            "travel_highlights",
            "cover_image",
            "best_season",
            "recommended_days",
            "average_rating",
            "average_ticket",
            "attraction_count",
            "tags",
            "travel_tips",
            "is_featured",
            "source_file",
            "attractions",
        )
