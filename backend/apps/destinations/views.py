import requests
from django.http import HttpResponse
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.serializers import TravelPostListSerializer
from apps.destinations.amap import AMapServiceError, fetch_city_static_map, fetch_city_weather, fetch_district, resolve_city_geo
from apps.destinations.home_recommendations import build_home_payload
from apps.destinations.models import Attraction, TravelCity
from apps.destinations.serializers import (
    AttractionDetailSerializer,
    AttractionSerializer,
    TravelCityDetailSerializer,
    TravelCityListSerializer,
)
from apps.planner.services import build_city_recommendations
from apps.destinations.services import clean_text


def parse_interest_list(raw_value) -> list[str]:
    """把逗号字符串或数组统一转成兴趣标签列表。"""

    if isinstance(raw_value, list):
        return [str(item) for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    return []


def short_province_name(value: str) -> str:
    text = clean_text(value)
    for suffix in ("维吾尔自治区", "壮族自治区", "回族自治区", "特别行政区", "自治区", "省", "市"):
        if text.endswith(suffix):
            return text[: -len(suffix)] or text
    return text


def serialize_city_map_marker(city: TravelCity) -> dict:
    geo = resolve_city_geo(city)
    return {
        "id": city.id,
        "name": city.name,
        "province": city.province,
        "short_intro": city.short_intro,
        "cover_image": city.cover_image,
        "recommended_days": city.recommended_days,
        "average_rating": city.average_rating,
        "attraction_count": city.attraction_count,
        "tags": city.tags[:3],
        "longitude": float(geo["longitude"]),
        "latitude": float(geo["latitude"]),
    }


def build_province_groups(cities: list[TravelCity]) -> list[dict]:
    grouped = {}
    for city in cities:
        province = clean_text(city.province)
        if not province:
            continue
        item = grouped.setdefault(
            province,
            {
                "province": province,
                "short_name": short_province_name(province),
                "city_count": 0,
                "attraction_count": 0,
                "average_rating_total": 0.0,
                "average_rating_count": 0,
                "top_city": None,
            },
        )
        item["city_count"] += 1
        item["attraction_count"] += int(city.attraction_count or 0)
        if city.average_rating is not None:
            item["average_rating_total"] += float(city.average_rating)
            item["average_rating_count"] += 1

        current_top = item["top_city"]
        current_score = (
            int(current_top.attraction_count or 0),
            float(current_top.average_rating or 0),
            current_top.name,
        ) if current_top else (-1, -1.0, "")
        next_score = (
            int(city.attraction_count or 0),
            float(city.average_rating or 0),
            city.name,
        )
        if next_score > current_score:
            item["top_city"] = city

    results = []
    for item in grouped.values():
        average_rating = (
            round(item["average_rating_total"] / item["average_rating_count"], 1)
            if item["average_rating_count"]
            else None
        )
        results.append(
            {
                "province": item["province"],
                "short_name": item["short_name"],
                "city_count": item["city_count"],
                "attraction_count": item["attraction_count"],
                "average_rating": average_rating,
                "top_city": item["top_city"],
            }
        )
    return sorted(results, key=lambda item: (-item["attraction_count"], item["province"]))


class HomeOverviewAPIView(APIView):
    """GET /api/overview/ 返回首页轮播、城市、景点和社区摘要数据。"""

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


class ProvinceMapOverviewAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            china = fetch_district("中国", subdistrict=1, extensions="all")
            province_centers = {item["name"]: item["center"] for item in china["districts"]}
            cities = list(
                TravelCity.objects.exclude(province="").order_by("-is_featured", "-attraction_count", "-average_rating", "name")
            )
            province_groups = build_province_groups(cities)

            province_markers = []
            for item in province_groups:
                top_city = item["top_city"]
                center = province_centers.get(item["province"]) or {}
                longitude = center.get("longitude")
                latitude = center.get("latitude")
                try:
                    geo = resolve_city_geo(top_city)
                    longitude = float(geo["longitude"])
                    latitude = float(geo["latitude"])
                except (AMapServiceError, TypeError, ValueError):
                    pass

                if longitude is None or latitude is None:
                    continue

                province_markers.append(
                    {
                        "province": item["province"],
                        "short_name": item["short_name"],
                        "city_count": item["city_count"],
                        "attraction_count": item["attraction_count"],
                        "average_rating": item["average_rating"],
                        "longitude": longitude,
                        "latitude": latitude,
                        "top_city": {
                            "id": top_city.id,
                            "name": top_city.name,
                            "cover_image": top_city.cover_image,
                            "tags": top_city.tags[:3],
                            "average_rating": top_city.average_rating,
                        },
                    }
                )

            return Response(
                {
                    "country": {
                        "name": china["name"],
                        "center": china["center"],
                        "boundary": china["boundary"],
                    },
                    "provinces": province_markers,
                }
            )
        except AMapServiceError as exc:
            return Response({"detail": str(exc)}, status=503)
        except requests.RequestException:
            return Response({"detail": "高德行政区服务暂时不可用，请稍后再试。"}, status=502)


class ProvinceMapDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        province = clean_text(request.query_params.get("province"))
        if not province:
            return Response({"detail": "缺少 province 参数。"}, status=400)

        queryset = TravelCity.objects.filter(province=province).order_by("-is_featured", "-attraction_count", "-average_rating", "name")
        if not queryset.exists():
            queryset = TravelCity.objects.filter(province__icontains=province).order_by(
                "-is_featured",
                "-attraction_count",
                "-average_rating",
                "name",
            )
        cities = list(queryset)
        if not cities:
            return Response({"detail": f"未找到 {province} 的城市数据。"}, status=404)

        try:
            district = fetch_district(province, subdistrict=1, extensions="all")
            city_markers = []
            for city in cities:
                try:
                    city_markers.append(serialize_city_map_marker(city))
                except (AMapServiceError, TypeError, ValueError):
                    continue

            average_ratings = [float(city.average_rating) for city in cities if city.average_rating is not None]
            top_city = max(
                cities,
                key=lambda item: (
                    int(item.attraction_count or 0),
                    float(item.average_rating or 0),
                    item.name,
                ),
            )

            return Response(
                {
                    "province": {
                        "name": province,
                        "short_name": short_province_name(province),
                        "center": district["center"],
                        "boundary": district["boundary"],
                        "city_count": len(cities),
                        "attraction_count": sum(int(city.attraction_count or 0) for city in cities),
                        "average_rating": round(sum(average_ratings) / len(average_ratings), 1) if average_ratings else None,
                        "top_city": {
                            "id": top_city.id,
                            "name": top_city.name,
                            "cover_image": top_city.cover_image,
                            "tags": top_city.tags[:3],
                        },
                    },
                    "cities": city_markers,
                }
            )
        except AMapServiceError as exc:
            return Response({"detail": str(exc)}, status=503)
        except requests.RequestException:
            return Response({"detail": "高德行政区服务暂时不可用，请稍后再试。"}, status=502)


class TravelCityViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/cities/ 与 /api/cities/:id/ 浏览城市列表和详情。"""

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
        """GET /api/cities/recommend/ 根据兴趣、预算和季节推荐城市。"""

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
    """GET /api/attractions/ 与 /api/attractions/:id/ 浏览景点列表和详情。"""

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
