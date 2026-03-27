"""Compatibility exports for historical imports from apps.core.models."""

from apps.backoffice.models import OperationLog
from apps.community.models import PostComment, PostFavorite, PostLike, TravelPost
from apps.destinations.models import Attraction, TravelCity
from apps.planner.models import TravelPlan
from apps.users.models import UserProfile


__all__ = [
    "Attraction",
    "OperationLog",
    "PostComment",
    "PostFavorite",
    "PostLike",
    "TravelCity",
    "TravelPlan",
    "TravelPost",
    "UserProfile",
]




