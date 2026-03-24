from apps.community.models import TravelPost


def refresh_post_counters(post: TravelPost) -> TravelPost:
    post.likes_count = post.likes.count()
    post.save(update_fields=["likes_count", "updated_at"])
    return post
