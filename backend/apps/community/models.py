from django.conf import settings
from django.db import models

from apps.destinations.models import Attraction, TravelCity


CORE_APP_LABEL = "core"


class TravelPost(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "草稿"),
        (STATUS_PUBLISHED, "已发布"),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="travel_posts", on_delete=models.CASCADE)
    city = models.ForeignKey(TravelCity, related_name="posts", on_delete=models.SET_NULL, null=True, blank=True)
    attraction = models.ForeignKey(Attraction, related_name="posts", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField("标题", max_length=180)
    content = models.TextField("正文")
    cover_image = models.URLField("封面图", blank=True, max_length=500)
    tags = models.JSONField("标签", default=list, blank=True)
    likes_count = models.PositiveIntegerField("点赞数", default=0)
    views_count = models.PositiveIntegerField("浏览数", default=0)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = CORE_APP_LABEL
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class PostLike(models.Model):
    post = models.ForeignKey(TravelPost, related_name="likes", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="liked_posts", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = CORE_APP_LABEL
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="uniq_post_like"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} like {self.post}"


class PostFavorite(models.Model):
    post = models.ForeignKey(TravelPost, related_name="favorites", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="favorite_posts", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = CORE_APP_LABEL
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="uniq_post_favorite"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} favorite {self.post}"


class PostComment(models.Model):
    post = models.ForeignKey(TravelPost, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="post_comments", on_delete=models.CASCADE)
    parent = models.ForeignKey("self", related_name="replies", on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField("评论内容")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = CORE_APP_LABEL
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.author} -> {self.post}"
