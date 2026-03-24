from django.contrib import admin

from apps.community.models import PostComment, PostFavorite, PostLike, TravelPost


@admin.register(TravelPost)
class TravelPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "city", "likes_count", "views_count", "status", "created_at")
    search_fields = ("title", "author__username", "city__name", "content")
    list_filter = ("status", "city")


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "parent", "created_at")
    search_fields = ("post__title", "author__username", "content")


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    search_fields = ("post__title", "user__username")


@admin.register(PostFavorite)
class PostFavoriteAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    search_fields = ("post__title", "user__username")
