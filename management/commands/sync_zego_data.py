from django.core.management.base import BaseCommand
from django.utils import timezone
from ...wholesale.models import Provider
from ...wholesale.data_sync_service import DataSyncService


class Command(BaseCommand):
    help = 'Sync data from Zego API to local database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            help='Provider name to sync (if not provided, sync all active providers)'
        )
        parser.add_argument(
            '--countries-only',
            action='store_true',
            help='Sync only countries data'
        )
        parser.add_argument(
            '--tours-only',
            action='store_true',
            help='Sync only program tours data'
        )
        parser.add_argument(
            '--check-updates',
            action='store_true',
            help='Check for updates before syncing'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting data sync at {timezone.now()}')
        )
        
        # Get providers to sync
        if options['provider']:
            try:
                providers = [Provider.objects.get(name=options['provider'])]
            except Provider.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Provider "{options["provider"]}" not found')
                )
                return
        else:
            providers = Provider.objects.all()
        
        for provider in providers:
            self.stdout.write(f'Syncing data for provider: {provider.name}')

            sync_service = DataSyncService(provider)

            # Check for updates if requested
            if options['check_updates']:
                if not sync_service.check_for_updates():
                    self.stdout.write(
                        self.style.WARNING(f'No updates available for {provider.name}')
                    )
                    continue
            
            # Sync countries
            if not options['tours_only']:
                self.stdout.write('Syncing countries...')
                countries_result = sync_service.sync_countries()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Countries - Created: {countries_result["created"]}, '
                        f'Updated: {countries_result["updated"]}, '
                        f'Errors: {countries_result["errors"]}'
                    )
                )
            
            # Sync program tours
            if not options['countries_only']:
                self.stdout.write('Syncing program tours...')
                tours_result = sync_service.sync_program_tours()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Program Tours - Created: {tours_result["created"]}, '
                        f'Updated: {tours_result["updated"]}, '
                        f'Errors: {tours_result["errors"]}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Data sync completed at {timezone.now()}')
        )
