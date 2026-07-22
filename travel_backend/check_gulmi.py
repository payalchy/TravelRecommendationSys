#!/usr/bin/env python
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from recommendation.models import Destination

# Check the problematic destination
dest = Destination.objects.filter(pName__icontains='Gulmi Durbar').first()
if dest:
    print(f"Destination: {dest.pName}")
    print(f"Province: {dest.province}")
    print(f"Coordinates: ({dest.latitude}, {dest.longitude})")
    if dest.latitude is None or dest.longitude is None:
        print("Status: ✓ COORDINATES CLEARED (will show 100 km default)")
    else:
        print(f"Status: Has coordinates")
else:
    print("Gulmi Durbar Area not found in database")
