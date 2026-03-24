from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.community.models import TravelPost
from apps.core.tagging import normalize_profile_styles, normalize_public_tags
from apps.destinations.models import Attraction, TravelCity
from apps.users.models import UserProfile


class Command(BaseCommand):
    help = "Normalize city, attraction, post and profile tags into a controlled set."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing them.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        summary = {
            "TravelCity.tags": self._normalize_queryset(
                TravelCity.objects.all(),
                field_name="tags",
                normalizer=normalize_public_tags,
                dry_run=dry_run,
            ),
            "Attraction.tags": self._normalize_queryset(
                Attraction.objects.all(),
                field_name="tags",
                normalizer=normalize_public_tags,
                dry_run=dry_run,
            ),
            "TravelPost.tags": self._normalize_queryset(
                TravelPost.objects.all(),
                field_name="tags",
                normalizer=normalize_public_tags,
                dry_run=dry_run,
            ),
            "UserProfile.favorite_styles": self._normalize_queryset(
                UserProfile.objects.all(),
                field_name="favorite_styles",
                normalizer=normalize_profile_styles,
                dry_run=dry_run,
            ),
        }

        mode = "Preview" if dry_run else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{mode} tag normalization summary:"))
        for label, changed in summary.items():
            self.stdout.write(f"- {label}: {changed}")

    def _normalize_queryset(self, queryset, *, field_name: str, normalizer, dry_run: bool) -> int:
        changed_objects = []
        for obj in queryset.iterator():
            current = getattr(obj, field_name) or []
            normalized = normalizer(current)
            if list(current) == normalized:
                continue
            setattr(obj, field_name, normalized)
            changed_objects.append(obj)

        if changed_objects and not dry_run:
            queryset.model.objects.bulk_update(changed_objects, [field_name])
        return len(changed_objects)
