from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wholesale.models import Provider, ProgramTour, Period
from wholesale.api_service import APIServiceFactory


class Command(BaseCommand):
    help = 'Synchronize CheckIn Group tour data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tours-only',
            action='store_true',
            help='Sync only program tours (skip periods)',
        )
        parser.add_argument(
            '--tour-id',
            type=int,
            help='Sync specific tour by ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving',
        )
        parser.add_argument(
            '--check-updates',
            action='store_true',
            help='Check for updates without syncing',
        )

    def handle(self, *args, **options):
        try:
            provider = Provider.objects.get(code='checkingroup')
        except Provider.DoesNotExist:
            raise CommandError(
                'CheckIn Group provider not found. '
                'Please create a Provider with code="checkingroup" first.'
            )

        service = APIServiceFactory.create_service(provider)
        mapper = APIServiceFactory.create_mapper(provider)

        # Test connection
        try:
            about = service.get_about()
            self.stdout.write(
                f"Connected to: {about.get('company_name', 'CheckIn Group')}"
            )
        except Exception as e:
            raise CommandError(f'Failed to connect to CheckIn Group API: {str(e)}')

        # Fetch tours
        if options['tour_id']:
            tours = [service.get_program_tour_details(options['tour_id'])]
        else:
            tours = service.get_program_tours()

        if not tours:
            self.stdout.write(self.style.WARNING('No tours found'))
            return

        self.stdout.write(f"Found {len(tours)} tour(s)")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be saved'))
            return

        # Sync tours and periods
        tours_created = 0
        tours_updated = 0
        periods_created = 0
        periods_updated = 0

        for tour_data in tours:
            with transaction.atomic():
                # Map and save tour
                tour_fields = mapper.map_tour_data(tour_data)
                # Remove provider from tour_fields as it's already set in lookup
                tour_fields.pop('provider', None)
                tour, created = ProgramTour.objects.update_or_create(
                    provider=provider,
                    external_id=tour_fields['external_id'],
                    defaults=tour_fields
                )

                if created:
                    tours_created += 1
                else:
                    tours_updated += 1

                # Sync periods if not tours-only
                if not options['tours_only'] and 'periods' in tour_data:
                    for period_data in tour_data['periods']:
                        period_fields = mapper.map_period_data(period_data, tour)
                        # Remove provider from period_fields as it's already set in lookup
                        period_fields.pop('provider', None)
                        period, created = Period.objects.update_or_create(
                            provider=provider,
                            external_id=period_fields['external_id'],
                            defaults={**period_fields, 'program': tour}
                        )

                        if created:
                            periods_created += 1
                        else:
                            periods_updated += 1

        # Display results
        self.stdout.write(self.style.SUCCESS(f'Tours created: {tours_created}'))
        self.stdout.write(self.style.SUCCESS(f'Tours updated: {tours_updated}'))
        self.stdout.write(self.style.SUCCESS(f'Periods created: {periods_created}'))
        self.stdout.write(self.style.SUCCESS(f'Periods updated: {periods_updated}'))
        self.stdout.write(self.style.SUCCESS('CheckIn Group sync complete!'))
