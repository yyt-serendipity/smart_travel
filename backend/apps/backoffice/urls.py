from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.backoffice.views import (
    AdminAttractionViewSet,
    AdminCityViewSet,
    AdminImportExcelAPIView,
    AdminImportExcelUploadAPIView,
    AdminLogViewSet,
    AdminPostViewSet,
    AdminSummaryAPIView,
    AdminUserViewSet,
)


router = DefaultRouter()
# 后台城市管理接口。
router.register("cities", AdminCityViewSet, basename="backoffice-city")
# 后台用户管理接口。
router.register("users", AdminUserViewSet, basename="backoffice-user")
# 后台景点管理接口。
router.register("attractions", AdminAttractionViewSet, basename="backoffice-attraction")
# 后台帖子管理接口。
router.register("posts", AdminPostViewSet, basename="backoffice-post")
# 后台日志接口。
router.register("logs", AdminLogViewSet, basename="backoffice-log")

urlpatterns = [
    # 后台概览统计接口。
    path("summary/", AdminSummaryAPIView.as_view(), name="backoffice-summary"),
    # Excel 数据导入接口。
    path("import-excels/", AdminImportExcelAPIView.as_view(), name="backoffice-import-excels"),
    path("import-excels/upload/", AdminImportExcelUploadAPIView.as_view(), name="backoffice-import-excels-upload"),
    path("", include(router.urls)),
]
