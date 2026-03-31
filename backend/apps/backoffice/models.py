from django.conf import settings
from django.db import models


CORE_APP_LABEL = "core"


class OperationLog(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "成功"),
        (STATUS_FAILED, "失败"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="operation_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    category = models.CharField("分类", max_length=40)
    action = models.CharField("操作", max_length=80)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    target_type = models.CharField("对象类型", max_length=80, blank=True)
    target_id = models.PositiveBigIntegerField("对象 ID", null=True, blank=True)
    target_name = models.CharField("对象名称", max_length=255, blank=True)
    request_path = models.CharField("请求路径", max_length=255, blank=True)
    request_method = models.CharField("请求方法", max_length=12, blank=True)
    ip_address = models.CharField("IP 地址", max_length=64, blank=True)
    detail = models.JSONField("详情", default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = CORE_APP_LABEL
        db_table = "operation_log"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.category}:{self.action}"
