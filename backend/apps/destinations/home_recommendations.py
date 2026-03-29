from __future__ import annotations

from collections import Counter
from decimal import Decimal

from django.db.models import Count

from apps.community.models import TravelPost
from apps.destinations.attraction_recommendations import (
    MODEL_NAME,
    UserPreferenceProfile,
    build_attraction_recommendation_bundle,
    serialize_profile,
)
from apps.destinations.models import Attraction, TravelCity
from apps.users.services import serialize_home_city


STYLE_KEYWORDS = {
    "自然风光": ["自然", "山", "湖", "海", "岛", "森林", "草原", "雪山", "峡谷", "瀑布"],
    "历史人文": ["历史", "人文", "古城", "古镇", "遗址", "博物馆", "故居", "寺", "街区"],
    "城市漫游": ["城市", "街区", "夜景", "骑楼", "地标", "步行街", "公园", "老街"],
    "周末度假": ["度假", "温泉", "轻松", "周末", "休闲", "短途", "疗愈"],
    "亲子出游": ["亲子", "乐园", "动物园", "海洋馆", "公园", "互动"],
    "美食寻味": ["美食", "小吃", "夜市", "餐厅", "烟火", "风味"],
    "摄影出片": ["摄影", "日出", "日落", "花海", "观景", "夜景", "打卡"],
    "户外徒步": ["徒步", "露营", "登山", "骑行", "漂流", "越野", "户外"],
}


def compact_text(parts) -> str:
    return " ".join(str(part or "").strip() for part in parts if str(part or "").strip())


def short_province_name(value: str) -> str:
    text = compact_text([value])
    for suffix in ("维吾尔自治区", "壮族自治区", "回族自治区", "特别行政区", "自治区", "省", "市"):
        if text.endswith(suffix):
            return text[: -len(suffix)] or text
    return text


def _serialize_decimal(value) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _serialize_top_city(city: TravelCity | None) -> dict | None:
    if city is None:
        return None
    return {
        "id": city.id,
        "name": city.name,
        "cover_image": city.cover_image,
        "tags": (city.tags or [])[:3],
        "average_rating": _serialize_decimal(city.average_rating),
    }


def build_province_groups(cities: list[TravelCity]) -> list[dict]:
    grouped = {}
    for city in cities:
        province = compact_text([city.province])
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


def build_home_stats() -> dict:
    return {
        "provinceCount": TravelCity.objects.exclude(province="").values("province").distinct().count(),
        "cityCount": TravelCity.objects.count(),
        "attractionCount": Attraction.objects.count(),
        "latestPostCount": 0,
    }


def build_home_province_cards(limit: int = 12) -> list[dict]:
    cities = list(
        TravelCity.objects.exclude(province="")
        .order_by("-is_featured", "-attraction_count", "-average_rating", "name")
    )
    cards = []
    for item in build_province_groups(cities)[:limit]:
        cards.append(
            {
                "province": item["province"],
                "shortName": item["short_name"],
                "cityCount": item["city_count"],
                "attractionCount": item["attraction_count"],
                "averageRating": item["average_rating"],
                "topCity": _serialize_top_city(item["top_city"]),
            }
        )
    return cards


def count_style_hits(text: str, favorite_styles: list[str]) -> tuple[int, list[str]]:
    matched_styles = []
    for style in favorite_styles:
        keywords = STYLE_KEYWORDS.get(style, [style])
        if any(keyword in text for keyword in keywords):
            matched_styles.append(style)
    return len(matched_styles), matched_styles


def city_text_blob(city: TravelCity) -> str:
    return compact_text(
        [
            city.name,
            city.province,
            city.short_intro,
            city.overview,
            city.travel_highlights,
            city.best_season,
            " ".join(city.tags or []),
        ]
    )


def attraction_text_blob(attraction: Attraction) -> str:
    return compact_text(
        [
            attraction.name,
            attraction.city.name if attraction.city_id else "",
            attraction.city.province if attraction.city_id else "",
            attraction.description,
            attraction.address,
            attraction.best_season,
            attraction.suggested_play_time,
            " ".join(attraction.tags or []),
        ]
    )


def score_city(city: TravelCity, home_city: TravelCity | None, favorite_styles: list[str]) -> tuple[float, list[str]]:
    text = city_text_blob(city)
    style_hits, matched_styles = count_style_hits(text, favorite_styles)
    score = float(city.average_rating or 0) * 10
    score += min(city.attraction_count or 0, 40)
    score += style_hits * 18

    if city.is_featured:
        score += 6

    if home_city:
        if city.id == home_city.id:
            score += 18
        elif city.province and city.province == home_city.province:
            score += 14

    return score, matched_styles


def build_recommendation_copy(recommendation_profile, model_name: str) -> dict:
    home_city = recommendation_profile.home_city
    display_styles = recommendation_profile.explicit_styles or recommendation_profile.top_styles

    if not recommendation_profile.is_personalized:
        return {
            "is_personalized": False,
            "home_city": None,
            "favorite_styles": [],
            "spotlight_title": "热门景点精选",
            "spotlight_description": "使用 TOPSIS 综合评分模型，按景点质量、内容完整度和城市热度做排序。",
            "city_title": "全国目的地推荐",
            "city_description": "优先展示适合直接进入城市详情、继续看景点与社区内容的热门城市。",
            "model_name": model_name,
            "profile_summary": {
                "top_styles": [],
                "evidence": [],
                "activity_summary": recommendation_profile.activity_summary,
            },
        }

    style_text = "、".join(display_styles[:3]) if display_styles else "你的旅行偏好"
    if home_city:
        return {
            "is_personalized": True,
            "home_city": serialize_home_city(home_city),
            "favorite_styles": display_styles,
            "spotlight_title": "为你定制的景点推荐",
            "spotlight_description": (
                f"结合常住城市 {home_city.name}、偏好风格 {style_text} 与社区互动行为，"
                "通过 TOPSIS 多指标评分做了优先排序。"
            ),
            "city_title": "更贴近你的城市灵感",
            "city_description": f"优先考虑 {home_city.province or home_city.name} 周边与符合你风格的城市内容。",
            "model_name": model_name,
            "profile_summary": {
                "top_styles": display_styles[:3],
                "evidence": recommendation_profile.evidence,
                "activity_summary": recommendation_profile.activity_summary,
            },
        }

    return {
        "is_personalized": True,
        "home_city": None,
        "favorite_styles": display_styles,
        "spotlight_title": "按你的偏好推荐景点",
        "spotlight_description": f"根据画像提取出的 {style_text} 偏好，并通过 TOPSIS 做了首页景点排序。",
        "city_title": "按风格筛过的城市推荐",
        "city_description": "城市和景点都会优先匹配你在个人主页里选择的旅行风格。",
        "model_name": model_name,
        "profile_summary": {
            "top_styles": display_styles[:3],
            "evidence": recommendation_profile.evidence,
            "activity_summary": recommendation_profile.activity_summary,
        },
    }


def pick_featured_cities(home_city: TravelCity | None, favorite_styles: list[str]) -> list[TravelCity]:
    if not home_city and not favorite_styles:
        return list(TravelCity.objects.order_by("-is_featured", "-average_rating", "-attraction_count")[:8])

    ranked = []
    for city in TravelCity.objects.all():
        score, matched_styles = score_city(city, home_city, favorite_styles)
        city.personalized_score = score
        city.matched_styles = matched_styles
        ranked.append(city)

    ranked.sort(
        key=lambda item: (
            getattr(item, "personalized_score", 0),
            float(item.average_rating or 0),
            item.attraction_count or 0,
        ),
        reverse=True,
    )
    return ranked[:8]


def pick_default_spotlight_attractions(limit: int = 8) -> list[Attraction]:
    return list(Attraction.objects.select_related("city").order_by("-rating", "name")[:limit])


def pick_spotlight_attractions(user=None, *, limit: int = 8) -> dict:
    bundle = build_attraction_recommendation_bundle(user, limit=limit)
    attractions = [row["attraction"] for row in bundle["results"]]
    return {
        "bundle": bundle,
        "attractions": attractions or pick_default_spotlight_attractions(limit),
    }


def pick_latest_posts() -> list[TravelPost]:
    return list(
        TravelPost.objects.select_related("author", "author__profile", "city", "attraction")
        .annotate(comment_count=Count("comments", distinct=True), favorite_count=Count("favorites", distinct=True))
        .filter(status=TravelPost.STATUS_PUBLISHED)
        .order_by("-created_at")[:6]
    )


def build_default_home_spotlight(limit: int = 8) -> dict:
    profile = UserPreferenceProfile(activity_summary={})
    attractions = pick_default_spotlight_attractions(limit)
    return {
        "bundle": {
            "profile": profile,
            "model": {
                "name": "default_home_fallback_v1",
                "algorithm": "rating_heat_fallback",
                "criteria": [],
                "candidate_count": len(attractions),
            },
        },
        "attractions": attractions,
    }


def build_story_sections(home_city: TravelCity | None, favorite_styles: list[str]) -> list[dict]:
    base_sections = [
        {
            "title": "城市推荐",
            "description": "从省份、标签和城市亮点切入，快速找到适合展开行程的目的地。",
        },
        {
            "title": "景点资料库",
            "description": "每个景点都保留地址、票务、开放时间、图片和玩法建议。",
        },
        {
            "title": "AI 行程规划",
            "description": "把城市和景点直接串成逐日安排，减少从搜集到规划的切换成本。",
        },
        {
            "title": "旅行社区",
            "description": "帖子支持点赞、收藏、评论，方便沉淀真实体验和路线参考。",
        },
    ]

    if not home_city and not favorite_styles:
        return base_sections

    if home_city:
        base_sections[0]["description"] = f"已优先结合 {home_city.name} 周边和你的个人偏好排序。"
    if favorite_styles:
        popular_style = Counter(favorite_styles).most_common(1)[0][0]
        base_sections[1]["description"] = f"首页会优先推荐更贴近“{popular_style}”风格的景点内容。"
    return base_sections


def build_home_payload(user=None, *, recommendation_mode: str = "default") -> dict:
    mode = "personalized" if recommendation_mode == "personalized" and user and user.is_authenticated else "default"
    spotlight = pick_spotlight_attractions(user, limit=8) if mode == "personalized" else build_default_home_spotlight(limit=8)
    recommendation_profile = spotlight["bundle"]["profile"]
    home_city = recommendation_profile.home_city if mode == "personalized" else None
    favorite_styles = (recommendation_profile.explicit_styles or recommendation_profile.top_styles) if mode == "personalized" else []
    recommendation = build_recommendation_copy(recommendation_profile, MODEL_NAME)
    recommendation["request_mode"] = mode
    recommendation["can_personalize"] = bool(user and user.is_authenticated)
    recommendation["is_default_stage"] = mode == "default"
    if mode == "default":
        recommendation["spotlight_description"] = "先展示默认热门景点推荐，个性化结果将在后台补充。"
        recommendation["city_description"] = "先按城市热度、景点密度和基础评分展示默认城市入口。"
    latest_posts = pick_latest_posts()
    stats = build_home_stats()
    stats["latestPostCount"] = len(latest_posts)
    featured_cities = pick_featured_cities(home_city, favorite_styles) or pick_featured_cities(None, [])

    return {
        "hero": {
            "eyebrow": "China Travel Studio",
            "title": "围绕中国城市、景点与旅行内容建立的智能旅游平台",
            "subtitle": "把景点资料、AI 行程、社区帖子和个人收藏放在一套连续的浏览体验里。",
        },
        "stats": stats,
        "province_cards": build_home_province_cards(limit=12),
        "recommendation": recommendation,
        "featured_cities": featured_cities,
        "spotlight_attractions": spotlight["attractions"],
        "spotlight_model": spotlight["bundle"]["model"],
        "spotlight_profile": serialize_profile(recommendation_profile),
        "latest_posts": latest_posts,
        "story_sections": build_story_sections(home_city, favorite_styles),
    }
