from pathlib import Path

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.backoffice.serializers import AdminUserSerializer, OperationLogSerializer, TravelCityAdminSerializer, TravelPostAdminSerializer
from apps.backoffice.models import OperationLog
from apps.community.models import PostComment, TravelPost
from apps.core.activity import log_operation
from apps.core.media_utils import save_uploaded_file
from apps.core.permissions import IsAdminUserOnly
from apps.destinations.models import Attraction, TravelCity
from apps.destinations.importers import import_excel_directory, import_excel_file
from apps.destinations.serializers import AttractionSerializer, TravelCityListSerializer
from apps.destinations.services import default_excel_directory


User = get_user_model()


def parse_truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def build_admin_summary() -> dict:
    """Return the five counts used by the backoffice overview."""

    return {
        "user_count": User.objects.count(),
        "city_count": TravelCity.objects.count(),
        "attraction_count": Attraction.objects.count(),
        "post_count": TravelPost.objects.count(),
        "comment_count": PostComment.objects.count(),
    }


class AdminSummaryAPIView(APIView):
    """GET /api/backoffice/summary/ returns the five overview metrics."""

    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        payload = build_admin_summary()
        return Response(payload)


class AdminUserViewSet(viewsets.ModelViewSet):
    """后台用户管理接口，支持筛选、编辑资料、禁用和删除账号。"""

    permission_classes = [IsAdminUserOnly]
    serializer_class = AdminUserSerializer
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = (
            User.objects.select_related("profile")
            .annotate(
                post_count=Count("travel_posts", distinct=True),
                comment_count=Count("post_comments", distinct=True),
                plan_count=Count("travel_plans", distinct=True),
            )
            .order_by("-is_staff", "-date_joined", "username")
        )
        keyword = self.request.query_params.get("q")
        role = self.request.query_params.get("role")
        status_value = self.request.query_params.get("status")
        limit = self.request.query_params.get("limit")
        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(profile__nickname__icontains=keyword)
                | Q(profile__home_city__icontains=keyword)
                | Q(profile__home_city_ref__name__icontains=keyword)
            )
        if role == "admin":
            queryset = queryset.filter(is_staff=True)
        elif role == "member":
            queryset = queryset.filter(is_staff=False)
        if status_value == "active":
            queryset = queryset.filter(is_active=True)
        elif status_value == "disabled":
            queryset = queryset.filter(is_active=False)
        if limit:
            queryset = queryset[: int(limit)]
        return queryset

    def perform_update(self, serializer):
        instance = serializer.save()
        log_operation(
            self.request,
            "backoffice",
            "update-user",
            target=instance,
            detail={"is_staff": instance.is_staff, "is_active": instance.is_active},
        )

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError("不能删除当前登录的管理员账号。")
        log_operation(
            self.request,
            "backoffice",
            "delete-user",
            target=instance,
            detail={"is_staff": instance.is_staff, "is_active": instance.is_active},
        )
        instance.delete()


class AdminCityViewSet(viewsets.ModelViewSet):
    """后台城市管理接口，支持城市的查询、创建、修改和删除。"""

    permission_classes = [IsAdminUserOnly]
    serializer_class = TravelCityAdminSerializer

    def get_queryset(self):
        queryset = TravelCity.objects.all().order_by("-is_featured", "-updated_at")
        keyword = self.request.query_params.get("q")
        limit = self.request.query_params.get("limit")
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(province__icontains=keyword)
                | Q(short_intro__icontains=keyword)
                | Q(overview__icontains=keyword)
            )
        if limit:
            queryset = queryset[: int(limit)]
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()
        log_operation(self.request, "backoffice", "create-city", target=instance, detail={"province": instance.province})

    def perform_update(self, serializer):
        instance = serializer.save()
        log_operation(self.request, "backoffice", "update-city", target=instance, detail={"province": instance.province})

    def perform_destroy(self, instance):
        log_operation(self.request, "backoffice", "delete-city", target=instance, detail={"province": instance.province})
        instance.delete()


class AdminAttractionViewSet(viewsets.ModelViewSet):
    """后台景点管理接口，支持按关键词和城市筛选景点。"""

    permission_classes = [IsAdminUserOnly]
    serializer_class = AttractionSerializer

    def get_queryset(self):
        queryset = Attraction.objects.select_related("city").all().order_by("-updated_at")
        keyword = self.request.query_params.get("q")
        city_id = self.request.query_params.get("city_id")
        limit = self.request.query_params.get("limit")
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(address__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(city__name__icontains=keyword)
            )
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        if limit:
            queryset = queryset[: int(limit)]
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()
        log_operation(
            self.request,
            "backoffice",
            "create-attraction",
            target=instance,
            detail={"city_id": instance.city_id, "city_name": instance.city.name},
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        log_operation(
            self.request,
            "backoffice",
            "update-attraction",
            target=instance,
            detail={"city_id": instance.city_id, "city_name": instance.city.name},
        )

    def perform_destroy(self, instance):
        log_operation(
            self.request,
            "backoffice",
            "delete-attraction",
            target=instance,
            detail={"city_id": instance.city_id, "city_name": instance.city.name},
        )
        instance.delete()


class AdminPostViewSet(viewsets.ModelViewSet):
    """后台帖子管理接口，支持社区内容的筛选和删除。"""

    permission_classes = [IsAdminUserOnly]
    serializer_class = TravelPostAdminSerializer

    def get_queryset(self):
        queryset = TravelPost.objects.select_related("author", "city", "attraction").all().order_by("-created_at")
        keyword = self.request.query_params.get("q")
        city_id = self.request.query_params.get("city_id")
        limit = self.request.query_params.get("limit")
        if keyword:
            queryset = queryset.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        if limit:
            queryset = queryset[: int(limit)]
        return queryset

    def perform_destroy(self, instance):
        log_operation(
            self.request,
            "backoffice",
            "delete-post",
            target=instance,
            detail={"author_id": instance.author_id, "city_id": instance.city_id, "attraction_id": instance.attraction_id},
        )
        instance.delete()


class AdminLogViewSet(viewsets.ReadOnlyModelViewSet):
    """后台操作日志查询接口。"""

    permission_classes = [IsAdminUserOnly]
    serializer_class = OperationLogSerializer

    def get_queryset(self):
        queryset = OperationLog.objects.select_related("user").all().order_by("-created_at")
        category = self.request.query_params.get("category")
        status_value = self.request.query_params.get("status")
        limit = self.request.query_params.get("limit")
        if category:
            queryset = queryset.filter(category=category)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if limit:
            queryset = queryset[: int(limit)]
        return queryset


class AdminImportExcelAPIView(APIView):
    """POST /api/backoffice/import-excels/ 从本地 Excel 目录导入城市与景点。"""

    permission_classes = [IsAuthenticated, IsAdminUserOnly]

    def post(self, request):
        directory = Path(request.data.get("directory") or default_excel_directory())
        if not directory.exists():
            log_operation(
                request,
                "backoffice",
                "import-excel-directory",
                status="failed",
                detail={"directory": str(directory), "reason": "directory-not-found"},
            )
            return Response({"detail": f"目录不存在: {directory}"}, status=status.HTTP_400_BAD_REQUEST)
        overwrite = parse_truthy(request.data.get("overwrite", False))
        limit = request.data.get("limit")
        imported = import_excel_directory(directory, overwrite=overwrite, limit=int(limit) if limit else None)
        log_operation(
            request,
            "backoffice",
            "import-excel-directory",
            detail={"directory": str(directory), "overwrite": overwrite, "count": len(imported)},
        )
        return Response(
            {
                "detail": f"已导入 {len(imported)} 个城市工作簿。",
                "cities": TravelCityListSerializer(imported[:20], many=True).data,
            }
        )


class AdminImportExcelUploadAPIView(APIView):
    """POST /api/backoffice/import-excels/upload/ 上传 Excel 文件并导入。"""

    permission_classes = [IsAuthenticated, IsAdminUserOnly]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        files = request.FILES.getlist("files")
        overwrite = parse_truthy(request.data.get("overwrite", False))
        if not files:
            return Response({"detail": "请至少选择一个 Excel 文件。"}, status=status.HTTP_400_BAD_REQUEST)

        imported = []
        filenames = []
        for uploaded in files:
            try:
                saved_upload = save_uploaded_file(uploaded, folder="excel-imports", category="excel-import")
                imported.append(import_excel_file(saved_upload.content, source_name=uploaded.name, overwrite=overwrite))
                filenames.append(uploaded.name)
            except (ValueError, RuntimeError) as exc:
                log_operation(
                    request,
                    "backoffice",
                    "import-excel-upload",
                    status="failed",
                    detail={"filename": uploaded.name, "reason": str(exc)},
                )
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_operation(
            request,
            "backoffice",
            "import-excel-upload",
            detail={"files": filenames, "overwrite": overwrite, "count": len(imported)},
        )
        return Response(
            {
                "detail": f"已从上传文件中导入 {len(imported)} 个城市工作簿。",
                "cities": TravelCityListSerializer(imported[:20], many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )
