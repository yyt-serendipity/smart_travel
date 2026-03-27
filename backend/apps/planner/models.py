from django.conf import settings
from django.db import models

from apps.destinations.models import TravelCity


CORE_APP_LABEL = "core"


class TravelPlan(models.Model):
    STATUS_GENERATED = "generated"
    STATUS_COLLECTED = "collected"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_GENERATED, "已生成"),
        (STATUS_COLLECTED, "已收藏"),
        (STATUS_COMPLETED, "已完成"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="travel_plans", on_delete=models.CASCADE)
    city = models.ForeignKey(TravelCity, related_name="travel_plans", on_delete=models.CASCADE)
    title = models.CharField("方案标题", max_length=160)
    departure_city = models.CharField("出发城市", max_length=100, blank=True)
    duration_days = models.PositiveIntegerField("出行天数", default=3)
    budget_level = models.CharField("预算档位", max_length=50, default="balanced")
    companions = models.CharField("同行方式", max_length=60, default="双人")
    interests = models.JSONField("兴趣偏好", default=list, blank=True)
    summary = models.TextField("方案摘要", blank=True)
    estimated_budget = models.PositiveIntegerField("预算估算", default=0)
    itinerary = models.JSONField("行程内容", default=list, blank=True)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default=STATUS_GENERATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = CORE_APP_LABEL
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
