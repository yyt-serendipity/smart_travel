from __future__ import annotations

import json
import re
from collections.abc import Iterable

import requests

from apps.destinations.models import TravelCity
from apps.destinations.services import clean_text
from apps.planner.services import extract_json_payload, get_llm_settings


PROFILE_FIELDS = ("short_intro", "overview", "travel_highlights", "travel_tips")
SHORT_INTRO_MAX_LENGTH = 110
OVERVIEW_MAX_LENGTH = 280
HIGHLIGHTS_MAX_LENGTH = 180
TIPS_MAX_LENGTH = 220
DEFAULT_TAG_TEXT = "\u57ce\u5e02\u6f2b\u6e38"
DEFAULT_SCENIC_TEXT = "\u4ee3\u8868\u666f\u70b9"
DEFAULT_LOCAL_TEXT = "\u5f53\u5730"
DEFAULT_SEASON_TEXT = "\u56db\u5b63"
SEPARATOR_TEXT = "\u3001"
SEMICOLON_TEXT = "\uff1b"
PUNCTUATION_PATTERN = r"[\uFF0C,\u3001/\uFF1B;|]+"
TRIM_PUNCTUATION = "\uFF1B;\uFF0C,\u3001\u3002. "

SYSTEM_PROMPT = """
You write concise city-detail copy for a Chinese travel product.
Return valid JSON only.
All content must be in Simplified Chinese.
Focus on city-level travel identity, atmosphere, route ideas, and practical advice.
Do not turn the overview into a description of a single attraction.
Do not invent named attractions that are not in the provided list.
Avoid markdown, numbering, bullets, and titles.
For each city:
- short_intro: one sentence, 24-60 Chinese characters.
- overview: one paragraph, 90-180 Chinese characters.
- travel_highlights: one paragraph with 3-4 clauses separated by Chinese semicolons.
- travel_tips: one paragraph with 3-4 clauses separated by Chinese semicolons.
""".strip()


class CityProfileGenerationError(RuntimeError):
    pass


def chunked(items: list[TravelCity], size: int) -> Iterable[list[TravelCity]]:
    if size <= 0:
        raise ValueError("size must be a positive integer")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def needs_profile_refresh(city: TravelCity) -> bool:
    attractions = list(city.attractions.all())
    attraction_names = [item.name for item in attractions[:3]]

    overview = normalize_profile_text(city.overview, OVERVIEW_MAX_LENGTH)
    highlights = normalize_profile_text(city.travel_highlights, HIGHLIGHTS_MAX_LENGTH)
    tips = normalize_profile_text(city.travel_tips, TIPS_MAX_LENGTH)
    short_intro = normalize_profile_text(city.short_intro, SHORT_INTRO_MAX_LENGTH)

    if not short_intro or len(short_intro) < 16:
        return True
    if not overview or len(overview) < 60:
        return True
    if not highlights or len(highlights) < 24:
        return True
    if not tips or len(tips) < 24:
        return True
    if looks_like_tag_list(highlights):
        return True
    if any(overview.startswith(name) for name in attraction_names):
        return True
    return False


def looks_like_tag_list(text: str) -> bool:
    tokens = [item.strip() for item in re.split(PUNCTUATION_PATTERN, clean_text(text)) if item.strip()]
    if not tokens or len(tokens) > 6:
        return False
    return all(len(token) <= 8 for token in tokens)


def normalize_profile_text(value: str, max_length: int) -> str:
    text = re.sub(r"\s+", " ", clean_text(value))
    text = text.strip(TRIM_PUNCTUATION)
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip(TRIM_PUNCTUATION)


def build_city_context(city: TravelCity) -> dict:
    attractions = list(city.attractions.all())[:6]
    attraction_context = []
    for attraction in attractions:
        attraction_context.append(
            {
                "name": attraction.name,
                "tags": (attraction.tags or [])[:3],
                "description": normalize_profile_text(attraction.description, 80),
                "tips": normalize_profile_text(attraction.tips, 50),
                "suggested_play_time": clean_text(attraction.suggested_play_time),
                "best_season": clean_text(attraction.best_season),
                "rating": float(attraction.rating) if attraction.rating is not None else None,
            }
        )

    return {
        "city_id": city.id,
        "name": city.name,
        "province": clean_text(city.province),
        "destination_type": clean_text(city.destination_type),
        "tags": (city.tags or [])[:5],
        "best_season": clean_text(city.best_season),
        "recommended_days": city.recommended_days,
        "average_rating": float(city.average_rating) if city.average_rating is not None else None,
        "attraction_count": city.attraction_count,
        "sample_attractions": attraction_context,
    }


def build_prompt(cities: list[TravelCity]) -> dict:
    return {
        "task": "Generate city-detail copy for the left panel of a city detail page.",
        "requirements": {
            "tone": "informative, specific, and practical",
            "forbidden": [
                "describing only one attraction as the whole city",
                "copying attraction introductions directly",
                "inventing unprovided named attractions",
                "generic filler sentences",
            ],
        },
        "cities": [build_city_context(city) for city in cities],
        "response_schema": {
            "profiles": [
                {
                    "city_id": "number",
                    "name": "string",
                    "short_intro": "string",
                    "overview": "string",
                    "travel_highlights": "string",
                    "travel_tips": "string",
                }
            ]
        },
    }


def parse_message_content(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise CityProfileGenerationError("LLM response did not contain any choices.")

    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        fragments = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                fragments.append(str(item.get("text", "")))
        return "\n".join(fragment for fragment in fragments if fragment)

    return str(content or "")


def coerce_profiles(raw_payload: dict, cities: list[TravelCity]) -> dict[int, dict[str, str]]:
    if isinstance(raw_payload, list):
        raw_profiles = raw_payload
    elif isinstance(raw_payload, dict):
        raw_profiles = raw_payload.get("profiles") or raw_payload.get("cities") or raw_payload.get("items") or []
    else:
        raise CityProfileGenerationError("LLM response JSON did not contain a usable profiles payload.")

    if not isinstance(raw_profiles, list):
        raise CityProfileGenerationError("LLM response JSON did not contain a profiles list.")

    city_by_id = {city.id: city for city in cities}
    city_by_name = {city.name: city for city in cities}
    profiles: dict[int, dict[str, str]] = {}

    for raw_profile in raw_profiles:
        if not isinstance(raw_profile, dict):
            continue

        city = None
        raw_city_id = raw_profile.get("city_id")
        if isinstance(raw_city_id, int) and raw_city_id in city_by_id:
            city = city_by_id[raw_city_id]
        elif isinstance(raw_city_id, str) and raw_city_id.isdigit() and int(raw_city_id) in city_by_id:
            city = city_by_id[int(raw_city_id)]

        if city is None:
            city = city_by_name.get(clean_text(raw_profile.get("name")))
        if city is None:
            continue

        profile = {}
        for field_name, max_length in (
            ("short_intro", SHORT_INTRO_MAX_LENGTH),
            ("overview", OVERVIEW_MAX_LENGTH),
            ("travel_highlights", HIGHLIGHTS_MAX_LENGTH),
            ("travel_tips", TIPS_MAX_LENGTH),
        ):
            profile[field_name] = normalize_profile_text(raw_profile.get(field_name, ""), max_length)

        if not all(profile.values()):
            continue
        profiles[city.id] = profile

    return profiles


def build_fallback_profile(city: TravelCity) -> dict[str, str]:
    attractions = [item.name for item in list(city.attractions.all())[:4]]
    tags = SEPARATOR_TEXT.join((city.tags or [])[:3]) or DEFAULT_TAG_TEXT
    scenic_names = SEPARATOR_TEXT.join(attractions[:3]) or f"{city.name}{DEFAULT_SCENIC_TEXT}"
    province_text = clean_text(city.province) or DEFAULT_LOCAL_TEXT
    season_text = clean_text(city.best_season) or DEFAULT_SEASON_TEXT
    days_text = max(city.recommended_days, 1)

    return {
        "short_intro": normalize_profile_text(
            (
                f"{city.name}\u9002\u5408\u5b89\u6392{days_text}\u5929\uff0c"
                f"\u56f4\u7ed5{tags}\u5c55\u5f00\u4e00\u6bb5\u8282\u594f\u8212\u5c55\u7684\u5728\u5730\u65c5\u884c\u3002"
            ),
            SHORT_INTRO_MAX_LENGTH,
        ),
        "overview": normalize_profile_text(
            (
                f"{city.name}\u4f4d\u4e8e{province_text}\uff0c\u884c\u7a0b\u53ef\u4ee5\u56f4\u7ed5"
                f"{scenic_names}\u7b49\u4ee3\u8868\u6027\u666f\u70b9\u5c55\u5f00\uff0c"
                "\u65e2\u80fd\u611f\u53d7\u57ce\u5e02\u98ce\u8c8c\uff0c\u4e5f\u9002\u5408\u6309\u4e3b\u9898\u4e32\u8054"
                "\u81ea\u7136\u3001\u4eba\u6587\u6216\u4f11\u95f2\u4f53\u9a8c\uff0c\u6574\u4f53\u66f4\u9002\u5408"
                "\u6162\u6162\u8d70\u3001\u5206\u533a\u73a9\u3002"
            ),
            OVERVIEW_MAX_LENGTH,
        ),
        "travel_highlights": normalize_profile_text(
            (
                f"\u53ef\u56f4\u7ed5{scenic_names}\u5b89\u6392\u4e3b\u7ebf{SEMICOLON_TEXT}"
                "\u9002\u5408\u628a\u5730\u6807\u666f\u70b9\u548c\u8857\u533a\u6162\u901b\u7a7f\u63d2\u8d77\u6765"
                f"{SEMICOLON_TEXT}\u5982\u679c\u65f6\u95f4\u5145\u88d5\uff0c\u5efa\u8bae\u7559\u51fa\u534a\u5929"
                "\u7ed9\u62cd\u7167\u3001\u770b\u591c\u666f\u6216\u4f53\u9a8c\u672c\u5730\u751f\u6d3b\u3002"
            ),
            HIGHLIGHTS_MAX_LENGTH,
        ),
        "travel_tips": normalize_profile_text(
            (
                f"\u5efa\u8bae\u4f18\u5148\u5728{season_text}\u51fa\u884c{SEMICOLON_TEXT}"
                "\u70ed\u95e8\u666f\u70b9\u5c3d\u91cf\u63d0\u524d\u786e\u8ba4\u5f00\u653e\u65f6\u95f4\u548c\u9884\u7ea6\u8981\u6c42"
                f"{SEMICOLON_TEXT}\u57ce\u5e02\u5185\u8de8\u533a\u5b89\u6392\u4e0d\u8981\u8fc7\u6ee1\uff0c"
                "\u6bcf\u5929\u4fdd\u7559\u673a\u52a8\u65f6\u95f4\u66f4\u7a33\u59a5\u3002"
            ),
            TIPS_MAX_LENGTH,
        ),
    }


def generate_city_profiles(cities: list[TravelCity], *, timeout: int | None = None) -> dict[int, dict[str, str]]:
    if not cities:
        return {}

    settings = get_llm_settings()
    if not settings:
        raise CityProfileGenerationError("LLM settings are not configured.")

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
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(build_prompt(cities), ensure_ascii=False)},
            ],
        },
        timeout=timeout or settings["timeout"],
    )
    response.raise_for_status()

    content = parse_message_content(response.json())
    parsed = extract_json_payload(content)
    if not parsed:
        raise CityProfileGenerationError("Failed to parse a valid JSON payload from the LLM response.")

    profiles = coerce_profiles(parsed, cities)
    if not profiles:
        raise CityProfileGenerationError("The LLM response did not contain any valid city profiles.")

    return profiles
