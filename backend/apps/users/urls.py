from django.urls import path

from apps.users.views import LoginAPIView, LogoutAPIView, MeAPIView, MediaUploadAPIView, ProfileAPIView, RegisterAPIView


# 用户认证和个人资料接口。
urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="register"),
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="logout"),
    path("auth/me/", MeAPIView.as_view(), name="me"),
    path("profile/me/", ProfileAPIView.as_view(), name="profile-me"),
    path("uploads/", MediaUploadAPIView.as_view(), name="media-upload"),
]
