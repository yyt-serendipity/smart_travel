from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.community.serializers import (
    PostCommentCreateSerializer,
    TravelPostCreateSerializer,
    TravelPostDetailSerializer,
    TravelPostListSerializer,
)
from apps.community.models import PostFavorite, TravelPost
from apps.community.services import refresh_post_counters
from apps.core.activity import log_operation
from apps.core.permissions import IsAuthorOrAdminOrReadOnly


class TravelPostViewSet(viewsets.ModelViewSet):
    """社区帖子接口，覆盖列表、详情、发帖、点赞、收藏与评论。"""

    queryset = TravelPost.objects.select_related("author", "author__profile", "city", "attraction").all()

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        if self.action in {"create", "like", "favorite", "favorites", "comment"}:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAuthorOrAdminOrReadOnly()]

    def get_queryset(self):
        queryset = (
            TravelPost.objects.select_related("author", "author__profile", "city", "attraction")
            .annotate(comment_count=Count("comments", distinct=True), favorite_count=Count("favorites", distinct=True))
            .filter(status=TravelPost.STATUS_PUBLISHED)
        )
        city_id = self.request.query_params.get("city_id")
        attraction_id = self.request.query_params.get("attraction_id")
        author_id = self.request.query_params.get("author_id")
        keyword = self.request.query_params.get("q")

        if city_id:
            queryset = queryset.filter(city_id=city_id)
        if attraction_id:
            queryset = queryset.filter(attraction_id=attraction_id)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        if keyword:
            queryset = queryset.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TravelPostDetailSerializer
        if self.action in {"create", "update", "partial_update"}:
            return TravelPostCreateSerializer
        return TravelPostListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=["views_count", "updated_at"])
        serializer = self.get_serializer(instance, context={"request": request})
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, status=TravelPost.STATUS_PUBLISHED)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        log_operation(
            request,
            "community",
            "create-post",
            target=serializer.instance,
            detail={"city_id": serializer.instance.city_id, "attraction_id": serializer.instance.attraction_id},
        )
        detail_serializer = TravelPostDetailSerializer(serializer.instance, context={"request": request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def favorites(self, request):
        queryset = self.get_queryset().filter(favorites__user=request.user).order_by("-favorites__created_at")
        serializer = TravelPostListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        post = self.get_object()
        like = post.likes.filter(user=request.user).first()
        if like:
            like.delete()
            liked = False
        else:
            post.likes.create(user=request.user)
            liked = True
        refresh_post_counters(post)
        log_operation(request, "community", "toggle-like", target=post, detail={"liked": liked})
        return Response({"liked": liked, "likes_count": post.likes_count})

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        post = self.get_object()
        favorite = PostFavorite.objects.filter(post=post, user=request.user).first()
        if favorite:
            favorite.delete()
            favorited = False
        else:
            PostFavorite.objects.create(post=post, user=request.user)
            favorited = True
        favorite_count = PostFavorite.objects.filter(post=post).count()
        log_operation(request, "community", "toggle-favorite", target=post, detail={"favorited": favorited})
        return Response({"favorited": favorited, "favorite_count": favorite_count})

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        post = self.get_object()
        payload = {**request.data, "post": post.id}
        serializer = PostCommentCreateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        log_operation(
            request,
            "community",
            "comment-post",
            target=post,
            detail={"comment_id": serializer.instance.id, "parent_id": serializer.instance.parent_id},
        )
        detail_serializer = TravelPostDetailSerializer(
            self.get_queryset().get(pk=post.pk),
            context={"request": request},
        )
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
