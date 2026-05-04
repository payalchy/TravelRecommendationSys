import json
import re
import time
from difflib import SequenceMatcher
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand
from django.db.models import Q

from recommendation.models import Destination


class Command(BaseCommand):
    help = "Fill missing latitude/longitude for destinations using Nominatim"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Max rows to process (0 = all)")
        parser.add_argument("--sleep", type=float, default=1.2, help="Delay between requests in seconds")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes")
        parser.add_argument("--force", action="store_true", help="Recompute even if coordinates exist")
        parser.add_argument("--max-retries", type=int, default=4, help="Retries for HTTP 429")
        parser.add_argument(
            "--min-similarity",
            type=float,
            default=0.72,
            help="Minimum name similarity to use nearby fallback coordinate",
        )

    def _normalize_name(self, value):
        if not value:
            return ""

        cleaned = re.sub(r"[^a-z0-9\s]", " ", str(value).lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _name_similarity(self, left, right):
        return SequenceMatcher(None, self._normalize_name(left), self._normalize_name(right)).ratio()

    def _nearby_coordinate_copy(self, latitude, longitude, destination_id):
        # Small deterministic offset keeps coordinates near a similar place but not identical.
        seed = int(destination_id or 0)
        lat_shift = ((seed % 5) - 2) * 0.004
        lon_shift = (((seed // 5) % 5) - 2) * 0.004

        lat = max(-90.0, min(90.0, float(latitude) + lat_shift))
        lon = max(-180.0, min(180.0, float(longitude) + lon_shift))
        return lat, lon

    def _find_similar_destination(self, destination, min_similarity):
        if not destination.pName:
            return None

        candidates = Destination.objects.exclude(pk=destination.pk).filter(
            latitude__isnull=False,
            longitude__isnull=False,
        )

        best = None
        best_score = 0.0
        target_name = destination.pName
        target_province = (destination.province or "").strip().lower()

        for candidate in candidates.iterator():
            score = self._name_similarity(target_name, candidate.pName)

            if target_province and (candidate.province or "").strip().lower() == target_province:
                score += 0.08

            if score > best_score:
                best_score = score
                best = candidate

        if best is None or best_score < float(min_similarity):
            return None

        return best, best_score

    def _fetch_coordinates(self, destination, delay, max_retries):
        if destination.province:
            queries = [f"{destination.pName}, {destination.province}, Nepal", f"{destination.pName}, Nepal"]
        else:
            queries = [f"{destination.pName}, Nepal"]

        for query in queries:
            try:
                payload = self._fetch_payload(query, delay, max_retries)
            except HTTPError as exc:
                # Fast mode: if provider keeps rate-limiting, skip to nearby-name fallback.
                if exc.code == 429:
                    return None
                raise

            if not payload:
                continue

            first = payload[0]
            try:
                return float(first.get("lat")), float(first.get("lon")), query
            except (TypeError, ValueError):
                continue

        return None

    def _fetch_payload(self, query, delay, max_retries):
        params = urlencode({"q": query, "format": "json", "limit": 1})
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        req = Request(url, headers={"User-Agent": "travel-backend-bulk-geocode/1.1"})

        attempt = 0
        while True:
            try:
                with urlopen(req, timeout=15) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code != 429 or attempt >= max_retries:
                    raise

                backoff = max(2.0, delay * (2 ** attempt))
                time.sleep(backoff)
                attempt += 1

    def handle(self, *args, **options):
        limit = options["limit"]
        delay = options["sleep"]
        dry_run = options["dry_run"]
        force = options["force"]
        max_retries = max(0, int(options["max_retries"]))
        min_similarity = float(options["min_similarity"])

        if force:
            queryset = Destination.objects.all().order_by("id")
        else:
            queryset = Destination.objects.filter(
                Q(latitude__isnull=True) | Q(longitude__isnull=True)
            ).order_by("id")

        if limit and limit > 0:
            queryset = queryset[:limit]

        total = queryset.count()
        updated = 0
        geocoded = 0
        nearby_fallback = 0
        skipped = 0
        failed = 0

        self.stdout.write(self.style.WARNING(f"Processing {total} destinations..."))

        for destination in queryset:
            if not destination.pName:
                skipped += 1
                continue

            try:
                resolved = self._fetch_coordinates(destination, delay, max_retries)

                if resolved:
                    lat, lon, used_query = resolved
                    source = "geocoded"
                else:
                    similar = self._find_similar_destination(destination, min_similarity)
                    if similar is None:
                        failed += 1
                        self.stdout.write(f"No match: {destination.pName}")
                        time.sleep(delay)
                        continue

                    similar_destination, score = similar
                    lat, lon = self._nearby_coordinate_copy(
                        similar_destination.latitude,
                        similar_destination.longitude,
                        destination.id,
                    )
                    source = f"nearby:{similar_destination.pName} ({score:.2f})"

                if not dry_run:
                    destination.latitude = lat
                    destination.longitude = lon
                    destination.save(update_fields=["latitude", "longitude"])

                updated += 1
                if source == "geocoded":
                    geocoded += 1
                    self.stdout.write(
                        f"Updated (geocoded): {destination.pName} -> ({lat}, {lon})"
                        f" [query={used_query}]"
                    )
                else:
                    nearby_fallback += 1
                    self.stdout.write(f"Updated ({source}): {destination.pName} -> ({lat}, {lon})")

            except Exception as exc:
                failed += 1
                self.stdout.write(f"Failed: {destination.pName} ({exc})")

            time.sleep(delay)

        self.stdout.write(
            self.style.SUCCESS(
                "Done. "
                f"updated={updated}, geocoded={geocoded}, nearby_fallback={nearby_fallback}, "
                f"skipped={skipped}, failed={failed}, total={total}, dry_run={dry_run}"
            )
        )
