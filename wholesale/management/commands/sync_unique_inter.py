from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from wholesale.models import Provider, RawVendorData, ProgramTour, Period, ProviderCategory
from wholesale.api_service import APIServiceFactory
from wholesale.data_sync_service import (
    map_unique_inter_tour_data,
    map_unique_inter_period_data,
    get_or_create_country_for_unique_inter
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync data from Unique Inter Wholesale API (two-stage: fetch raw → process)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fetch-only',
            action='store_true',
            help='Only fetch and store raw data, do not process'
        )
        parser.add_argument(
            '--process-only',
            action='store_true',
            help='Only process existing raw data, do not fetch'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Sync specific category only (e.g., 59, 60, 64)'
        )
        parser.add_argument(
            '--provider-code',
            type=str,
            default='unique_inter',
            help='Provider code (default: unique_inter)'
        )

    def handle(self, *args, **options):
        provider_code = options['provider_code']

        try:
            provider = Provider.objects.get(code=provider_code)
        except Provider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Provider "{provider_code}" not found. '
                    f'Please create it first.'
                )
            )
            return

        # Stage 1: Fetch raw data (unless --process-only)
        if not options['process_only']:
            self.fetch_raw_data(provider, options.get('category'))

        # Stage 2: Process raw data (unless --fetch-only)
        if not options['fetch_only']:
            self.process_raw_data(provider)

    def fetch_raw_data(self, provider, category_filter=None):
        """Fetch and store raw data from API"""
        self.stdout.write(
            self.style.WARNING('═' * 60)
        )
        self.stdout.write(
            self.style.WARNING('STAGE 1: Fetching raw data from Unique Inter API')
        )
        self.stdout.write(
            self.style.WARNING('═' * 60)
        )

        api_service = APIServiceFactory.create_service(provider)

        # Get categories to sync
        if category_filter:
            categories = ProviderCategory.objects.filter(
                provider=provider,
                category_id=category_filter
            )
        else:
            categories = ProviderCategory.objects.filter(
                provider=provider,
                is_active=True
            ).order_by('-priority', 'name')

        if not categories.exists():
            self.stdout.write(
                self.style.ERROR(
                    'No categories configured. Run: '
                    'python manage.py sync_unique_inter_categories'
                )
            )
            return

        total_stored = 0

        for category in categories:
            self.stdout.write(
                f'\nFetching category: {category.name} ({category.category_id})...'
            )

            raw_responses = api_service.get_tour_packages_by_category(
                category.category_id
            )

            if not raw_responses:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ✗ No data returned for category {category.category_id}'
                    )
                )
                continue

            category_count = 0

            for raw_item in raw_responses:
                product_code = raw_item.get('ProductCode', '')

                if not product_code:
                    logger.warning(f"Skipping item with no ProductCode: {raw_item}")
                    continue

                RawVendorData.objects.update_or_create(
                    provider=provider,
                    external_id=product_code,
                    category=category.category_id,
                    defaults={
                        'raw_json': raw_item,
                        'processed': False,
                        'fetched_at': timezone.now(),
                        'error_message': ''
                    }
                )
                category_count += 1

            total_stored += category_count

            # Update category metadata
            category.total_tours = category_count
            category.last_synced = timezone.now()
            category.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ Stored {category_count} raw records'
                )
            )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Raw data fetch completed: {total_stored} total records stored'
            )
        )

    @transaction.atomic
    def process_raw_data(self, provider):
        """Process raw data and create ProgramTour/Period records"""
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING('═' * 60)
        )
        self.stdout.write(
            self.style.WARNING('STAGE 2: Processing raw data into models')
        )
        self.stdout.write(
            self.style.WARNING('═' * 60)
        )

        # Get unprocessed records
        unprocessed = RawVendorData.objects.filter(
            provider=provider,
            processed=False
        ).select_related('provider')

        if not unprocessed.exists():
            self.stdout.write(
                self.style.WARNING('No unprocessed raw data found')
            )
            return

        self.stdout.write(
            f'\nProcessing {unprocessed.count()} raw records...\n'
        )

        # Group by mainid (tour program)
        tours_by_mainid = {}
        for raw_record in unprocessed:
            mainid = raw_record.raw_json.get('mainid')
            if not mainid:
                logger.warning(
                    f"Skipping raw record {raw_record.id} with no mainid"
                )
                raw_record.error_message = 'No mainid in raw data'
                raw_record.save()
                continue

            if mainid not in tours_by_mainid:
                tours_by_mainid[mainid] = []
            tours_by_mainid[mainid].append(raw_record)

        tours_created = 0
        tours_updated = 0
        periods_created = 0
        periods_updated = 0
        errors = 0

        for mainid, raw_records in tours_by_mainid.items():
            try:
                # Create/update tour from first record
                first_raw = raw_records[0].raw_json
                tour_data = map_unique_inter_tour_data(first_raw)
                external_id = tour_data.pop('external_id')

                if not external_id:
                    raise ValueError(f"No external_id mapped for mainid {mainid}")

                # Get or create Country from extracted country_name
                country_name = tour_data.get('country_name', '')
                country_obj = get_or_create_country_for_unique_inter(
                    provider,
                    country_name
                )
                tour_data['country'] = country_obj

                tour, tour_created = ProgramTour.objects.update_or_create(
                    provider=provider,
                    external_id=external_id,
                    defaults=tour_data
                )

                if tour_created:
                    tours_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created tour: {tour.name} ({tour.code})'
                        )
                    )
                else:
                    tours_updated += 1

                # Process all periods (departures) for this tour
                for raw_record in raw_records:
                    try:
                        period_data = map_unique_inter_period_data(
                            raw_record.raw_json
                        )
                        period_external_id = period_data.pop('external_id')

                        if not period_external_id:
                            raise ValueError(
                                f"No external_id for period in record {raw_record.id}"
                            )

                        period, period_created = Period.objects.update_or_create(
                            provider=provider,
                            external_id=period_external_id,
                            program=tour,
                            defaults=period_data
                        )

                        if period_created:
                            periods_created += 1
                        else:
                            periods_updated += 1

                        # Mark as processed
                        raw_record.processed = True
                        raw_record.processed_at = timezone.now()
                        raw_record.error_message = ''
                        raw_record.save()

                    except Exception as e:
                        logger.error(
                            f"Error processing period {raw_record.external_id}: {e}"
                        )
                        raw_record.error_message = str(e)
                        raw_record.save()
                        errors += 1

            except Exception as e:
                logger.error(f"Error processing tour {mainid}: {e}")
                for raw_record in raw_records:
                    raw_record.error_message = str(e)
                    raw_record.save()
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error processing tour {mainid}: {str(e)}'
                    )
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING('═' * 60)
        )
        self.stdout.write(
            self.style.SUCCESS('PROCESSING COMPLETE')
        )
        self.stdout.write(
            self.style.WARNING('═' * 60)
        )
        self.stdout.write(f'Tours created:  {tours_created}')
        self.stdout.write(f'Tours updated:  {tours_updated}')
        self.stdout.write(f'Periods created: {periods_created}')
        self.stdout.write(f'Periods updated: {periods_updated}')
        if errors > 0:
            self.stdout.write(
                self.style.ERROR(f'Errors: {errors}')
            )

        # Show unique countries summary
        from wholesale.models import Country
        unique_countries = Country.objects.filter(provider=provider).values_list('name', 'iso_code')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Unique Countries in Database:'))
        for country_name, iso_code in unique_countries:
            self.stdout.write(f'  - {country_name} ({iso_code if iso_code else "N/A"})')
        self.stdout.write('')
