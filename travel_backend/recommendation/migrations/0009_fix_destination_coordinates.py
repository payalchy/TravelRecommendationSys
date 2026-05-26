# Generated migration to fix destination coordinates
# Run with: python manage.py migrate

from django.db import migrations

def fix_coordinates(apps, schema_editor):
    """Fix destination coordinates with accurate values from Google Maps"""
    Destination = apps.get_model('recommendation', 'Destination')
    
    # Accurate coordinates for major destinations in Nepal
    coordinates_map = {
        'thamel': {'lat': 27.7126, 'lon': 85.3109},
        'chobhar gorge': {'lat': 27.6804, 'lon': 85.3186},
        'tokha': {'lat': 27.7403, 'lon': 85.3372},
        'simraungadh fort': {'lat': 27.6262, 'lon': 85.4134},
        'vajrayogini temple pharping': {'lat': 27.6143, 'lon': 85.2861},
    }
    
    updated_count = 0
    for dest in Destination.objects.all():
        name_lower = dest.pName.lower().strip() if dest.pName else ""
        
        # Find matching coordinates
        for key, coord in coordinates_map.items():
            if key in name_lower or name_lower in key:
                dest.latitude = coord['lat']
                dest.longitude = coord['lon']
                dest.save()
                updated_count += 1
                print(f"✓ Updated {dest.pName}: ({coord['lat']}, {coord['lon']})")
                break

def reverse_coordinates(apps, schema_editor):
    """Reverse the coordinate fix (optional)"""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('recommendation', '0008_destination_city'),
    ]

    operations = [
        migrations.RunPython(fix_coordinates, reverse_coordinates),
    ]
