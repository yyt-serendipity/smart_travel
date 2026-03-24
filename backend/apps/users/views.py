from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.activity import log_operation
from apps.core.media_utils import save_uploaded_file
from apps.users.serializers import LoginSerializer, RegisterSerializer, UserProfileSerializer
from apps.users.services import ensure_user_profile, serialize_user


class RegisterAPIView(APIView):
    """POST /api/auth/register/ 注册账号并返回登录 token。"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        ensure_user_profile(user)
        token, _ = Token.objects.get_or_create(user=user)
        log_operation(request, "auth", "register", target=user, detail={"username": user.username})
        return Response({"token": token.key, "user": serialize_user(user)}, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """POST /api/auth/login/ 登录并返回 token 与用户摘要。"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response({"detail": "用户名或密码错误。"}, status=status.HTTP_400_BAD_REQUEST)
        ensure_user_profile(user)
        token, _ = Token.objects.get_or_create(user=user)
        log_operation(request, "auth", "login", target=user, detail={"username": user.username})
        return Response({"token": token.key, "user": serialize_user(user)})


class LogoutAPIView(APIView):
    """POST /api/auth/logout/ 退出当前账号并删除 token。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        log_operation(request, "auth", "logout", target=request.user, detail={"username": request.user.username})
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "已退出登录。"})


class MeAPIView(APIView):
    """GET /api/auth/me/ 获取当前登录用户的简要信息。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_user_profile(request.user)
        return Response({"user": serialize_user(request.user)})


class ProfileAPIView(APIView):
    """GET/PATCH /api/profile/me/ 读取或更新个人主页资料。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_user_profile(request.user)
        return Response(UserProfileSerializer(profile).data)

    def patch(self, request):
        profile = ensure_user_profile(request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_operation(
            request,
            "profile",
            "update-profile",
            target=profile,
            detail={"home_city": serializer.data.get("home_city", ""), "has_avatar": bool(serializer.data.get("avatar_url"))},
        )
        return Response(serializer.data)


class MediaUploadAPIView(APIView):
    """POST /api/uploads/ 上传图片或文件并返回可直接保存的 URL。"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get("file")
        category = (request.data.get("category") or "attachment").strip()
        if not uploaded:
            return Response({"detail": "请选择需要上传的文件。"}, status=status.HTTP_400_BAD_REQUEST)
        if uploaded.size > 10 * 1024 * 1024:
            return Response({"detail": "文件大小不能超过 10MB。"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            saved_upload = save_uploaded_file(uploaded, folder=category, category=category)
        except (ValueError, RuntimeError) as exc:
            log_operation(
                request,
                "upload",
                "upload-media",
                status="failed",
                detail={"filename": uploaded.name, "category": category, "reason": str(exc)},
            )
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_operation(
            request,
            "upload",
            "upload-media",
            target={"type": "UploadedFile", "name": uploaded.name},
            detail={"category": category, "url": saved_upload.url, "size": uploaded.size},
        )
        return Response(
            {
                "url": saved_upload.url,
                "name": uploaded.name,
                "size": uploaded.size,
                "category": category,
            },
            status=status.HTTP_201_CREATED,
        )
