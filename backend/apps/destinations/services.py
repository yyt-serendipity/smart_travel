from __future__ import annotations

import ast
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

from apps.community.models import TravelPost
from apps.core.tagging import normalize_public_tags
from apps.destinations.models import Attraction, TravelCity


CITY_TAG_RULES = {
    "自然风光": ["山", "湖", "海", "湾", "岛", "峡", "谷", "瀑布", "冰川", "草原", "森林", "雪", "河", "湿地"],
    "人文古迹": ["古城", "古镇", "博物馆", "故居", "寺", "庙", "遗址", "街", "书院", "塔", "院"],
    "亲子休闲": ["乐园", "动物园", "海洋馆", "熊猫", "温泉", "公园"],
    "户外体验": ["徒步", "漂流", "冲浪", "骑行", "潜水", "登山", "滑雪", "露营"],
    "摄影观景": ["日出", "日落", "观景", "夜景", "灯塔", "花海"],
    "民族文化": ["藏", "羌", "苗", "彝", "傣", "侗", "土司", "民俗", "风情"],
}

PROVINCE_PATTERNS = [
    "北京市",
    "上海市",
    "天津市",
    "重庆市",
    "香港特别行政区",
    "澳门特别行政区",
    "内蒙古自治区",
    "广西壮族自治区",
    "西藏自治区",
    "宁夏回族自治区",
    "新疆维吾尔自治区",
    "海南省",
    "四川省",
    "广东省",
    "浙江省",
    "江苏省",
    "福建省",
    "山东省",
    "云南省",
    "贵州省",
    "陕西省",
    "河南省",
    "河北省",
    "湖北省",
    "湖南省",
    "江西省",
    "山西省",
    "辽宁省",
    "吉林省",
    "黑龙江省",
    "安徽省",
    "甘肃省",
    "青海省",
]


def safe_decimal(value: str | float | int | None) -> Decimal | None:
    if value in (None, "", "--"):
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.1"))
    except Exception:
        return None


def clean_text(value) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def compact_text(value, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", clean_text(value))
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def fit_text(value, max_length: int) -> str:
    return clean_text(value)[:max_length]


def parse_ticket_data(value) -> str:
    text = clean_text(value)
    if not text:
        return ""
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, dict):
            lines = []
            for key, val in list(parsed.items())[:5]:
                price = ", ".join(str(item).replace("\xa5", "RMB ") for item in val)
                lines.append(f"{clean_text(key)} {price}".strip())
            return "\n".join(lines)
    except Exception:
        pass
    return text.replace("\xa5", "RMB ")


def infer_tags(*texts: str) -> list[str]:
    merged = " ".join(clean_text(item) for item in texts)
    tags = []
    for tag, keywords in CITY_TAG_RULES.items():
        if any(keyword in merged for keyword in keywords):
            tags.append(tag)
    return tags or ["城市漫游"]


def infer_province(*texts: str) -> str:
    merged = " ".join(clean_text(item) for item in texts)
    for item in PROVINCE_PATTERNS:
        if item in merged:
            return item
    for pattern in [r"([\u4e00-\u9fa5]{2,8}省)", r"([\u4e00-\u9fa5]{2,8}市)", r"([\u4e00-\u9fa5]{2,12}自治区)"]:
        match = re.search(pattern, merged)
        if match:
            return match.group(1)
    return ""


def infer_destination_type(name: str) -> str:
    scenic_keywords = ["山", "湾", "湖", "沟", "海", "岛", "谷", "岭", "景区", "半岛"]
    region_keywords = ["州", "盟", "新区", "地区"]
    if any(name.endswith(keyword) or keyword in name for keyword in scenic_keywords):
        return "scenic"
    if any(name.endswith(keyword) or keyword in name for keyword in region_keywords):
        return "region"
    return "city"


def compute_city_profile(city: TravelCity) -> TravelCity:
    attractions = list(city.attractions.all())
    city.attraction_count = len(attractions)

    ratings = [float(item.rating) for item in attractions if item.rating is not None]
    city.average_rating = Decimal(str(round(sum(ratings) / len(ratings), 1))) if ratings else None

    season_candidates = [item.best_season.strip() for item in attractions if clean_text(item.best_season)]
    city.best_season = fit_text(Counter(season_candidates).most_common(1)[0][0] if season_candidates else "", 200)
    city.cover_image = fit_text(
        next((item.image_url for item in attractions if clean_text(item.image_url)), city.cover_image),
        200,
    )
    city.average_ticket = fit_text(
        next((item.ticket_info for item in attractions if clean_text(item.ticket_info)), city.average_ticket),
        255,
    )

    tag_pool = []
    for item in attractions:
        tag_pool.extend(item.tags)
    city.tags = normalize_public_tags([name for name, _ in Counter(tag_pool).most_common(5)]) or normalize_public_tags(
        infer_tags(city.name, city.overview)
    )
    city.recommended_days = max(2, min(6, (len(attractions) // 7) + 1))

    top_names = "、".join(item.name for item in attractions[:4])
    city.short_intro = city.short_intro or compact_text(
        f"{city.name}适合安排 {city.recommended_days} 天游玩，热门景点包括 {top_names}。", 220
    )
    city.overview = city.overview or f"{city.name}拥有 {city.attraction_count} 个可展示景点，适合围绕 {', '.join(city.tags[:3])} 展开旅行。"
    city.travel_highlights = city.travel_highlights or "、".join(city.tags[:4])
    city.travel_tips = city.travel_tips or next((item.tips for item in attractions if clean_text(item.tips)), "")
    city.is_featured = city.is_featured or (
        city.attraction_count >= 15 and bool(city.average_rating and city.average_rating >= Decimal("4.5"))
    )
    return city


def build_home_payload() -> dict:
    featured_cities = list(TravelCity.objects.order_by("-is_featured", "-average_rating")[:8])
    spotlight_attractions = list(Attraction.objects.select_related("city").order_by("-rating")[:8])
    latest_posts = list(TravelPost.objects.select_related("author", "city", "attraction").filter(status="published")[:6])

    return {
        "hero": {
            "eyebrow": "China Travel Studio",
            "title": "只围绕中国城市与景点的智能旅游平台",
            "subtitle": "把真实景点资料、AI 行程、游记社区和后台管理放进一套更清晰的学生项目结构里。",
        },
        "featured_cities": featured_cities,
        "spotlight_attractions": spotlight_attractions,
        "latest_posts": latest_posts,
        "story_sections": [
            {
                "title": "城市推荐",
                "description": "先按省份、关键词和标签找到适合出发的中国城市。",
            },
            {
                "title": "景点资料库",
                "description": "每个景点都有地址、门票、开放时间、游玩建议和图片。",
            },
            {
                "title": "景点级 AI 行程",
                "description": "AI 规划直接细化到景点和一天内的时段安排。",
            },
            {
                "title": "旅游社区",
                "description": "支持围绕城市和景点发帖、点赞、评论，像信息流一样浏览。",
            },
        ],
    }


def default_excel_directory() -> Path:
    return Path(r"C:/Users/YT-yuntian/Desktop/cities_data_excel")
