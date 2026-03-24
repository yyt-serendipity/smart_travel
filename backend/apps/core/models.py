"""Compatibility exports for historical imports from apps.core.models."""

from apps.backoffice.models import OperationLog
from apps.community.models import PostComment, PostFavorite, PostLike, TravelPost
from apps.destinations.models import Attraction, Destination, TravelCity
from apps.planner.models import TravelPlan, TripPlan
from apps.users.models import UserProfile


__all__ = [
    "Attraction",
    "Destination",
    "OperationLog",
    "PostComment",
    "PostFavorite",
    "PostLike",
    "TravelCity",
    "TravelPlan",
    "TravelPost",
    "TripPlan",
    "UserProfile",
]
