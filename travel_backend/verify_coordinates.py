import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from recommendation.models import Destination
import math

# Get a destination with coordinates
dests = Destination.objects.filter(latitude__isnull=False, longitude__isnull=False)[:5]

print("[VERIFICATION] Sample destinations with coordinates:\n")
for dest in dests:
    print(f"Destination: {dest.pName}")
    print(f"  Province: {dest.province}")
    print(f"  Coordinates: ({dest.latitude:.4f}, {dest.longitude:.4f})")
    
    # Calculate distance from default user location (Kathmandu)
    user_lat, user_lon = 27.7172, 85.3240
    
    lat_diff = math.radians(dest.latitude - user_lat)
    lon_diff = math.radians(dest.longitude - user_lon)
    
    a = math.sin(lat_diff / 2) ** 2 + math.cos(math.radians(user_lat)) * math.cos(math.radians(dest.latitude)) * math.sin(lon_diff / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = 6371 * c
    
    print(f"  Distance from Kathmandu: {distance_km:.2f} km")
    print()

# Count how many now have coordinates
total_with_coords = Destination.objects.filter(latitude__isnull=False, longitude__isnull=False).count()
total_missing = Destination.objects.count() - total_with_coords

print(f"\n[STATS]")
print(f"Total destinations with coordinates: {total_with_coords}")
print(f"Total destinations missing coordinates: {total_missing}")
print(f"Progress: {(total_with_coords / Destination.objects.count() * 100):.1f}%")
