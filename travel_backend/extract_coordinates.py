import json
import os
from difflib import SequenceMatcher
from django.core.management import execute_from_command_line
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from recommendation.models import Destination
import re

# Common suffixes to remove for better matching
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
    # Remove numbers and extra spaces
    name = re.sub(r'\d+', '', name)
    # Remove common suffixes
    for suffix in COMMON_SUFFIXES:
        if name.lower().endswith(suffix.lower()):
            name = name[:len(name)-len(suffix)].strip()
            break
    return name.lower().strip()

def similarity(a, b):
    """Calculate string similarity ratio with preprocessing"""
    a_clean = preprocess_name(a)
    b_clean = preprocess_name(b)
    return SequenceMatcher(None, a_clean, b_clean).ratio()

def word_overlap(a, b):
    """Check if key words overlap between two names"""
    a_words = set(preprocess_name(a).split())
    b_words = set(preprocess_name(b).split())
    if not a_words or not b_words:
        return 0
    overlap = len(a_words & b_words)
    return overlap / max(len(a_words), len(b_words))

# Check JSON files for existing coordinates
json_files = ['data_utf8.json', 'full_backup_utf8.json', 'data.json']

destinations_with_coords = {}

for json_file in json_files:
    if os.path.exists(json_file):
        print(f"\n[FILE] Checking {json_file}...")
        try:
            # Try different encodings for BOM
            try:
                with open(json_file, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
            except:
                with open(json_file, 'r', encoding='utf-16') as f:
                    data = json.load(f)
            
            if isinstance(data, list):
                dests = [item for item in data if item.get('model') == 'recommendation.destination']
                print(f"   Found {len(dests)} destinations")
                
                for dest in dests:
                    fields = dest.get('fields', {})
                    pname = fields.get('pName', '').strip()
                    lat = fields.get('latitude')
                    lon = fields.get('longitude')
                    
                    if pname and lat and lon:
                        destinations_with_coords[pname] = (float(lat), float(lon))
                
                print(f"   Extracted {len(destinations_with_coords)} destinations with coordinates")
                break
        except Exception as e:
            print(f"   Error: {str(e)[:80]}")

# Find destinations in DB with missing coordinates
print("\n\n[SEARCH] Checking database for missing coordinates...")
missing = Destination.objects.filter(latitude__isnull=True) | Destination.objects.filter(longitude__isnull=True)
print(f"Total destinations missing coordinates: {missing.count()}")

# Try to match and update with improved fuzzy matching
print("\n[MATCH] Enhanced fuzzy matching (all remaining destinations)...")
updated = 0
not_found = []

missing = Destination.objects.filter(latitude__isnull=True) | Destination.objects.filter(longitude__isnull=True)
total_missing = missing.count()

for idx, dest in enumerate(missing, 1):
    best_match = None
    best_score = 0.50  # LOWERED threshold for more lenient matching
    match_type = None
    
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
            match_type = "fuzzy" if sim_score > overlap_score else "overlap"
    
    if best_match:
        json_name, (lat, lon) = best_match
        dest.latitude = lat
        dest.longitude = lon
        dest.save()
        
        if idx % 50 == 0 or idx == 1:
            print(f"[{idx}/{total_missing}] OK: {dest.pName} -> {json_name} [{best_score:.2f}]")
        updated += 1
    else:
        not_found.append(dest.pName)

print(f"\n[SUCCESS] Updated {updated} destinations from JSON data")
print(f"[FAILED] Could not find matches for {len(not_found)} destinations")
if not_found[:15]:
    print("\nSample not found (first 15):")
    for name in not_found[:15]:
        print(f"  - {name}")
