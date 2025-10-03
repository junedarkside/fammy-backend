from django.core.management.base import BaseCommand
from wholesale.models import ProgramTour
from collections import Counter


class Command(BaseCommand):
    help = 'Audit tours with invalid country names'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider-code',
            type=str,
            help='Filter by provider code (e.g., unique_inter, zego)'
        )

    def handle(self, *args, **options):
        provider_code = options.get('provider_code')

        # Find tours with country_name but no Country FK
        queryset = ProgramTour.objects.filter(
            country__isnull=True
        ).exclude(country_name='').select_related('provider')

        if provider_code:
            queryset = queryset.filter(provider__code=provider_code)

        if not queryset.exists():
            self.stdout.write(
                self.style.SUCCESS('✓ All tours have valid countries!')
            )
            return

        # Group by provider and invalid country_name
        by_provider = {}
        invalid_names = Counter()

        for tour in queryset:
            provider_name = tour.provider.name
            if provider_name not in by_provider:
                by_provider[provider_name] = []
            by_provider[provider_name].append(tour)
            invalid_names[tour.country_name] += 1

        # Report
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                f'⚠ Found {queryset.count()} tours with invalid country names'
            )
        )
        self.stdout.write('')

        self.stdout.write(
            self.style.WARNING('Invalid Country Names (frequency):')
        )
        for name, count in invalid_names.most_common():
            self.stdout.write(f'  - "{name}": {count} tours')

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Tours by Provider:'))
        for provider_name, tours in by_provider.items():
            self.stdout.write(f'\n{provider_name}: {len(tours)} tours')
            for tour in tours[:5]:  # Show first 5
                self.stdout.write(
                    f'  - {tour.code}: "{tour.country_name}"'
                )
            if len(tours) > 5:
                self.stdout.write(f'  ... and {len(tours) - 5} more')

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'To fix: Filter by "Needs Review" in Django Admin → Wholesale → Program Tours'
            )
        )
        self.stdout.write('')
