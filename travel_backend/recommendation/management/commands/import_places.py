import os
import pandas as pd
from django.conf import settings
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from recommendation.models import Destination

class Command(BaseCommand): 
    help = 'Import places from Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='nepal_destination_all.xlsx',
            help='Path to the Excel file to import destinations from',
        )

    def handle(self, *args, **options):
        # Clear old destination data
        Destination.objects.all().delete()

        file_path = options['file']
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(os.path.join(settings.BASE_DIR, file_path))

        if not os.path.exists(file_path):
            raise CommandError(f'Excel file not found: {file_path}')

        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            p_name = str(row['pName']).strip() if pd.notna(row.get('pName')) else ''
            province = str(row.get('province', '')).strip() if pd.notna(row.get('province')) else ''

            if not p_name:
                continue

            Destination.objects.create(
                pName=p_name,
                province=province,
                culture=row.get('culture', 0) if pd.notna(row.get('culture')) else 0,
                adventure=row.get('adventure', 0) if pd.notna(row.get('adventure')) else 0,
                wildlife=row.get('wildlife', 0) if pd.notna(row.get('wildlife')) else 0,
                sightseeing=row.get('sightseeing', 0) if pd.notna(row.get('sightseeing')) else 0,
                history=row.get('history', 0) if pd.notna(row.get('history')) else 0,
                tags=row.get('tags', '') if pd.notna(row.get('tags')) else '',
            )

        self.stdout.write(self.style.SUCCESS('Data imported successfully!'))