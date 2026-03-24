from django.contrib import admin

from apps.backoffice.models import OperationLog


admin.site.site_header = "Smart Travel 鍚庡彴绠＄悊"
admin.site.site_title = "Smart Travel Backoffice"
admin.site.index_title = "涓浗鏃呮父骞冲彴鏁版嵁绠＄悊"


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ("category", "action", "status", "user", "target_name", "created_at")
    search_fields = ("category", "action", "target_name", "user__username")
    list_filter = ("category", "status", "request_method")
