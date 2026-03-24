from __future__ import annotations

import os
from functools import lru_cache

import requests

from apps.destinations.models import TravelCity
from apps.destinations.services import clean_text


AMAP_BASE_URL = "https://restapi.amap.com"
WEEKDAY_LABELS = {
    "1": "周一",
    "2": "周二",
    "3": "周三",
    "4": "周四",
    "5": "周五",
    "6": "周六",
    "7": "周日",
}


class AMapServiceError(Exception):
    """Raised when AMap rejects a request or city lookup cannot be resolved."""


def get_amap_settings() -> dict | None:
    api_key = os.getenv("AMAP_API_KEY") or os.getenv("AMAP_WEB_SERVICE_KEY") or os.getenv("GAODE_API_KEY")
    if not api_key:
        return None
    return {
        "api_key": api_key,
        "base_url": (os.getenv("AMAP_BASE_URL") or AMAP_BASE_URL).rstrip("/"),
        "timeout": int(os.getenv("AMAP_REQUEST_TIMEOUT", "8")),
    }


def _require_amap_settings() -> dict:
    settings = get_amap_settings()
    if settings:
        return settings
    raise AMapServiceError("未配置高德开放平台 Key，暂时无法加载地图和天气。")


def _amap_get_json(path: str, **params) -> dict:
    settings = _require_amap_settings()
    response = requests.get(
        f"{settings['base_url']}{path}",
        params={
            **params,
            "key": settings["api_key"],
            "output": "JSON",
        },
        timeout=settings["timeout"],
    )
    response.raise_for_status()
    payload = response.json()
    if str(payload.get("status")) != "1":
        detail = clean_text(payload.get("info") or payload.get("infocode") or "高德接口返回异常。")
        raise AMapServiceError(detail)
    return payload


def _parse_location_pair(location: str) -> tuple[float | None, float | None]:
    value = clean_text(location)
    if not value or "," not in value:
        return None, None
    longitude, latitude = (value.split(",") + ["", ""])[:2]
    try:
        return float(longitude), float(latitude)
    except (TypeError, ValueError):
        return None, None


def _parse_center(location: str) -> dict:
    longitude, latitude = _parse_location_pair(location)
    return {
        "longitude": longitude,
        "latitude": latitude,
    }


def _parse_district_boundary(polyline: str) -> list[list[dict[str, float]]]:
    segments = []
    for raw_polygon in clean_text(polyline).split("|"):
        points = []
        for raw_point in raw_polygon.split(";"):
            longitude, latitude = _parse_location_pair(raw_point)
            if longitude is None or latitude is None:
                continue
            points.append({"longitude": longitude, "latitude": latitude})
        if len(points) >= 3:
            segments.append(points)
    return segments


@lru_cache(maxsize=128)
def fetch_district(keyword: str, subdistrict: int = 1, extensions: str = "base") -> dict:
    payload = _amap_get_json(
        "/v3/config/district",
        keywords=keyword,
        subdistrict=subdistrict,
        extensions=extensions,
    )
    districts = payload.get("districts") or []
    if not districts:
        raise AMapServiceError(f"暂时无法加载 {keyword} 的行政区地图数据。")

    district = districts[0]
    children = []
    for item in district.get("districts") or []:
        children.append(
            {
                "name": clean_text(item.get("name")),
                "adcode": clean_text(item.get("adcode")),
                "level": clean_text(item.get("level")),
                "center": _parse_center(item.get("center")),
            }
        )

    return {
        "name": clean_text(district.get("name") or keyword),
        "adcode": clean_text(district.get("adcode")),
        "level": clean_text(district.get("level")),
        "center": _parse_center(district.get("center")),
        "boundary": _parse_district_boundary(district.get("polyline")),
        "districts": children,
    }


@lru_cache(maxsize=2048)
def _geocode_address(address: str, city_hint: str) -> dict | None:
    payload = _amap_get_json("/v3/geocode/geo", address=address, city=city_hint)
    geocodes = payload.get("geocodes") or []
    if not geocodes:
        return None

    geo = geocodes[0]
    location = clean_text(geo.get("location"))
    longitude, latitude = (location.split(",") + ["", ""])[:2]
    return {
        "location": location,
        "longitude": longitude,
        "latitude": latitude,
        "adcode": clean_text(geo.get("adcode")),
        "citycode": clean_text(geo.get("citycode")),
        "city_name": clean_text(geo.get("city") or address),
        "province": clean_text(geo.get("province")),
        "formatted_address": clean_text(geo.get("formatted_address") or address),
    }


def resolve_city_geo(city: TravelCity) -> dict:
    lookup_candidates = []
    province = clean_text(city.province)
    if province and province not in city.name:
        lookup_candidates.append((f"{province}{city.name}", province))
    lookup_candidates.append((city.name, province))

    for address, city_hint in lookup_candidates:
        geo = _geocode_address(address, city_hint)
        if not geo:
            continue
        return {
            **geo,
            "city_name": clean_text(geo.get("city_name") or city.name),
            "province": clean_text(geo.get("province") or city.province),
            "formatted_address": clean_text(geo.get("formatted_address") or city.name),
        }

    raise AMapServiceError(f"暂时无法定位 {city.name} 的地图信息。")


def fetch_city_weather(city: TravelCity) -> dict:
    geo = resolve_city_geo(city)
    adcode = geo["adcode"]
    if not adcode:
        raise AMapServiceError(f"{city.name} 暂无可用的行政区编码，天气信息稍后再试。")

    live_payload = _amap_get_json("/v3/weather/weatherInfo", city=adcode, extensions="base")
    forecast_payload = _amap_get_json("/v3/weather/weatherInfo", city=adcode, extensions="all")

    live = (live_payload.get("lives") or [{}])[0]
    forecast = (forecast_payload.get("forecasts") or [{}])[0]
    casts = forecast.get("casts") or []

    return {
        "city_name": geo["city_name"] or city.name,
        "province": geo["province"],
        "location": geo["location"],
        "adcode": adcode,
        "report_time": clean_text(forecast.get("reporttime") or live.get("reporttime")),
        "current": {
            "weather": clean_text(live.get("weather")),
            "temperature": clean_text(live.get("temperature")),
            "wind_direction": clean_text(live.get("winddirection")),
            "wind_power": clean_text(live.get("windpower")),
            "humidity": clean_text(live.get("humidity")),
            "report_time": clean_text(live.get("reporttime")),
        },
        "forecast": [
            {
                "date": clean_text(cast.get("date")),
                "week": clean_text(cast.get("week")),
                "week_label": WEEKDAY_LABELS.get(clean_text(cast.get("week")), ""),
                "day_weather": clean_text(cast.get("dayweather")),
                "night_weather": clean_text(cast.get("nightweather")),
                "day_temp": clean_text(cast.get("daytemp")),
                "night_temp": clean_text(cast.get("nighttemp")),
                "day_wind": clean_text(cast.get("daywind")),
                "night_wind": clean_text(cast.get("nightwind")),
                "day_power": clean_text(cast.get("daypower")),
                "night_power": clean_text(cast.get("nightpower")),
            }
            for cast in casts[:4]
        ],
    }


def fetch_city_static_map(city: TravelCity) -> tuple[bytes, str]:
    geo = resolve_city_geo(city)
    settings = _require_amap_settings()
    marker_label = clean_text(city.name)[:1] or "M"

    response = requests.get(
        f"{settings['base_url']}/v3/staticmap",
        params={
            "location": geo["location"],
            "zoom": 10,
            "size": "760*360",
            "scale": 2,
            "traffic": 1,
            "markers": f"mid,0x0d5c63,{marker_label}:{geo['location']}",
            "key": settings["api_key"],
        },
        timeout=settings["timeout"],
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "image/png")
    if "json" in content_type.lower():
        payload = response.json()
        detail = clean_text(payload.get("info") or payload.get("infocode") or "静态地图服务返回异常。")
        raise AMapServiceError(detail)

    return response.content, content_type
