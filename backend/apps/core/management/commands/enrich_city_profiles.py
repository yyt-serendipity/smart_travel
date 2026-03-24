from __future__ import annotations

import math

import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.destinations.ai_profiles import (
    PROFILE_FIELDS,
    CityProfileGenerationError,
    build_fallback_profile,
    chunked,
    generate_city_profiles,
    needs_profile_refresh,
)
from apps.destinations.models import TravelCity


class Command(BaseCommand):
    help = "Generate city introductions, highlights and travel tips with AI and save them into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--city",
            action="append",
            dest="cities",
            default=[],
            help="Only enrich the specified city name. Repeat this option to select multiple cities.",
        )
        parser.add_argument("--limit", type=int, default=None, help="Only process the first N matched cities.")
        parser.add_argument("--offset", type=int, default=0, help="Skip the first N matched cities before processing.")
        parser.add_argument("--batch-size", type=int, default=8, help="How many cities to send in one LLM request.")
        parser.add_argument("--force", action="store_true", help="Refresh all matched cities instead of only weak or missing profiles.")
        parser.add_argument("--dry-run", action="store_true", help="Preview generated content without writing into the database.")
        parser.add_argument(
            "--strict",
            action="store_true",
            help="If LLM generation fails, skip the city instead of filling it with a template fallback.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        if batch_size <= 0:
            raise CommandError("--batch-size must be a positive integer.")
        if options["offset"] < 0:
            raise CommandError("--offset must be zero or a positive integer.")

        queryset = TravelCity.objects.prefetch_related("attractions").order_by("id")
        city_names = [name.strip() for name in options["cities"] if name and name.strip()]
        if city_names:
            queryset = queryset.filter(name__in=city_names)

        cities = list(queryset)
        if not cities:
            raise CommandError("No cities matched the current filter.")

        if not options["force"]:
            cities = [city for city in cities if needs_profile_refresh(city)]

        if options["offset"]:
            cities = cities[options["offset"] :]

        if options["limit"] is not None:
            cities = cities[: options["limit"]]

        if not cities:
            self.stdout.write(self.style.SUCCESS("No city profiles need refreshing."))
            return

        total_batches = math.ceil(len(cities) / batch_size)
        self.stdout.write(
            f"Preparing to process {len(cities)} cities in {total_batches} batch(es). "
            f"Mode: {'dry-run' if options['dry_run'] else 'write'}"
        )

        stats = {
            "updated": 0,
            "llm_batch": 0,
            "llm_single": 0,
            "template": 0,
            "skipped": 0,
        }

        for batch_index, city_batch in enumerate(chunked(cities, batch_size), start=1):
            self.stdout.write(f"[{batch_index}/{total_batches}] Processing {len(city_batch)} cities...")
            generated = self.generate_batch(city_batch, strict=options["strict"])

            batch_updated = []
            now = timezone.now()
            for city in city_batch:
                generated_item = generated.get(city.id)
                if not generated_item:
                    stats["skipped"] += 1
                    self.stderr.write(f"  - skipped {city.name}: no profile was generated")
                    continue

                source = generated_item["source"]
                profile = generated_item["profile"]
                stats[source] += 1

                if options["dry_run"]:
                    preview = profile["short_intro"]
                    self.stdout.write(f"  - {city.name} [{source}] {preview}")
                    continue

                for field_name in PROFILE_FIELDS:
                    setattr(city, field_name, profile[field_name])
                city.updated_at = now
                batch_updated.append(city)

            if batch_updated and not options["dry_run"]:
                TravelCity.objects.bulk_update(batch_updated, [*PROFILE_FIELDS, "updated_at"])
                stats["updated"] += len(batch_updated)
                self.stdout.write(f"  Saved {len(batch_updated)} cities in this batch.")

        self.stdout.write(self.style.SUCCESS("City profile enrichment finished."))
        self.stdout.write(
            "Summary: "
            f"updated={stats['updated']}, "
            f"llm_batch={stats['llm_batch']}, "
            f"llm_single={stats['llm_single']}, "
            f"template={stats['template']}, "
            f"skipped={stats['skipped']}"
        )

    def generate_batch(self, city_batch: list[TravelCity], *, strict: bool) -> dict[int, dict]:
        results: dict[int, dict] = {}
        unresolved = list(city_batch)

        try:
            batch_profiles = generate_city_profiles(city_batch)
        except (requests.RequestException, CityProfileGenerationError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.stderr.write(f"  Batch request failed: {exc}")
        else:
            for city in city_batch:
                profile = batch_profiles.get(city.id)
                if not profile:
                    continue
                results[city.id] = {"profile": profile, "source": "llm_batch"}
            unresolved = [city for city in city_batch if city.id not in results]

        for city in unresolved:
            try:
                single_profile = generate_city_profiles([city]).get(city.id)
            except (requests.RequestException, CityProfileGenerationError, ValueError, TypeError, KeyError, AttributeError) as exc:
                self.stderr.write(f"  Single-city request failed for {city.name}: {exc}")
                if strict:
                    continue
                results[city.id] = {"profile": build_fallback_profile(city), "source": "template"}
                continue

            if single_profile:
                results[city.id] = {"profile": single_profile, "source": "llm_single"}
                continue

            if strict:
                self.stderr.write(f"  No valid profile returned for {city.name}.")
                continue
            results[city.id] = {"profile": build_fallback_profile(city), "source": "template"}

        return results
