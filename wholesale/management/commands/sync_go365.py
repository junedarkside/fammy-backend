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
            '--periods-only',
            action='store_true',
            help='Sync only periods for existing tours'
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
        if options.get('setup_provider'):
            self._setup_provider(options.get('setup_provider'))
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
        if options.get('test_connection'):
            self._test_connection(api_service)
            return

        # Set language if specified
        if options.get('language', 'en') != 'en':
            api_service.set_language(options.get('language', 'en'))

        # Search functionality
        if options.get('search'):
            self._search_tours(api_service, options)
            return

        # Use multi-provider sync service
        sync_service = MultiProviderSyncService()

        try:
            if options.get('countries_only'):
                self._sync_countries_only(api_service)
            elif options.get('tours_only'):
                self._sync_tours_only(api_service, options)
            elif options.get('periods_only'):
                self._sync_periods_only(api_service, sync_service, provider, options)
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
                page=options.get('page', 1),
                limit=options.get('limit', 10)
            )

            if results:
                # Extract data array if search returns dict with status/data
                if isinstance(results, dict) and 'data' in results:
                    results = results['data']

                self.stdout.write(
                    self.style.SUCCESS(f'Found {len(results)} tours')
                )
                for i, tour in enumerate(results[:5], 1):  # Show first 5 results
                    name = tour.get('tour_name', 'No name')
                    tour_id = tour.get('tour_id', tour.get('id', 'No ID'))
                    price = tour.get('tour_price_start', 'No price')
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
        from wholesale.models import Country
        from django.db import transaction

        try:
            self.stdout.write('Fetching countries from Go365 API...')
            countries = api_service.get_countries()

            if countries:
                # Extract data array if response contains status/data
                if isinstance(countries, dict) and 'data' in countries:
                    countries = countries['data']

                self.stdout.write(
                    self.style.SUCCESS(f'✓ Retrieved {len(countries)} countries')
                )

                # Get provider
                provider = Provider.objects.get(code='go365')

                created_count = 0
                updated_count = 0

                for country_data in countries:
                    try:
                        with transaction.atomic():
                            name_en = country_data.get('country_name_en', country_data.get('country_name', ''))
                            name_th = country_data.get('country_name_th', '')
                            code_2 = country_data.get('country_code_2', '')
                            code_3 = country_data.get('country_code_3', '')

                            # Skip countries without valid codes
                            if not code_2 and not code_3:
                                self.stdout.write(
                                    self.style.WARNING(f'Skipping country {name_en}: No country code provided')
                                )
                                continue

                            # Extract city data if available
                            cities = country_data.get('city', [])

                            country, created = Country.objects.update_or_create(
                                provider=provider,
                                provider_code=code_2 or code_3,
                                defaults={
                                    'name': name_en,
                                    'normalized_name': name_en.lower().strip() if name_en else '',
                                    'iso_code': code_3 or '',  # Use empty string instead of None
                                    'content': name_th,  # Store Thai name in content field
                                    'locations': cities if cities else None,
                                }
                            )

                            if created:
                                created_count += 1
                            else:
                                updated_count += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'ERROR syncing country {name_en}: {str(e)}')
                        )
                        import traceback
                        self.stdout.write(traceback.format_exc())

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Countries sync completed - Created: {created_count}, Updated: {updated_count}'
                    )
                )

                # Show sample
                for country in countries[:3]:
                    name = country.get('country_name_en', country.get('country_name', 'No name'))
                    code = country.get('country_code_2', country.get('country_code_3', 'No code'))
                    product_count = country.get('product_count', 0)
                    self.stdout.write(f'  - {name} ({code}) - {product_count} tours')
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
            page = options.get('page', 1)
            limit = options.get('limit', 10)
            self.stdout.write(f'Fetching tours (page {page}, limit {limit})...')
            tours = api_service.get_program_tours(
                page=page,
                limit=limit
            )

            if tours:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Retrieved {len(tours)} tours')
                )
                # TODO: Process tours into database when models are ready
                for i, tour in enumerate(tours[:3], 1):  # Show sample
                    name = tour.get('tour_name', 'No name')
                    tour_id = tour.get('tour_id', tour.get('id', 'No ID'))
                    price = tour.get('tour_price_start', 'No price')
                    # Get first country name from tour_country array
                    countries = tour.get('tour_country', [])
                    country = countries[0].get('country_name_en', 'No country') if countries else 'No country'
                    self.stdout.write(f'  {i}. {name} - {country} (ID: {tour_id}, Price: {price})')
            else:
                self.stdout.write(
                    self.style.WARNING('No tours retrieved')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Tours sync failed: {e}')
            )

    def _sync_periods_only(self, api_service, sync_service, provider, options):
        """Sync periods for existing tours"""
        from wholesale.models import ProgramTour, Period
        from wholesale.api_service import APIServiceFactory
        from django.db import transaction

        try:
            # Get existing Go365 tours
            tours = ProgramTour.objects.filter(provider=provider)

            if not tours.exists():
                self.stdout.write(self.style.WARNING('No Go365 tours found. Run full sync first.'))
                return

            self.stdout.write(f'Found {tours.count()} existing tours')

            mapper = APIServiceFactory.create_mapper(provider)
            total_created = 0
            total_updated = 0

            for tour in tours:
                try:
                    tour_id = tour.external_id
                    periods_data = api_service.get_tour_periods(tour_id)

                    if periods_data:
                        self.stdout.write(f"Tour {tour.code}: {len(periods_data)} periods")

                        for period_data in periods_data:
                            with transaction.atomic():
                                period_fields = mapper.map_period_data(period_data, tour)
                                period_fields.pop('provider', None)

                                period, created = Period.objects.update_or_create(
                                    provider=provider,
                                    external_id=period_fields['external_id'],
                                    defaults={**period_fields, 'program': tour}
                                )

                                if created:
                                    total_created += 1
                                else:
                                    total_updated += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Failed to sync periods for {tour.code}: {e}')
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Periods sync completed - Created: {total_created}, Updated: {total_updated}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Periods sync failed: {e}')
            )

    def _sync_full_provider(self, sync_service: MultiProviderSyncService, provider: Provider):
        """Sync all data for the provider and save to database"""
        from wholesale.api_service import APIServiceFactory
        from wholesale.models import ProgramTour, Period, Flight, Itinerary
        from django.db import transaction

        try:
            self.stdout.write('Starting full sync for Go365 provider...')

            # Create service and mapper
            service = APIServiceFactory.create_service(provider)
            mapper = APIServiceFactory.create_mapper(provider)

            # Fetch tours
            tours = service.get_program_tours(limit=50)  # Fetch first 50 tours

            if not tours:
                self.stdout.write(self.style.WARNING('No tours found'))
                return

            self.stdout.write(f"Found {len(tours)} tour(s)")

            # Sync tours and periods
            tours_created = 0
            tours_updated = 0

            for tour_data in tours:
                try:
                    with transaction.atomic():
                        # Map and save tour
                        tour_fields = mapper.map_tour_data(tour_data)
                        tour_fields.pop('provider', None)  # Remove as it's in lookup

                        tour, created = ProgramTour.objects.update_or_create(
                            provider=provider,
                            external_id=str(tour_data.get('tour_id', '')),
                            defaults=tour_fields
                        )

                        if created:
                            tours_created += 1
                        else:
                            tours_updated += 1

                        # Sync itineraries for this tour
                        tour_id = tour_data.get('tour_id')
                        if tour_id:
                            try:
                                # Fetch tour details for itinerary
                                tour_details = service.get_program_tour_details(tour_id)

                                if tour_details:
                                    daily_itineraries = tour_details.get('tour_daily', [])

                                    if daily_itineraries:
                                        itineraries_created = 0
                                        itineraries_updated = 0

                                        for itinerary_data in daily_itineraries:
                                            try:
                                                itinerary_fields = mapper.map_itinerary_data(itinerary_data, tour)

                                                # Validate required fields
                                                if not itinerary_fields.get('day'):
                                                    self.stdout.write(
                                                        self.style.WARNING(f'    Skipping itinerary: Missing day number')
                                                    )
                                                    continue

                                                if not itinerary_fields.get('external_id'):
                                                    self.stdout.write(
                                                        self.style.WARNING(f'    Skipping itinerary day {itinerary_data.get("day_num")}: Missing external_id')
                                                    )
                                                    continue

                                                itinerary_fields.pop('provider', None)
                                                itinerary_fields.pop('program_id', None)

                                                itinerary, itin_created = Itinerary.objects.update_or_create(
                                                    provider=provider,
                                                    external_id=itinerary_fields['external_id'],
                                                    defaults={**itinerary_fields, 'program': tour}
                                                )

                                                if itin_created:
                                                    itineraries_created += 1
                                                else:
                                                    itineraries_updated += 1

                                            except Exception as e:
                                                self.stdout.write(
                                                    self.style.ERROR(f'    ERROR syncing itinerary day {itinerary_data.get("day_num")}: {str(e)}')
                                                )
                                                import traceback
                                                self.stdout.write(traceback.format_exc())

                                        if itineraries_created or itineraries_updated:
                                            self.stdout.write(
                                                self.style.SUCCESS(
                                                    f"  ✓ Itineraries: {itineraries_created} created, {itineraries_updated} updated"
                                                )
                                            )

                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f'  Failed to fetch itineraries for tour {tour_id}: {e}')
                                )

                        # Sync periods for this tour
                        if tour_id:
                            try:
                                # Fetch periods from API
                                periods_data = service.get_tour_periods(tour_id)

                                if periods_data:
                                    self.stdout.write(f"  Syncing {len(periods_data)} periods for tour {tour_id}")

                                    periods_created = 0
                                    periods_updated = 0
                                    flights_created = 0
                                    flights_updated = 0

                                    for period_data in periods_data:
                                        try:
                                            # Map period data
                                            period_fields = mapper.map_period_data(period_data, tour)
                                            period_fields.pop('provider', None)

                                            # Create or update period
                                            period, created = Period.objects.update_or_create(
                                                provider=provider,
                                                external_id=period_fields['external_id'],
                                                defaults={**period_fields, 'program': tour}
                                            )

                                            if created:
                                                periods_created += 1
                                            else:
                                                periods_updated += 1

                                            # Sync flights for this period
                                            flights_data = period_data.get('period_flight', [])
                                            if flights_data:
                                                for flight_data in flights_data:
                                                    try:
                                                        flight_fields = mapper.map_flight_data(flight_data, period)

                                                        # Validate required fields
                                                        if not flight_fields.get('flight_no'):
                                                            self.stdout.write(
                                                                self.style.WARNING(f'      Skipping flight {flight_data.get("flight_id")}: Missing flight_no')
                                                            )
                                                            continue

                                                        flight_fields.pop('provider', None)
                                                        flight_fields.pop('period_id', None)

                                                        # Use provider + period + flight_no as unique identifier
                                                        flight, flight_created = Flight.objects.update_or_create(
                                                            provider=provider,
                                                            period=period,
                                                            flight_no=flight_fields['flight_no'],
                                                            defaults=flight_fields
                                                        )

                                                        if flight_created:
                                                            flights_created += 1
                                                        else:
                                                            flights_updated += 1

                                                    except Exception as e:
                                                        self.stdout.write(
                                                            self.style.ERROR(f'      ERROR syncing flight {flight_data.get("flight_id")}: {str(e)}')
                                                        )
                                                        import traceback
                                                        self.stdout.write(traceback.format_exc())

                                        except Exception as e:
                                            self.stdout.write(
                                                self.style.WARNING(f'    Failed to sync period {period_data.get("period_id")}: {e}')
                                            )

                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"  ✓ Periods: {periods_created} created, {periods_updated} updated"
                                        )
                                    )
                                    if flights_created or flights_updated:
                                        self.stdout.write(
                                            self.style.SUCCESS(
                                                f"  ✓ Flights: {flights_created} created, {flights_updated} updated"
                                            )
                                        )

                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f'  Failed to fetch periods for tour {tour_id}: {e}')
                                )

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Failed to sync tour {tour_data.get("tour_id")}: {e}')
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Sync completed - Tours created: {tours_created}, updated: {tours_updated}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Full sync failed: {e}')
            )