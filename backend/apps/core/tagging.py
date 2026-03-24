from __future__ import annotations

import re
from collections.abc import Iterable


PUBLIC_TAGS = (
    "自然风光",
    "人文古迹",
    "亲子休闲",
    "城市漫游",
    "民族文化",
    "摄影观景",
    "户外体验",
)

PROFILE_STYLE_OPTIONS = (
    "自然风光",
    "历史人文",
    "城市漫游",
    "周末度假",
    "亲子出游",
    "美食寻味",
    "摄影出片",
    "户外徒步",
)

PUBLIC_TAG_ALIASES = {
    "自然景观": "自然风光",
    "山水风光": "自然风光",
    "风景": "自然风光",
    "历史人文": "人文古迹",
    "历史文化": "人文古迹",
    "古迹": "人文古迹",
    "城市打卡": "城市漫游",
    "周末出游": "城市漫游",
    "周末游": "城市漫游",
    "城市漫步": "城市漫游",
    "亲子": "亲子休闲",
    "亲子出游": "亲子休闲",
    "民俗文化": "民族文化",
    "民族风情": "民族文化",
    "摄影": "摄影观景",
    "拍照": "摄影观景",
    "摄影打卡": "摄影观景",
    "户外徒步": "户外体验",
    "徒步": "户外体验",
}

PROFILE_STYLE_ALIASES = {
    "自然景观": "自然风光",
    "山水风光": "自然风光",
    "人文古迹": "历史人文",
    "历史文化": "历史人文",
    "古迹": "历史人文",
    "周末游": "周末度假",
    "周末出游": "周末度假",
    "亲子休闲": "亲子出游",
    "亲子": "亲子出游",
    "美食": "美食寻味",
    "摄影观景": "摄影出片",
    "摄影": "摄影出片",
    "拍照": "摄影出片",
    "户外体验": "户外徒步",
    "徒步": "户外徒步",
}


def _as_list(values) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (list, tuple, set)):
        return [str(item) for item in values]
    return [str(values)]


def _sanitize_token(value: str, *, max_length: int) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s+", "", text)
    text = text.strip("#")
    text = re.sub(r"[、，,。.;；:：/\\\\|]+", "", text)
    text = re.sub(r"[()（）\\[\\]【】<>《》“”\"'‘’]+", "", text)
    if not text:
        return ""
    if len(text) > max_length:
        return ""
    if re.search(r"(https?://|www\.)", text, flags=re.IGNORECASE):
        return ""
    return text


def _normalize_labels(
    values: Iterable[str] | str | None,
    *,
    allowed: tuple[str, ...],
    aliases: dict[str, str],
    max_items: int,
    max_length: int,
) -> list[str]:
    normalized = []
    seen = set()
    allowed_set = set(allowed)
    for raw in _as_list(values):
        token = _sanitize_token(raw, max_length=max_length)
        if not token:
            continue
        token = aliases.get(token, token)
        if token not in allowed_set or token in seen:
            continue
        normalized.append(token)
        seen.add(token)
        if len(normalized) >= max_items:
            break
    return normalized


def normalize_public_tags(values: Iterable[str] | str | None, max_items: int = 5) -> list[str]:
    return _normalize_labels(
        values,
        allowed=PUBLIC_TAGS,
        aliases=PUBLIC_TAG_ALIASES,
        max_items=max_items,
        max_length=8,
    )


def normalize_profile_styles(values: Iterable[str] | str | None, max_items: int = 8) -> list[str]:
    return _normalize_labels(
        values,
        allowed=PROFILE_STYLE_OPTIONS,
        aliases=PROFILE_STYLE_ALIASES,
        max_items=max_items,
        max_length=8,
    )
