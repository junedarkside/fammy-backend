from django.core.management.base import BaseCommand
from django.utils import timezone
from wholesale.models import Provider
from wholesale.services import MultiProviderSyncService, ProviderRegistrationService
from wholesale.api_service import Go365APIService


class Command(BaseCommand):
    help = 'Sync data from Go365 Travel API using the multi-provider system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup-provider',
            type=str,
            help='Setup Go365 provider with given API key'
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test connection to Go365 API'
        )
        parser.add_argument(
            '--countries-only',
            action='store_true',
            help='Sync only countries data'
        )
        parser.add_argument(
            '--tours-only',
            action='store_true',
            help='Sync only tours data'
        )
        parser.add_argument(
            '--language',
            type=str,
            choices=['th', 'en', 'ch'],
            default='en',
            help='API response language (default: en)'
        )
        parser.add_argument(
            '--search',
            type=str,
            help='Search tours with specific query'
        )
        parser.add_argument(
            '--page',
            type=int,
            default=1,
            help='Page number for pagination (default: 1)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Results per page (default: 10)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Go365 sync started at {timezone.now()}')
        )

        # Setup provider if requested
        if options['setup_provider']:
            self._setup_provider(options['setup_provider'])
            return

        # Get Go365 provider
        try:
            provider = Provider.objects.get(code='go365')
        except Provider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Go365 provider not found. Use --setup-provider to create it.')
            )
            return

        # Create API service
        try:
            api_service = Go365APIService(provider)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create Go365 API service: {e}')
            )
            return

        # Test connection if requested
        if options['test_connection']:
            self._test_connection(api_service)
            return

        # Set language if specified
        if options['language'] != 'en':
            api_service.set_language(options['language'])

        # Search functionality
        if options['search']:
            self._search_tours(api_service, options)
            return

        # Use multi-provider sync service
        sync_service = MultiProviderSyncService()

        try:
            if options['countries_only']:
                self._sync_countries_only(api_service)
            elif options['tours_only']:
                self._sync_tours_only(api_service, options)
            else:
                self._sync_full_provider(sync_service, provider)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Sync failed: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Go365 sync completed at {timezone.now()}')
        )

    def _setup_provider(self, api_key: str):
        """Setup Go365 provider with API key"""
        try:
            provider = ProviderRegistrationService.register_go365_provider(
                name='Go365 Travel',
                code='go365',
                base_url='https://www.go365travel.com',
                api_key=api_key,
                default_language='en'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created Go365 provider: {provider.name}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to setup provider: {e}')
            )

    def _test_connection(self, api_service: Go365APIService):
        """Test connection to Go365 API"""
        try:
            if api_service.test_connection():
                self.stdout.write(
                    self.style.SUCCESS('✓ Connection to Go365 API successful')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Connection to Go365 API failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Connection test error: {e}')
            )

    def _search_tours(self, api_service: Go365APIService, options: dict):
        """Search tours with specific query"""
        try:
            self.stdout.write(f"Searching tours for: '{options['search']}'")
            results = api_service.search_tours(
                search_query=options['search'],
                page=options['page'],
                limit=options['limit']
            )

            if results:
                self.stdout.write(
                    self.style.SUCCESS(f'Found {len(results)} tours')
                )
                for i, tour in enumerate(results[:5], 1):  # Show first 5 results
                    name = tour.get('name', 'No name')
                    tour_id = tour.get('tour_id', tour.get('id', 'No ID'))
                    price = tour.get('price', 'No price')
                    self.stdout.write(f'  {i}. {name} (ID: {tour_id}, Price: {price})')
            else:
                self.stdout.write(
                    self.style.WARNING('No tours found')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Search failed: {e}')
            )

    def _sync_countries_only(self, api_service: Go365APIService):
        """Sync only countries data"""
        try:
            self.stdout.write('Fetching countries from Go365 API...')
            countries = api_service.get_countries()

            if countries:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Retrieved {len(countries)} countries')
                )
                # TODO: Process countries into database when models are ready
                for country in countries[:3]:  # Show sample
                    name = country.get('name', 'No name')
                    code = country.get('code', 'No code')
                    self.stdout.write(f'  - {name} ({code})')
            else:
                self.stdout.write(
                    self.style.WARNING('No countries retrieved')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Countries sync failed: {e}')
            )

    def _sync_tours_only(self, api_service: Go365APIService, options: dict):
        """Sync only tours data"""
        try:
            self.stdout.write(f'Fetching tours (page {options["page"]}, limit {options["limit"]})...')
            tours = api_service.get_program_tours(
                page=options['page'],
                limit=options['limit']
            )

            if tours:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Retrieved {len(tours)} tours')
                )
                # TODO: Process tours into database when models are ready
                for i, tour in enumerate(tours[:3], 1):  # Show sample
                    name = tour.get('name', 'No name')
                    tour_id = tour.get('tour_id', tour.get('id', 'No ID'))
                    price = tour.get('price', 'No price')
                    country = tour.get('country', 'No country')
                    self.stdout.write(f'  {i}. {name} - {country} (ID: {tour_id}, Price: {price})')
            else:
                self.stdout.write(
                    self.style.WARNING('No tours retrieved')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Tours sync failed: {e}')
            )

    def _sync_full_provider(self, sync_service: MultiProviderSyncService, provider: Provider):
        """Sync all data for the provider using multi-provider service"""
        try:
            self.stdout.write('Starting full sync for Go365 provider...')
            result = sync_service.sync_provider(provider)

            if result['status'] == 'success':
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Sync completed - Countries: {result["countries"]}, '
                        f'Tours: {result["tours"]}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Sync failed - Status: {result["status"]}, '
                        f'Error: {result.get("error", "Unknown error")}'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Full sync failed: {e}')
            )