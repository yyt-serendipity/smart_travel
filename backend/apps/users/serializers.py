from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.core.tagging import normalize_profile_styles
from apps.destinations.models import TravelCity
from apps.users.models import UserProfile
from apps.users.services import assign_home_city, ensure_user_profile, serialize_home_city, serialize_user


User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在。")
        return value

    def create(self, validated_data):
        nickname = validated_data.pop("nickname", "")
        user = User.objects.create_user(**validated_data)
        profile = ensure_user_profile(user)
        if nickname:
            profile.nickname = nickname
            profile.save(update_fields=["nickname", "updated_at"])
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    home_city_id = serializers.PrimaryKeyRelatedField(
        source="home_city_ref",
        queryset=TravelCity.objects.all(),
        required=False,
        allow_null=True,
    )
    home_city_detail = serializers.SerializerMethodField()
    favorite_styles = serializers.ListField(child=serializers.CharField(max_length=32), required=False)

    class Meta:
        model = UserProfile
        fields = (
            "user",
            "nickname",
            "avatar_url",
            "bio",
            "home_city",
            "home_city_id",
            "home_city_detail",
            "favorite_styles",
        )

    def get_user(self, obj):
        return serialize_user(obj.user)

    def get_home_city_detail(self, obj):
        return serialize_home_city(obj.home_city_ref)

    def validate_favorite_styles(self, value):
        return normalize_profile_styles(value)

    def update(self, instance, validated_data):
        favorite_styles = validated_data.pop("favorite_styles", None)
        home_city_ref = validated_data.pop("home_city_ref", serializers.empty)
        home_city_name = validated_data.get("home_city", serializers.empty)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if home_city_ref is not serializers.empty:
            assign_home_city(instance, home_city_ref=home_city_ref)
        elif home_city_name is not serializers.empty:
            assign_home_city(instance, home_city_name=home_city_name)

        if favorite_styles is not None:
            instance.favorite_styles = favorite_styles

        instance.save()
        return instance
