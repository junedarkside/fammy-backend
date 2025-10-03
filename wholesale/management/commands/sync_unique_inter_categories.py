from django.core.management.base import BaseCommand
from django.utils import timezone
from wholesale.models import Provider, ProviderCategory
from wholesale.api_service import APIServiceFactory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Discover and sync categories from Unique Inter Wholesale API'

    def add_arguments(self, parser):
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
                    f'Please create it first with user_email in extra JSONField.'
                )
            )
            return

        self.stdout.write(f'Discovering categories for {provider.name}...')

        # Create API service
        api_service = APIServiceFactory.create_service(provider)

        # Check if it's UniqueInterAPIService
        if not hasattr(api_service, 'discover_categories'):
            self.stdout.write(
                self.style.ERROR(
                    f'Provider {provider.code} does not support category discovery'
                )
            )
            return

        # Discover categories
        categories = api_service.discover_categories()

        if not categories:
            self.stdout.write(
                self.style.WARNING('No active categories found')
            )
            return

        # Sync categories to database
        created_count = 0
        updated_count = 0

        for cat_data in categories:
            category, created = ProviderCategory.objects.update_or_create(
                provider=provider,
                category_id=cat_data['category_id'],
                defaults={
                    'name': cat_data['name'],
                    'name_local': cat_data.get('name_local', ''),
                    'total_tours': cat_data.get('tour_count', 0),
                    'is_active': True,
                    'last_synced': timezone.now()
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: {category.name} ({category.category_id}) - '
                        f'{category.total_tours} tours'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Updated: {category.name} ({category.category_id}) - '
                        f'{category.total_tours} tours'
                    )
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Category sync completed: {created_count} created, '
                f'{updated_count} updated'
            )
        )
        self.stdout.write('')
        self.stdout.write(
            'You can now manage categories in Django Admin:'
        )
        self.stdout.write('  - Enable/disable categories')
        self.stdout.write('  - Set sync priority')
        self.stdout.write('  - Add new categories manually')
