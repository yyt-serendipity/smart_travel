from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.backoffice.models import OperationLog
from apps.community.models import TravelPost
from apps.destinations.models import TravelCity
from apps.core.tagging import normalize_profile_styles, normalize_public_tags
from apps.users.models import UserProfile
from apps.users.services import assign_home_city


User = get_user_model()


class TravelCityAdminSerializer(serializers.ModelSerializer):
    def validate_tags(self, value):
        return normalize_public_tags(value)

    class Meta:
        model = TravelCity
        fields = "__all__"


class TravelPostAdminSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    attraction_name = serializers.CharField(source="attraction.name", read_only=True)

    def validate_tags(self, value):
        return normalize_public_tags(value)

    class Meta:
        model = TravelPost
        fields = (
            "id",
            "author",
            "author_name",
            "city",
            "city_name",
            "attraction",
            "attraction_name",
            "title",
            "content",
            "cover_image",
            "tags",
            "likes_count",
            "views_count",
            "status",
            "created_at",
        )


class OperationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    nickname = serializers.SerializerMethodField()

    def get_nickname(self, obj):
        profile = getattr(obj.user, "profile", None)
        return getattr(profile, "nickname", "") if profile else ""

    class Meta:
        model = OperationLog
        fields = (
            "id",
            "category",
            "action",
            "status",
            "username",
            "nickname",
            "target_type",
            "target_id",
            "target_name",
            "request_path",
            "request_method",
            "ip_address",
            "detail",
            "created_at",
        )


class AdminUserSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(required=False, allow_blank=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True, max_length=500)
    bio = serializers.CharField(required=False, allow_blank=True)
    home_city = serializers.CharField(required=False, allow_blank=True)
    favorite_styles = serializers.ListField(child=serializers.CharField(), required=False)
    post_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    plan_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "is_staff",
            "is_active",
            "is_superuser",
            "date_joined",
            "last_login",
            "nickname",
            "avatar_url",
            "bio",
            "home_city",
            "favorite_styles",
            "post_count",
            "comment_count",
            "plan_count",
        )
        read_only_fields = ("is_superuser", "date_joined", "last_login", "post_count", "comment_count", "plan_count")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        profile = getattr(instance, "profile", None)
        data["nickname"] = getattr(profile, "nickname", "")
        data["avatar_url"] = getattr(profile, "avatar_url", "")
        data["bio"] = getattr(profile, "bio", "")
        data["home_city"] = getattr(profile, "home_city", "")
        data["favorite_styles"] = getattr(profile, "favorite_styles", []) or []
        return data

    def validate_favorite_styles(self, value):
        return normalize_profile_styles(value)

    def update(self, instance, validated_data):
        profile_fields = {}
        for key in ("nickname", "avatar_url", "bio", "home_city", "favorite_styles"):
            if key in validated_data:
                profile_fields[key] = validated_data.pop(key)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_fields:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_fields.items():
                if attr == "home_city":
                    assign_home_city(profile, home_city_name=value)
                    continue
                setattr(profile, attr, value)
            profile.save()

        return instance
