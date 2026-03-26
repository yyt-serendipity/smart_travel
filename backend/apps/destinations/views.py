import requests
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.serializers import TravelPostListSerializer
from apps.destinations.amap import AMapServiceError, fetch_city_static_map, fetch_city_weather
from apps.destinations.home_recommendations import build_home_payload
from apps.destinations.models import Attraction, TravelCity
from apps.destinations.serializers import (
    AttractionDetailSerializer,
    AttractionSerializer,
    TravelCityDetailSerializer,
    TravelCityListSerializer,
)
from apps.planner.services import build_city_recommendations


def parse_interest_list(raw_value) -> list[str]:
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    return []


class HomeOverviewAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        payload = build_home_payload(request.user)
        return Response(
            {
                **payload,
                "featured_cities": TravelCityListSerializer(payload["featured_cities"], many=True).data,
                "spotlight_attractions": AttractionSerializer(payload["spotlight_attractions"], many=True).data,
                "latest_posts": TravelPostListSerializer(
                    payload["latest_posts"],
                    many=True,
                    context={"request": request},
                ).data,
            }
        )


class TravelCityViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = TravelCity.objects.all().order_by("-is_featured", "-average_rating", "name")
        keyword = self.request.query_params.get("q")
        province = self.request.query_params.get("province")
        tag = self.request.query_params.get("tag")
        limit = self.request.query_params.get("limit")

        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(province__icontains=keyword)
                | Q(short_intro__icontains=keyword)
                | Q(overview__icontains=keyword)
            )
        if province:
            queryset = queryset.filter(province__icontains=province)
        if tag:
            queryset = queryset.filter(tags__icontains=tag)
        if limit:
            queryset = queryset[: int(limit)]
        return queryset

    def get_serializer_class(self):
        return TravelCityDetailSerializer if self.action == "retrieve" else TravelCityListSerializer

    @action(detail=False, methods=["get"])
    def recommend(self, request):
        interests = parse_interest_list(request.query_params.getlist("interest") or request.query_params.get("interests"))
        budget_level = request.query_params.get("budget_level", "balanced")
        season_hint = request.query_params.get("season_hint", "")
        cities = build_city_recommendations(interests, budget_level, season_hint)
        return Response(TravelCityListSerializer(cities, many=True).data)

    @action(detail=True, methods=["get"])
    def weather(self, request, pk=None):
        city = self.get_object()
        try:
            return Response(fetch_city_weather(city))
        except AMapServiceError as exc:
            return Response({"detail": str(exc)}, status=502)
        except requests.RequestException:
            return Response({"detail": "高德天气服务暂时不可用，请稍后重试。"}, status=502)

    @action(detail=True, methods=["get"], url_path="static-map")
    def static_map(self, request, pk=None):
        city = self.get_object()
        try:
            image_bytes, content_type = fetch_city_static_map(city)
        except AMapServiceError as exc:
            return HttpResponse(str(exc), status=502, content_type="text/plain; charset=utf-8")
        except requests.RequestException:
            return HttpResponse("高德静态地图暂时不可用，请稍后重试。", status=502, content_type="text/plain; charset=utf-8")

        response = HttpResponse(image_bytes, content_type=content_type)
        response["Cache-Control"] = "public, max-age=1800"
        return response


class AttractionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Attraction.objects.select_related("city").all().order_by("-rating", "name")
        city_id = self.request.query_params.get("city_id")
        province = self.request.query_params.get("province")
        keyword = self.request.query_params.get("q")
        tag = self.request.query_params.get("tag")
        limit = self.request.query_params.get("limit")

        if city_id:
            queryset = queryset.filter(city_id=city_id)
        if province:
            queryset = queryset.filter(city__province__icontains=province)
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(address__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(city__name__icontains=keyword)
            )
        if tag:
            queryset = queryset.filter(tags__icontains=tag)
        if limit:
            queryset = queryset[: int(limit)]
        return queryset

    def get_serializer_class(self):
        return AttractionDetailSerializer if self.action == "retrieve" else AttractionSerializer
