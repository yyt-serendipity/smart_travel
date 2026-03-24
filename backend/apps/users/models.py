from django.conf import settings
from django.db import models

from apps.destinations.models import TravelCity


CORE_APP_LABEL = "core"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    nickname = models.CharField("昵称", max_length=100, blank=True)
    avatar_url = models.URLField("头像链接", blank=True, max_length=500)
    bio = models.TextField("个人简介", blank=True)
    home_city = models.CharField("常住城市", max_length=100, blank=True)
    home_city_ref = models.ForeignKey(
        TravelCity,
        related_name="resident_profiles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    favorite_styles = models.JSONField("偏好风格", default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = CORE_APP_LABEL
        ordering = ["user__username"]

    def __str__(self) -> str:
        return self.nickname or self.user.username
