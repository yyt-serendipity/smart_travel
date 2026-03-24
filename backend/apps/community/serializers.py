from rest_framework import serializers

from apps.community.models import PostComment, PostFavorite, PostLike, TravelPost
from apps.core.tagging import normalize_public_tags
from apps.destinations.serializers import AttractionSerializer, TravelCityListSerializer
from apps.users.services import serialize_user


def is_post_liked(post, user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return PostLike.objects.filter(post=post, user=user).exists()


def is_post_favorited(post, user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return PostFavorite.objects.filter(post=post, user=user).exists()


class PostCommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ("id", "post", "author", "parent", "content", "created_at", "replies")
        read_only_fields = ("author", "replies")

    def get_author(self, obj):
        return serialize_user(obj.author)

    def get_replies(self, obj):
        if obj.parent_id:
            return []
        replies = obj.replies.select_related("author")
        return [
            {
                "id": reply.id,
                "author": serialize_user(reply.author),
                "content": reply.content,
                "created_at": reply.created_at,
            }
            for reply in replies
        ]


class TravelPostListSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    city_name = serializers.CharField(source="city.name", read_only=True)
    attraction_name = serializers.CharField(source="attraction.name", read_only=True)
    comment_count = serializers.SerializerMethodField()
    favorite_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    favorited = serializers.SerializerMethodField()

    class Meta:
        model = TravelPost
        fields = (
            "id",
            "author",
            "city",
            "city_name",
            "attraction",
            "attraction_name",
            "title",
            "content",
            "cover_image",
            "tags",
            "likes_count",
            "comment_count",
            "favorite_count",
            "views_count",
            "liked",
            "favorited",
            "created_at",
        )

    def get_author(self, obj):
        return serialize_user(obj.author)

    def get_comment_count(self, obj):
        return getattr(obj, "comment_count", obj.comments.count())

    def get_favorite_count(self, obj):
        return getattr(obj, "favorite_count", obj.favorites.count())

    def get_liked(self, obj):
        request = self.context.get("request")
        return is_post_liked(obj, getattr(request, "user", None))

    def get_favorited(self, obj):
        request = self.context.get("request")
        return is_post_favorited(obj, getattr(request, "user", None))


class TravelPostDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    city_detail = TravelCityListSerializer(source="city", read_only=True)
    attraction_detail = AttractionSerializer(source="attraction", read_only=True)
    comments = serializers.SerializerMethodField()
    favorite_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    favorited = serializers.SerializerMethodField()

    class Meta:
        model = TravelPost
        fields = (
            "id",
            "author",
            "city",
            "city_detail",
            "attraction",
            "attraction_detail",
            "title",
            "content",
            "cover_image",
            "tags",
            "likes_count",
            "favorite_count",
            "views_count",
            "liked",
            "favorited",
            "comments",
            "created_at",
        )

    def get_author(self, obj):
        return serialize_user(obj.author)

    def get_comments(self, obj):
        roots = obj.comments.filter(parent__isnull=True).select_related("author")
        return PostCommentSerializer(roots, many=True).data

    def get_favorite_count(self, obj):
        return getattr(obj, "favorite_count", obj.favorites.count())

    def get_liked(self, obj):
        request = self.context.get("request")
        return is_post_liked(obj, getattr(request, "user", None))

    def get_favorited(self, obj):
        request = self.context.get("request")
        return is_post_favorited(obj, getattr(request, "user", None))


class TravelPostCreateSerializer(serializers.ModelSerializer):
    def validate_tags(self, value):
        return normalize_public_tags(value)

    class Meta:
        model = TravelPost
        fields = ("id", "city", "attraction", "title", "content", "cover_image", "tags", "status")


class PostCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ("post", "parent", "content")
