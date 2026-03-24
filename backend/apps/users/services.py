from __future__ import annotations

from django.contrib.auth import get_user_model

from apps.destinations.models import TravelCity
from apps.users.models import UserProfile


User = get_user_model()
MISSING = object()


def serialize_home_city(city: TravelCity | None) -> dict | None:
    if not city:
        return None
    return {
        "id": city.id,
        "name": city.name,
        "province": city.province,
        "cover_image": city.cover_image,
        "recommended_days": city.recommended_days,
        "attraction_count": city.attraction_count,
        "tags": city.tags,
    }


def assign_home_city(
    profile: UserProfile,
    *,
    home_city_name=MISSING,
    home_city_ref=MISSING,
) -> UserProfile:
    if home_city_ref is not MISSING:
        profile.home_city_ref = home_city_ref
        profile.home_city = home_city_ref.name if home_city_ref else ""
        return profile

    if home_city_name is not MISSING:
        normalized_name = str(home_city_name or "").strip()
        matched_city = TravelCity.objects.filter(name=normalized_name).first() if normalized_name else None
        profile.home_city_ref = matched_city
        profile.home_city = matched_city.name if matched_city else normalized_name
    return profile


def ensure_user_profile(user: User) -> UserProfile:
    profile, created = UserProfile.objects.get_or_create(user=user, defaults={"nickname": user.username})
    if created:
        return profile

    if profile.home_city and not profile.home_city_ref_id:
        matched_city = TravelCity.objects.filter(name=profile.home_city).first()
        if matched_city:
            profile.home_city_ref = matched_city
            profile.home_city = matched_city.name
            profile.save(update_fields=["home_city_ref", "home_city", "updated_at"])
    return profile


def serialize_user(user: User) -> dict:
    profile = getattr(user, "profile", None) or ensure_user_profile(user)
    home_city = profile.home_city_ref
    return {
        "id": user.id,
        "username": user.username,
        "nickname": profile.nickname or user.username,
        "avatar_url": profile.avatar_url,
        "bio": profile.bio,
        "home_city": home_city.name if home_city else profile.home_city,
        "home_city_id": home_city.id if home_city else None,
        "home_city_detail": serialize_home_city(home_city),
        "favorite_styles": profile.favorite_styles or [],
        "is_staff": user.is_staff,
    }
