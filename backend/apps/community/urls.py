from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.community.views import TravelPostViewSet


router = DefaultRouter()
# 社区帖子流、帖子详情、点赞和评论接口。
router.register("posts", TravelPostViewSet, basename="travel-post")

urlpatterns = [
    path("", include(router.urls)),
]
