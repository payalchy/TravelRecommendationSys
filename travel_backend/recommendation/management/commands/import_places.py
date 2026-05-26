import os
import pandas as pd
from datetime import datetime
from django.conf import settings
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from recommendation.models import Destination, TravelPackage, Recommendation, CostComparison, PackageItinerary

class Command(BaseCommand): 
    help = 'Import places from Excel file (clears existing data first)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='nepal_destination_all.xlsx',
            help='Path to the Excel file to import destinations from',
        )
        parser.add_argument(
            '--no-clear',
            action='store_true',
            help='Do not clear existing data before importing',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(os.path.join(settings.BASE_DIR, file_path))

        if not os.path.exists(file_path):
            raise CommandError(f'Excel file not found: {file_path}')

        # Clear old data unless --no-clear is specified
        if not options['no_clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            CostComparison.objects.all().delete()
            Recommendation.objects.all().delete()
            PackageItinerary.objects.all().delete()
            TravelPackage.objects.all().delete()
            deleted_count, _ = Destination.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {deleted_count} destinations'))

        # Read Excel file
        self.stdout.write(self.style.WARNING(f'Reading {file_path}...'))
        df = pd.read_excel(file_path)
        self.stdout.write(f'Total rows in file: {len(df)}')

        # Prepare destination objects for bulk creation
        destinations_to_create = []

        for idx, row in df.iterrows():
            p_name = str(row['pName']).strip() if pd.notna(row.get('pName')) else ''
            
            if not p_name:
                continue

            province = str(row.get('province', '')).strip() if pd.notna(row.get('province')) else ''
            city = str(row.get('city', '')).strip() if pd.notna(row.get('city')) else ''

            destination = Destination(
                pName=p_name,
                province=province,
                city=city,
                culture=float(row.get('culture', 0)) if pd.notna(row.get('culture')) else 0,
                adventure=float(row.get('adventure', 0)) if pd.notna(row.get('adventure')) else 0,
                wildlife=float(row.get('wildlife', 0)) if pd.notna(row.get('wildlife')) else 0,
                sightseeing=float(row.get('sightseeing', 0)) if pd.notna(row.get('sightseeing')) else 0,
                history=float(row.get('history', 0)) if pd.notna(row.get('history')) else 0,
                tags=str(row.get('tags', '')) if pd.notna(row.get('tags')) else '',
            )
            destinations_to_create.append(destination)

        self.stdout.write(f'Prepared {len(destinations_to_create)} destinations for import')

        # Use bulk_create for efficient insertion (bypasses save() method, no coordinate fetching)
        batch_size = 500
        created_count = 0

        self.stdout.write(self.style.WARNING('Importing destinations...'))
        for i in range(0, len(destinations_to_create), batch_size):
            batch = destinations_to_create[i:i+batch_size]
            # Use ignore_conflicts to skip duplicates
            Destination.objects.bulk_create(batch, ignore_conflicts=True)
            created_count += len(batch)
            progress = (created_count / len(destinations_to_create)) * 100
            self.stdout.write(f'Progress: {created_count}/{len(destinations_to_create)} ({progress:.1f}%)')

        # Verify final count
        final_count = Destination.objects.count()
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Import completed!'))
        self.stdout.write(f'Total destinations in database: {final_count}')
        
        if final_count == len(destinations_to_create):
            self.stdout.write(self.style.SUCCESS('✓ All destinations imported successfully!'))