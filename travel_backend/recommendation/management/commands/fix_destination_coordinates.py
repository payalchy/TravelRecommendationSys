from django.core.management.base import BaseCommand
from recommendation.models import Destination
import time


class Command(BaseCommand):
    help = 'Auto-populate missing latitude/longitude for all destinations (with rate limiting)'

    def handle(self, *args, **options):
        # Find all destinations with missing coordinates
        missing = Destination.objects.filter(
            latitude__isnull=True
        ) | Destination.objects.filter(
            longitude__isnull=True
        )
        
        count = missing.count()
        self.stdout.write(f"Found {count} destinations with missing coordinates\n")
        self.stdout.write("Processing with 1.5 second delay between requests to avoid rate limiting...\n")
        
        success = 0
        failed = 0
        skipped = 0
        
        for idx, dest in enumerate(missing, 1):
            self.stdout.write(f"[{idx}/{count}] Processing: {dest.pName}...", ending=' ')
            
            # This triggers save() which calls _fetch_coordinates_from_nominatim()
            try:
                dest.save()
                
                if dest.latitude and dest.longitude:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ ({dest.latitude:.4f}, {dest.longitude:.4f})"
                        )
                    )
                    success += 1
                else:
                    self.stdout.write(self.style.WARNING("✗ No coordinates found"))
                    failed += 1
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\n\nInterrupted by user"))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error: {str(e)[:50]}"))
                failed += 1
            
            # Rate limiting: 1.5 second delay between requests
            if idx < count:
                time.sleep(1.5)
        
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(self.style.SUCCESS(f"✓ Success: {success}"))
        self.stdout.write(self.style.ERROR(f"✗ Failed: {failed}"))
        total_processed = success + failed
        self.stdout.write(f"\nProcessed {total_processed} of {count} destinations")
        self.stdout.write(f"Progress: {(total_processed/count)*100:.1f}%")
