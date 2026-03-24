from __future__ import annotations

import json
import os
import re
from decimal import Decimal

import requests
from django.db.models import Q

from apps.destinations.models import Attraction, TravelCity
from apps.destinations.services import clean_text, compact_text


INTEREST_CITY_WEIGHTS = {
    "自然风光": {"自然风光": 26, "摄影观景": 12, "户外体验": 10},
    "人文古迹": {"人文古迹": 24, "民族文化": 14},
    "亲子休闲": {"亲子休闲": 24, "自然风光": 8},
    "户外徒步": {"户外体验": 24, "自然风光": 14},
    "摄影": {"摄影观景": 24, "自然风光": 10, "民族文化": 8},
    "美食": {"人文古迹": 10, "民族文化": 10},
}

BUDGET_LEVEL_TO_PRICE = {
    "value": 1800,
    "balanced": 3200,
    "premium": 5200,
}

INTEREST_KEYWORDS = {
    "自然风光": ["山", "海", "湖", "岛", "谷", "瀑布", "森林", "雪", "湿地"],
    "人文古迹": ["古城", "古镇", "博物馆", "遗址", "寺", "庙", "祠", "故居"],
    "亲子休闲": ["乐园", "动物园", "熊猫", "公园", "海洋馆"],
    "户外徒步": ["徒步", "登山", "露营", "漂流", "骑行", "步道"],
    "摄影": ["观景", "夜景", "日出", "日落", "花海", "灯塔"],
    "美食": ["老街", "夜市", "小吃", "市集", "风情"],
}

DEFAULT_CHECKLIST = [
    "提前确认门票与开放时间",
    "准备舒适步行鞋和充电设备",
    "夜间活动尽量安排在住宿点附近",
]

DEFAULT_BLOCK_SUMMARY = {
    "上午": "建议早点出发，把核心景点放在上午，尽量避开高峰排队。",
    "下午": "下午安排体验类或步行类景点，让节奏更从容。",
    "晚上": "晚上留给夜景、老街或轻量活动，避免过度奔波。",
}

DEFAULT_PERIODS = ["上午", "下午", "晚上"]


class PlannerGenerationError(Exception):
    def __init__(self, message: str, stage: str = "planner") -> None:
        super().__init__(message)
        self.message = message
        self.stage = stage


def explain_request_exception(exc: requests.RequestException) -> str:
    if isinstance(exc, requests.Timeout):
        return "大模型响应超时，请稍后重试。"
    if isinstance(exc, requests.ConnectionError):
        return "无法连接大模型服务，请检查网络或接口配置。"

    response = getattr(exc, "response", None)
    if response is not None:
        detail = ""
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            error_data = payload.get("error")
            if isinstance(error_data, dict):
                detail = clean_text(
                    error_data.get("message")
                    or error_data.get("code")
                    or error_data.get("type")
                    or ""
                )
            elif error_data:
                detail = clean_text(str(error_data))
            detail = detail or clean_text(payload.get("message") or payload.get("detail") or "")

        detail = detail or compact_text(clean_text(getattr(response, "text", "")), 120)
        if detail:
            return f"大模型接口调用失败（HTTP {response.status_code}）：{detail}"
        return f"大模型接口调用失败（HTTP {response.status_code}）。"

    raw_message = clean_text(str(exc))
    if raw_message:
        return f"大模型请求失败：{raw_message}"
    return "大模型请求失败，请稍后重试。"


def build_failed_plan(
    message: str,
    *,
    stage: str,
    city: TravelCity | None = None,
    recommended_cities: list[TravelCity] | None = None,
    matched_city_name: str = "",
    fallback_reason: str = "",
) -> dict:
    return {
        "success": False,
        "failure_reason": message,
        "failure_stage": stage,
        "fallback_reason": fallback_reason,
        "trip_title": "鏆傛棤鍙敤琛岀▼",
        "summary": message,
        "estimated_budget": 0,
        "budget_breakdown": {},
        "city": city,
        "recommended_cities": recommended_cities or [],
        "must_visit_spots": [],
        "packing_list": [],
        "itinerary": [],
        "planner_mode": "failed",
        "planner_provider": "rule",
        "planner_model": "",
        "matched_city_name": matched_city_name,
        "used_fallback": False,
    }


def build_city_recommendations(interests: list[str], budget_level: str, season_hint: str, limit: int = 6) -> list[TravelCity]:
    cities = list(TravelCity.objects.all())
    ranked: list[tuple[int, TravelCity]] = []
    budget_target = BUDGET_LEVEL_TO_PRICE.get(budget_level, 3200)

    for city in cities:
        score = 0
        city_tags = city.tags or []

        for interest in interests:
            weights = INTEREST_CITY_WEIGHTS.get(interest, {})
            for tag, weight in weights.items():
                if tag in city_tags:
                    score += weight

        if season_hint and season_hint in clean_text(city.best_season):
            score += 12
        if city.recommended_days <= 4:
            score += 6
        if city.average_rating:
            score += int(float(city.average_rating) * 10)
        if city.average_ticket:
            if "免费" in clean_text(city.average_ticket):
                score += 8
            numbers = [int(item) for item in re.findall(r"(\d+)", city.average_ticket)]
            if numbers and min(numbers) <= budget_target:
                score += 6

        ranked.append((score, city))

    ranked.sort(key=lambda item: (item[0], item[1].average_rating or Decimal("0.0")), reverse=True)
    return [city for _, city in ranked[:limit]]


def attraction_match_score(attraction: Attraction, interests: list[str]) -> int:
    score = 0
    text = " ".join(
        [
            attraction.name,
            attraction.description,
            attraction.address,
            attraction.opening_hours,
            " ".join(attraction.tags or []),
        ]
    )
    for interest in interests:
        for keyword in INTEREST_KEYWORDS.get(interest, []):
            if keyword in text:
                score += 8
    if attraction.rating:
        score += int(float(attraction.rating) * 5)
    if "免费" in clean_text(attraction.ticket_info):
        score += 3
    return score


def serialize_spot_payload(spot: Attraction) -> dict:
    return {
        "id": spot.id,
        "name": spot.name,
        "image_url": spot.image_url,
        "address": compact_text(spot.address, 80),
        "opening_hours": compact_text(spot.opening_hours, 80),
        "ticket_info": compact_text(spot.ticket_info, 100),
        "suggested_play_time": spot.suggested_play_time,
        "rating": str(spot.rating) if spot.rating is not None else "",
    }


def build_day_block(period: str, spot: Attraction, summary: str = "") -> dict:
    return {
        "period": period,
        "spot": serialize_spot_payload(spot),
        "summary": clean_text(summary) or DEFAULT_BLOCK_SUMMARY[period],
    }


def build_day_blocks(day_spots: list[Attraction]) -> list[dict]:
    return [build_day_block(period, spot) for period, spot in zip(DEFAULT_PERIODS, day_spots)]


def build_plan_itinerary(city: TravelCity, interests: list[str], duration_days: int) -> list[dict]:
    attractions = list(city.attractions.all())
    ranked = sorted(attractions, key=lambda item: attraction_match_score(item, interests), reverse=True)
    if not ranked:
        return []

    per_day = 3
    max_spots = min(len(ranked), max(duration_days * per_day, duration_days))
    selected = ranked[:max_spots]

    itinerary = []
    for day in range(duration_days):
        start = day * per_day
        day_spots = selected[start : start + per_day]
        if not day_spots:
            day_spots = selected[: min(per_day, len(selected))]

        names = [item.name for item in day_spots]
        itinerary.append(
            {
                "day": day + 1,
                "theme": f"{city.name} 第 {day + 1} 天 · {' / '.join(names[:2])}",
                "summary": f"今天围绕 {'、'.join(names)} 展开，节奏按“核心景点优先，体验与休闲穿插”来安排。",
                "transport_tip": f"建议把 {names[0]} 作为当天核心锚点，其余景点按顺路原则串联，尽量减少折返。",
                "checklist": DEFAULT_CHECKLIST,
                "spots": [serialize_spot_payload(item) for item in day_spots],
                "blocks": build_day_blocks(day_spots),
            }
        )
    return itinerary


def estimate_plan_budget(city: TravelCity, duration_days: int, budget_level: str) -> int:
    base = BUDGET_LEVEL_TO_PRICE.get(budget_level, 3200)
    rating_factor = int((float(city.average_rating or Decimal("4.0")) - 3.5) * 400)
    return max(1200, base * duration_days // 2 + rating_factor)


def resolve_target_city(city_id=None, target_city: str = "") -> TravelCity | None:
    if city_id:
        try:
            return TravelCity.objects.get(id=city_id)
        except TravelCity.DoesNotExist:
            pass

    query = clean_text(target_city)
    if not query:
        return None

    exact_match = TravelCity.objects.filter(name=query).first()
    if exact_match:
        return exact_match

    return (
        TravelCity.objects.filter(
            Q(name__icontains=query)
            | Q(province__icontains=query)
            | Q(short_intro__icontains=query)
            | Q(overview__icontains=query)
        )
        .order_by("-is_featured", "-average_rating", "name")
        .first()
    )


def build_target_city_recommendations(city: TravelCity, limit: int = 4) -> list[TravelCity]:
    same_province = list(
        TravelCity.objects.filter(province=city.province)
        .exclude(id=city.id)
        .order_by("-is_featured", "-average_rating", "name")[: limit - 1]
    )
    if len(same_province) < limit - 1:
        extra = list(
            TravelCity.objects.exclude(id__in=[city.id, *(item.id for item in same_province)])
            .order_by("-is_featured", "-average_rating", "name")[: limit - 1 - len(same_province)]
        )
        same_province.extend(extra)
    return [city, *same_province][:limit]


def get_llm_settings() -> dict | None:
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or dashscope_api_key
    provider = (os.getenv("LLM_PROVIDER") or ("qwen" if dashscope_api_key else "openai")).lower()
    model = (
        os.getenv("LLM_API_MODEL")
        or os.getenv("OPENAI_MODEL")
        or os.getenv("DASHSCOPE_MODEL")
        or os.getenv("QWEN_MODEL")
        or ("qwen2.5-14b-instruct" if provider == "qwen" else "")
    )
    if not api_key or not model:
        return None

    default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1" if provider == "qwen" else "https://api.openai.com/v1"
    return {
        "api_key": api_key,
        "model": model,
        "provider": provider,
        "base_url": (
            os.getenv("LLM_API_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("DASHSCOPE_BASE_URL")
            or default_base_url
        ).rstrip("/"),
        "timeout": int(os.getenv("LLM_API_TIMEOUT", "25")),
    }


def extract_json_payload(content: str) -> dict | None:
    if not content:
        return None
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def resolve_spot_reference(raw_block: dict, attraction_pool: list[Attraction], fallback_index: int) -> Attraction | None:
    by_id = {str(item.id): item for item in attraction_pool}
    by_name = {item.name: item for item in attraction_pool}

    if raw_block.get("spot_id") is not None and str(raw_block.get("spot_id")) in by_id:
        return by_id[str(raw_block.get("spot_id"))]

    spot_name = clean_text(raw_block.get("spot_name") or raw_block.get("spot") or "")
    if spot_name in by_name:
        return by_name[spot_name]

    for item in attraction_pool:
        if spot_name and spot_name in item.name:
            return item

    if not attraction_pool:
        return None
    return attraction_pool[fallback_index % len(attraction_pool)]


def normalize_llm_itinerary(raw_data: dict, city: TravelCity, attraction_pool: list[Attraction], duration_days: int) -> list[dict]:
    raw_days = raw_data.get("itinerary") or raw_data.get("days") or []
    if not isinstance(raw_days, list):
        return []

    itinerary = []
    for day_index in range(duration_days):
        raw_day = raw_days[day_index] if day_index < len(raw_days) and isinstance(raw_days[day_index], dict) else {}
        raw_blocks = raw_day.get("blocks") or []
        blocks = []
        spots = []

        for block_index, period in enumerate(DEFAULT_PERIODS):
            raw_block = {}
            if isinstance(raw_blocks, list):
                raw_block = next(
                    (
                        item
                        for item in raw_blocks
                        if isinstance(item, dict) and clean_text(item.get("period")) == period
                    ),
                    raw_blocks[block_index] if block_index < len(raw_blocks) and isinstance(raw_blocks[block_index], dict) else {},
                )

            spot = resolve_spot_reference(raw_block, attraction_pool, day_index * len(DEFAULT_PERIODS) + block_index)
            if not spot:
                continue
            spots.append(serialize_spot_payload(spot))
            blocks.append(build_day_block(period, spot, raw_block.get("summary", "")))

        if not blocks:
            start = day_index * len(DEFAULT_PERIODS)
            fallback_spots = attraction_pool[start : start + len(DEFAULT_PERIODS)] or attraction_pool[: len(DEFAULT_PERIODS)]
            if not fallback_spots:
                continue
            blocks = build_day_blocks(fallback_spots)
            spots = [serialize_spot_payload(item) for item in fallback_spots]

        theme = clean_text(raw_day.get("theme")) or f"{city.name} 第 {day_index + 1} 天"
        summary = clean_text(raw_day.get("summary")) or f"围绕 {'、'.join(item['name'] for item in spots[:3])} 展开全天游览。"
        transport_tip = clean_text(raw_day.get("transport_tip")) or f"建议优先按顺路动线串联 {spots[0]['name']} 等景点。"
        checklist = [clean_text(item) for item in raw_day.get("checklist", []) if clean_text(item)]

        itinerary.append(
            {
                "day": day_index + 1,
                "theme": theme,
                "summary": summary,
                "transport_tip": transport_tip,
                "checklist": checklist[:5] or DEFAULT_CHECKLIST,
                "spots": spots,
                "blocks": blocks,
            }
        )

    return itinerary


def generate_itinerary_with_llm(city: TravelCity, interests: list[str], duration_days: int, payload: dict) -> dict | None:
    settings = get_llm_settings()
    if not settings:
        raise PlannerGenerationError("未配置可用的大模型参数，已切换为规则规划。", stage="llm_config")

    ranked_attractions = sorted(city.attractions.all(), key=lambda item: attraction_match_score(item, interests), reverse=True)
    attraction_pool = list(ranked_attractions[: max(10, duration_days * 4)])
    if not attraction_pool:
        raise PlannerGenerationError("当前城市缺少可供大模型编排的景点数据，已切换为规则规划。", stage="attraction_pool")

    attraction_context = [
        {
            "id": item.id,
            "name": item.name,
            "tags": item.tags[:3],
            "play_time": item.suggested_play_time,
            "ticket_info": compact_text(item.ticket_info, 60),
            "opening_hours": compact_text(item.opening_hours, 50),
        }
        for item in attraction_pool
    ]

    prompt = {
        "city": city.name,
        "province": city.province,
        "duration_days": duration_days,
        "departure_city": payload.get("departure_city", ""),
        "budget_level": payload.get("budget_level", "balanced"),
        "companions": payload.get("companions", ""),
        "season_hint": payload.get("season_hint", ""),
        "interests": interests,
        "available_attractions": attraction_context,
        "response_schema": {
            "trip_title": "string",
            "summary": "string",
            "packing_list": ["string"],
            "itinerary": [
                {
                    "day": "number",
                    "theme": "string",
                    "summary": "string",
                    "transport_tip": "string",
                    "checklist": ["string"],
                    "blocks": [
                        {"period": "上午", "spot_id": "number", "spot_name": "string", "summary": "string"},
                        {"period": "下午", "spot_id": "number", "spot_name": "string", "summary": "string"},
                        {"period": "晚上", "spot_id": "number", "spot_name": "string", "summary": "string"},
                    ],
                }
            ],
        },
    }

    response = requests.post(
        f"{settings['base_url']}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings["model"],
            "temperature": 0.35,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是中国旅行路线规划助手。"
                        "你只能从给定的景点列表中选择景点，必须输出合法 JSON，"
                        "不要输出任何额外解释。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt, ensure_ascii=False),
                },
            ],
        },
        timeout=settings["timeout"],
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    parsed = extract_json_payload(content)
    if not parsed:
        raise PlannerGenerationError("大模型返回内容无法解析为有效行程数据，已切换为规则规划。", stage="llm_parse")

    itinerary = normalize_llm_itinerary(parsed, city, attraction_pool, duration_days)
    if not itinerary:
        raise PlannerGenerationError("大模型返回的行程为空，已切换为规则规划。", stage="llm_itinerary")

    return {
        "trip_title": clean_text(parsed.get("trip_title")) or f"{city.name}{duration_days}天 AI 智能行程",
        "summary": clean_text(parsed.get("summary")) or f"已结合 {city.name} 的真实景点库生成更细化的行程建议。",
        "packing_list": [clean_text(item) for item in parsed.get("packing_list", []) if clean_text(item)][:6],
        "itinerary": itinerary,
        "planner_mode": "llm",
        "planner_provider": settings["provider"],
        "planner_model": settings["model"],
    }


def build_ai_plan(payload: dict) -> dict:
    interests = payload.get("interests", [])
    budget_level = payload.get("budget_level", "balanced")
    duration_days = int(payload.get("duration_days", 3))
    season_hint = payload.get("season_hint", "")
    target_city_id = payload.get("city_id")
    target_city_query = clean_text(payload.get("target_city", ""))

    city = resolve_target_city(target_city_id, target_city_query)
    if city:
        recommended_cities = build_target_city_recommendations(city)
    else:
        recommended_cities = build_city_recommendations(interests, budget_level, season_hint, limit=4)
        city = recommended_cities[0] if recommended_cities else TravelCity.objects.order_by("-average_rating").first()

    if city is None:
        return build_failed_plan(
            "当前没有可用于规划的城市数据，请先补充城市信息后重试。",
            stage="city_data",
        )

    llm_result = None
    fallback_reason = ""
    failure_stage = ""
    try:
        llm_result = generate_itinerary_with_llm(city, interests, duration_days, payload)
    except requests.RequestException as exc:
        fallback_reason = explain_request_exception(exc)
        failure_stage = "llm_request"
    except PlannerGenerationError as exc:
        fallback_reason = exc.message
        failure_stage = exc.stage
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        fallback_reason = "大模型返回格式异常，已切换为规则规划。"
        failure_stage = "llm_response"
    except Exception:
        fallback_reason = "规划引擎处理失败，已切换为规则规划。"
        failure_stage = "planner"

    itinerary = llm_result["itinerary"] if llm_result else build_plan_itinerary(city, interests, duration_days)
    if not itinerary:
        return build_failed_plan(
            "当前城市缺少可生成行程的景点数据，请稍后重试或更换城市。",
            stage="itinerary",
            city=city,
            recommended_cities=recommended_cities,
            matched_city_name=city.name,
            fallback_reason=fallback_reason,
        )

    budget = estimate_plan_budget(city, duration_days, budget_level)
    must_visit_spots = itinerary[0]["spots"][:3] if itinerary else []

    return {
        "success": True,
        "failure_reason": "",
        "failure_stage": failure_stage,
        "fallback_reason": fallback_reason,
        "trip_title": llm_result["trip_title"] if llm_result else f"{city.name}{duration_days}天 AI 旅行规划",
        "summary": llm_result["summary"]
        if llm_result
        else f"围绕 {city.name} 为你生成了 {duration_days} 天行程，兼顾 {', '.join(interests or city.tags[:2] or ['城市漫游'])} 等偏好。",
        "estimated_budget": budget,
        "budget_breakdown": {
            "transport": int(budget * 0.28),
            "tickets": int(budget * 0.22),
            "food": int(budget * 0.20),
            "stay": int(budget * 0.30),
        },
        "city": city,
        "recommended_cities": recommended_cities,
        "must_visit_spots": must_visit_spots,
        "packing_list": (llm_result or {}).get("packing_list")
        or [
            "身份证件",
            "舒适步行鞋",
            "常用充电设备",
        ],
        "itinerary": itinerary,
        "planner_mode": (llm_result or {}).get("planner_mode", "rule"),
        "planner_provider": (llm_result or {}).get("planner_provider", "rule"),
        "planner_model": (llm_result or {}).get("planner_model", ""),
        "matched_city_name": city.name,
        "used_fallback": bool(fallback_reason and not llm_result),
    }
