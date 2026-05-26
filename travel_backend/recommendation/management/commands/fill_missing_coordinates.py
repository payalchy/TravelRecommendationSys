import json
import re
import time
from difflib import SequenceMatcher
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
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
        parser.add_argument(
            "--build-city-cache",
            action="store_true",
            help="Build city coordinates cache from Excel (slow, 1.5s per city)",
        )
        parser.add_argument(
            "--city-delay",
            type=float,
            default=1.5,
            help="Delay between city lookups in seconds (for rate limiting)",
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

    def _build_city_coordinates_cache(self, excel_file, city_delay, max_retries):
        """Build a cache of all unique city coordinates from Excel file.
        
        This uses Nominatim with longer delays (1.5s+) to avoid rate limiting.
        Takes ~8+ minutes for 327 cities but provides fallback coordinates for all remaining destinations.
        """
        try:
            self.stdout.write(self.style.WARNING(f"Reading cities from {excel_file}..."))
            df = pd.read_excel(excel_file)
            cities = sorted(df['city'].dropna().unique())
            self.stdout.write(f"Found {len(cities)} unique cities")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read Excel file: {e}"))
            return {}

        city_coords = {}
        total = len(cities)
        successful = 0

        self.stdout.write(self.style.WARNING(f"\nFetching coordinates for {total} cities (delay={city_delay}s per city)..."))
        self.stdout.write("This may take ~8+ minutes. Press Ctrl+C to stop.\n")

        for idx, city in enumerate(cities, 1):
            try:
                query = f"{city}, Nepal"
                payload = self._fetch_payload(query, city_delay, max_retries)

                if payload and len(payload) > 0:
                    first = payload[0]
                    coords = (float(first.get("lat")), float(first.get("lon")))
                    city_coords[city] = coords
                    successful += 1
                    status = "✓"
                else:
                    status = "⚠"

                if idx % 10 == 0 or idx == total:
                    pct = (idx / total) * 100
                    self.stdout.write(
                        f"[{idx:3d}/{total}] {status} {city:<30} - "
                        f"Progress: {pct:.0f}% ({successful} successful)"
                    )

            except HTTPError as e:
                if e.code == 429:
                    self.stdout.write(self.style.WARNING(f"[{idx:3d}/{total}] ⚠ {city:<30} - Rate limited, retrying with backoff..."))
                    time.sleep(city_delay * 2)
                else:
                    self.stdout.write(self.style.ERROR(f"[{idx:3d}/{total}] ✗ {city:<30} - HTTP {e.code}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{idx:3d}/{total}] ✗ {city:<30} - {str(e)[:50]}"))

        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS(
            f"✓ City Cache Complete: {len(city_coords)}/{total} cities mapped ({(len(city_coords)/total)*100:.1f}%)"
        ))
        return city_coords

    def _get_city_fallback_coordinate(self, destination, city_coords_cache):
        """Get coordinates using city center fallback.
        
        Returns (lat, lon, source_city) or None if city not in cache.
        """
        if not destination.city:
            return None

        # Try exact city match
        if destination.city in city_coords_cache:
            lat, lon = city_coords_cache[destination.city]
            return lat, lon, destination.city

        # Try fuzzy city match
        for cached_city, coords in city_coords_cache.items():
            if destination.city.lower() in cached_city.lower() or cached_city.lower() in destination.city.lower():
                lat, lon = coords
                return lat, lon, cached_city

        return None

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
        """Fetch coordinates for a destination using Nominatim.
        
        Returns (lat, lon, query) on success, None on failure.
        """
        if destination.city:
            # Try destination name + city first for better precision
            queries = [
                f"{destination.pName}, {destination.city}, Nepal",
                f"{destination.pName}, Nepal",
            ]
        else:
            queries = [f"{destination.pName}, Nepal"]

        if destination.province:
            # Insert province-based query early
            queries.insert(0, f"{destination.pName}, {destination.province}, Nepal")

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
        build_city_cache = options.get("build_city_cache", False)
        city_delay = float(options.get("city_delay", 1.5))

        # Step 1: Build city coordinates cache if requested
        city_coords_cache = {}
        if build_city_cache:
            try:
                excel_file = "nepal_destination_all.xlsx"
                city_coords_cache = self._build_city_coordinates_cache(excel_file, city_delay, max_retries)
                self.stdout.write("\n" + "="*70 + "\n")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error building city cache: {e}"))

        # Step 2: Process destinations
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
        city_fallback = 0
        skipped = 0
        failed = 0

        self.stdout.write(self.style.WARNING(f"Processing {total} destinations..."))
        self.stdout.write(f"Sources: Nominatim → Similar Name → City Center → Fail\n")

        for idx, destination in enumerate(queryset, 1):
            if not destination.pName:
                skipped += 1
                continue

            try:
                resolved = self._fetch_coordinates(destination, delay, max_retries)

                if resolved:
                    lat, lon, used_query = resolved
                    source = "geocoded"
                else:
                    # Try 1: Similar destination with nearby offset
                    similar = self._find_similar_destination(destination, min_similarity)
                    if similar is not None:
                        similar_destination, score = similar
                        lat, lon = self._nearby_coordinate_copy(
                            similar_destination.latitude,
                            similar_destination.longitude,
                            destination.id,
                        )
                        source = f"nearby:{similar_destination.pName} ({score:.2f})"
                    # Try 2: City center fallback
                    elif city_coords_cache:
                        city_result = self._get_city_fallback_coordinate(destination, city_coords_cache)
                        if city_result:
                            lat, lon, source_city = city_result
                            source = f"city_center:{source_city}"
                            city_fallback += 1
                        else:
                            failed += 1
                            self.stdout.write(f"  ✗ {destination.pName} ({destination.city}): No coordinates found")
                            time.sleep(delay)
                            continue
                    else:
                        failed += 1
                        if idx % 50 == 0:
                            self.stdout.write(f"  ✗ {destination.pName}: No geocoding available")
                        time.sleep(delay)
                        continue

                if not dry_run:
                    destination.latitude = lat
                    destination.longitude = lon
                    destination.save(update_fields=["latitude", "longitude"])

                updated += 1
                if source == "geocoded":
                    geocoded += 1
                    if idx % 50 == 0:
                        self.stdout.write(
                            f"  ✓ {destination.pName:<35} [geocoded] ({lat:.4f}, {lon:.4f})"
                        )
                elif source.startswith("nearby:"):
                    nearby_fallback += 1
                    if idx % 100 == 0:
                        self.stdout.write(f"  ✓ {destination.pName:<35} [{source}] ({lat:.4f}, {lon:.4f})")
                elif source.startswith("city_center:"):
                    if idx % 100 == 0:
                        self.stdout.write(f"  ✓ {destination.pName:<35} [{source}] ({lat:.4f}, {lon:.4f})")

                if idx % 100 == 0:
                    pct = (idx / total) * 100
                    self.stdout.write(
                        f"    Progress: {idx}/{total} ({pct:.1f}%) - "
                        f"Geocoded:{geocoded} Nearby:{nearby_fallback} City:{city_fallback}"
                    )

            except Exception as exc:
                failed += 1
                self.stdout.write(f"  ✗ {destination.pName}: {exc}")

            time.sleep(delay)

        # Final summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS(
            f"✓ COMPLETED\n"
            f"  Updated: {updated}/{total} ({(updated/total)*100:.1f}%)\n"
            f"    - Geocoded (Nominatim): {geocoded}\n"
            f"    - Similar Name Fallback: {nearby_fallback}\n"
            f"    - City Center Fallback: {city_fallback}\n"
            f"  Skipped: {skipped}\n"
            f"  Failed: {failed}\n"
            f"  Dry Run: {dry_run}"
        ))
        self.stdout.write("="*70)
