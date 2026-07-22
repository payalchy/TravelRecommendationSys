#!/usr/bin/env python
"""
Reset fuzzy-matched coordinates and re-apply with STRICTER threshold (0.60+)
This removes the 413 bad matches and reprocesses with higher confidence requirements.
"""

import os
import sys
import django
import json
import re
from difflib import SequenceMatcher

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from recommendation.models import Destination

# =========================
# PREPROCESSING & SIMILARITY
# =========================

COMMON_SUFFIXES = [
    'Hill', 'Peak', 'Trail', 'Trek', 'Pass', 'Area', 'Valley', 'Village', 'Town',
    'City', 'Bazaar', 'River', 'Lake', 'Forest', 'Temple', 'Monastery', 'Camp',
    'Base', 'Viewpoint', 'Point', 'Glacier', 'Waterfall', 'Route', 'Corridor',
    'Danda', 'Gadhi', 'Fort', 'Square', 'Park', 'Garden', 'Zone', 'Site',
    'Viewtower', 'Tower', 'Road', 'Street', 'Lane', 'Museum', 'School',
    'Airstrip', 'Airport', 'Railway', 'Station', 'Pond', 'Khola', 'Khad'
]

def preprocess_name(name):
    """Remove common suffixes and clean name for better matching"""
    name = str(name).strip()
    name = re.sub(r'\d+', '', name)  # Remove numbers
    for suffix in COMMON_SUFFIXES:
        if name.lower().endswith(suffix.lower()):
            name = name[:len(name)-len(suffix)].strip()
            break
    return name.lower().strip()

def similarity(a, b):
    """String similarity between two names"""
    a_clean = preprocess_name(a)
    b_clean = preprocess_name(b)
    if not a_clean or not b_clean:
        return 0.0
    return SequenceMatcher(None, a_clean, b_clean).ratio()

def word_overlap(a, b):
    """Check if key words overlap between two names"""
    a_words = set(preprocess_name(a).split())
    b_words = set(preprocess_name(b).split())
    if not a_words or not b_words:
        return 0
    overlap = len(a_words & b_words)
    return overlap / max(len(a_words), len(b_words))

# =========================
# MAIN LOGIC
# =========================

print("=" * 70)
print("STEP 1: RESET BAD FUZZY MATCHES")
print("=" * 70)

# Step 1: Count current state
total_before = Destination.objects.count()
with_coords_before = Destination.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).count()
print(f"\nBefore reset:")
print(f"  Total destinations: {total_before}")
print(f"  With coordinates: {with_coords_before}")

# Note: We can't easily identify which 413 were fuzzy matched, so we'll:
# 1. Load all 697 from JSON
# 2. Clear ALL coordinates first
# 3. Only restore the ones from the JSON backup (high confidence)
# 4. Then fuzzy match the rest with stricter threshold

print("\n[RESET] Clearing all coordinates to start fresh...")
updated_count = Destination.objects.all().update(latitude=None, longitude=None)
print(f"  Cleared {updated_count} destination coordinates")

with_coords_after_reset = Destination.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).count()
print(f"  Destinations now with coordinates: {with_coords_after_reset}")

# =========================
# STEP 2: RELOAD JSON & RESTORE ORIGINAL DATA
# =========================

print("\n" + "=" * 70)
print("STEP 2: RESTORE ORIGINAL 697 JSON COORDINATES (100% CONFIDENCE)")
print("=" * 70)

print("\n[FILE] Loading data_utf8.json...")
try:
    with open('data_utf8.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
except FileNotFoundError:
    print("[ERROR] data_utf8.json not found in current directory")
    sys.exit(1)

print(f"  Loaded {len(data)} total records from JSON")

# Extract destinations with coordinates from JSON
destinations_with_coords = {}
for item in data:
    if item.get('model') == 'recommendation.destination':
        fields = item.get('fields', {})
        pname = fields.get('pName')
        lat = fields.get('latitude')
        lon = fields.get('longitude')
        
        if pname and lat is not None and lon is not None:
            destinations_with_coords[pname] = (lat, lon)

print(f"  Extracted {len(destinations_with_coords)} destinations with coordinates from JSON")

# Restore the JSON coordinates (these are 100% original)
restored = 0
for json_name, (lat, lon) in destinations_with_coords.items():
    try:
        dest = Destination.objects.filter(pName__iexact=json_name).first()
        if dest:
            dest.latitude = lat
            dest.longitude = lon
            dest.save()
            restored += 1
    except Exception as e:
        pass

print(f"\n[SUCCESS] Restored {restored} destinations from JSON backup (exact name match)")
with_coords_after_restore = Destination.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).count()
print(f"  Total with coordinates: {with_coords_after_restore}")

# =========================
# STEP 3: FUZZY MATCH WITH STRICTER THRESHOLD (0.60+)
# =========================

print("\n" + "=" * 70)
print("STEP 3: FUZZY MATCHING WITH STRICTER THRESHOLD (0.60+)")
print("=" * 70)

print("\n[MATCH] Matching with stricter criteria (threshold = 0.60)...")
updated = 0
not_found = []

missing = Destination.objects.filter(latitude__isnull=True) | Destination.objects.filter(longitude__isnull=True)
total_missing = missing.count()

print(f"  Processing {total_missing} destinations with missing coordinates...\n")

for idx, dest in enumerate(missing, 1):
    best_match = None
    best_score = 0.60  # STRICT THRESHOLD - only high confidence matches
    
    for json_name, coords in destinations_with_coords.items():
        # Strategy 1: Direct similarity (with preprocessing)
        sim_score = similarity(dest.pName, json_name)
        
        # Strategy 2: Word overlap (catches partial matches)
        overlap_score = word_overlap(dest.pName, json_name)
        
        # Combined score: weight both approaches
        combined_score = (sim_score * 0.7) + (overlap_score * 0.3)
        
        if combined_score > best_score:
            best_score = combined_score
            best_match = (json_name, coords)
    
    if best_match:
        json_name, (lat, lon) = best_match
        dest.latitude = lat
        dest.longitude = lon
        dest.save()
        
        if idx % 100 == 0 or idx == 1:
            print(f"[{idx}/{total_missing}] OK: {dest.pName} -> {json_name} [{best_score:.2f}]")
        updated += 1
    else:
        not_found.append(dest.pName)

print(f"\n[SUCCESS] Updated {updated} destinations with fuzzy matching (0.60+ threshold)")
print(f"[STILL MISSING] {len(not_found)} destinations with no confident match")

# =========================
# FINAL VERIFICATION
# =========================

print("\n" + "=" * 70)
print("FINAL VERIFICATION")
print("=" * 70)

total_final = Destination.objects.count()
with_coords_final = Destination.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).count()
without_coords = total_final - with_coords_final
coverage = (with_coords_final / total_final * 100) if total_final > 0 else 0

print(f"\nFinal state:")
print(f"  Total destinations: {total_final}")
print(f"  With coordinates: {with_coords_final}")
print(f"  Missing coordinates: {without_coords}")
print(f"  Coverage: {coverage:.1f}%")

print(f"\nComparison:")
print(f"  Started with: {with_coords_before}")
print(f"  Ended with: {with_coords_final}")
print(f"  Net change: {with_coords_final - with_coords_before:+d}")

if not_found:
    print(f"\nSample unmatched destinations (first 20):")
    for name in not_found[:20]:
        print(f"  - {name}")

print("\n" + "=" * 70)
print("CLEANUP COMPLETE - Ready for Nominatim API for remaining destinations")
print("=" * 70)
