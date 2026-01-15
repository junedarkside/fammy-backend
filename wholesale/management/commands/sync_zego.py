from django.core.management.base import BaseCommand, CommandError
from wholesale.models import Provider
from wholesale.data_sync_service import DataSyncService


class Command(BaseCommand):
    help = 'Sync data from Zego API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--countries-only',
            action='store_true',
            help='Only sync countries, skip tours',
        )
        parser.add_argument(
            '--tours-only',
            action='store_true',
            help='Only sync tours, skip countries',
        )
        parser.add_argument(
            '--check-updates',
            action='store_true',
            help='Check if there are updates available without syncing',
        )

    def handle(self, *args, **options):
        try:
            # Get Zego provider
            provider = Provider.objects.get(code='zego')
        except Provider.DoesNotExist:
            raise CommandError('Zego provider not found. Please create a Provider with code="zego" first.')

        # Create sync service
        sync_service = DataSyncService(provider)

        # Check for updates
        if options['check_updates']:
            self.stdout.write('Checking for updates...')
            has_updates = sync_service.check_for_updates()
            if has_updates:
                self.stdout.write(self.style.SUCCESS('Updates are available!'))
            else:
                self.stdout.write(self.style.WARNING('No updates available.'))
            return

        # Sync countries
        if not options['tours_only']:
            self.stdout.write('Syncing countries from Zego API...')
            try:
                countries_count = sync_service.sync_countries()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully synced {countries_count} countries.')
                )
            except Exception as e:
                raise CommandError(f'Error syncing countries: {str(e)}')

        # Sync tours
        if not options['countries_only']:
            self.stdout.write('Syncing tours from Zego API...')
            try:
                result = sync_service.sync_program_tours()
                tours_count = result.get('tours_created', 0) if isinstance(result, dict) else 0
                periods_count = result.get('periods_created', 0) if isinstance(result, dict) else 0
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully synced {tours_count} tours and {periods_count} periods.'
                    )
                )
            except Exception as e:
                raise CommandError(f'Error syncing tours: {str(e)}')

        self.stdout.write(self.style.SUCCESS('Zego sync complete!'))
