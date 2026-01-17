---
name: integrate-provider
description: Use when adding a new tour provider/wholesaler API. Analyzes API responses and generates mapper, normalizer, and sync command code. Examples - "Add new provider TravelHub", "Integrate Viator API", "Create adapter for new wholesaler"
model: sonnet
---

# Provider Integration Helper

## Purpose

Help integrate new tour provider/wholesaler APIs by analyzing their data structure and generating the necessary Django code (mappers, normalizers, management commands, models).

## When to Use This Skill

- Adding a completely new tour provider to the platform
- Integrating a wholesaler API with different data structure
- Creating sync commands for a new data source
- Need to generate boilerplate code for provider integration
- Analyzing API responses to understand data mapping needs

## Integration Workflow

### Step 1: Gather Provider Information

Ask the user for basic provider details:

**Required information**:
- Provider name (e.g., "TravelHub", "Viator", "GetYourGuide")
- Provider code (short identifier, e.g., "travelhub", "viator", "gyg")
- API base URL (e.g., "https://api.travelhub.com/v1")
- Authentication method (API key, OAuth, Basic Auth, none)
- API documentation URL (if available)

**Questions to ask**:
```
1. What is the provider's name and short code?
2. What is the API base URL?
3. How does the API authenticate? (API key header, token, credentials, etc.)
4. Do you have sample API responses for:
   - Countries/destinations
   - Tour packages
   - Tour periods/dates
   - Flights (if applicable)
   - Itineraries/day-by-day program (if applicable)
5. Does the provider have unique data not in our current models?

CATEGORY-RELATED QUESTIONS (Critical for choosing integration pattern):
6. Does the API require category/classification parameters to fetch tours?
   - Can you fetch tours without specifying a category?
   - If category is required, what are the available categories?
7. Are categories documented in the API documentation?
   - If yes, what are the category IDs and names?
   - If no, can categories be discovered programmatically?
8. Do categories represent destinations, regions, or tour types?
9. How many categories does the provider have? (Finite or infinite?)
10. Can tours be fetched in bulk, or only per category?
```

### Step 2: Analyze API Response Structure

Request sample JSON responses from the provider's API endpoints:

**Critical endpoints to analyze**:
1. **Countries/Destinations** - Geographic data
2. **Tours/Packages** - Tour listing
3. **Tour Details** - Individual tour information
4. **Periods/Dates** - Available travel dates and pricing
5. **Flights** - Flight information (if provided)
6. **Itineraries** - Day-by-day program (if provided)

**For each response, identify**:
- Root data structure (object, array, nested object)
- Field names and data types
- Required vs optional fields
- Nested objects and arrays
- Unique identifiers
- Foreign key relationships
- Pagination structure (if any)

**Example analysis**:
```json
// Sample tour response
{
  "data": {
    "tours": [
      {
        "id": "TH001",
        "title": "Amazing Thailand Tour",
        "destination": "Thailand",
        "duration": 5,
        "price": {
          "amount": 25000,
          "currency": "THB"
        },
        "dates": [
          {
            "start": "2026-03-15",
            "end": "2026-03-20",
            "available_seats": 20
          }
        ]
      }
    ]
  }
}
```

**Analysis notes**:
- Root path: `data.tours[]` (array of tours)
- Tour ID field: `id` → maps to `ProgramTour.provider_tour_id`
- Tour name: `title` → maps to `ProgramTour.name`
- Destination: `destination` (string) → needs country lookup
- Duration: `duration` (integer) → maps to `ProgramTour.total_days`
- Price: nested object with `amount` and `currency`
- Dates: embedded array → should be Period model records

### Step 3: Check for Existing Similar Providers

Before generating new code, check if any existing provider has similar data structure:

**Existing providers** (use as reference patterns):

- **Zego** - Standard tour provider with separate country/tour/period endpoints
  - Pattern: Simple REST API, straightforward data mapping
  - Use for: Basic provider integration with standard endpoints

- **Unique Inter** - Departure-centric model with categories, two-stage pipeline
  - Pattern: Complex two-stage (fetch → process), category-based filtering, title parsing
  - Use for: Providers with complex data processing, category systems
  - Files: `sync_unique_inter.py`, `sync_unique_inter_categories.py`, `data_sync_service.py`

- **CheckIn Group** - Thai B2B wholesaler with complete pricing and commissions
  - Pattern: Simple REST API, JSON pricing, Thai language, complete tour details
  - Use for: Thai B2B wholesalers, providers with comprehensive pricing data
  - Files: `sync_checkingroup.py`, `CheckInGroupMapper` (lines 612-924)

- **Go365** - Multi-language support, detailed flight information
  - Pattern: Standard REST API with pagination, multi-language, search capabilities
  - Use for: Providers with language options, detailed flight/period data
  - Files: `sync_go365.py`, `Go365Mapper`

**Files to check**:
```bash
# Read existing mappers
Read wholesale/provider_mappers.py

# Check existing normalizers
Read wholesale/field_normalizers.py

# Review existing sync commands
Glob wholesale/management/commands/sync_*.py
```

**Decision**:
- If data structure is very similar → Extend existing mapper
- If data structure is different → Create new mapper
- If normalization is standard → Reuse existing normalizer
- If normalization is unique → Create provider-specific normalizer

#### ProviderCategory Decision Guide

**CRITICAL: Determine if the API requires category parameters**

Ask yourself these questions about the provider's API:

1. **Can you fetch tours without specifying a category?**
   - YES → Use Pattern A (Simple REST) or Pattern B (Two-Stage Pipeline)
   - NO → Continue to question 2

2. **Does the API require category/classification parameter to return tours?**
   - YES → Use Pattern C (Category-Based API) with ProviderCategory model
   - NO → Use Pattern A or B

3. **Are categories finite and discoverable?**
   - YES → Perfect for ProviderCategory pattern
   - NO (infinite/user-generated) → Consider alternative approach

**Example scenarios**:

**Scenario 1: Category-based API (Use ProviderCategory)**
```
API Endpoint: GET /tours?category_id=59
Response: Returns tours only for category 59 (Europe)

Without category_id parameter: API returns error or empty result

✓ Use Pattern C with ProviderCategory model
```

**Scenario 2: Category as filter (DON'T use ProviderCategory)**
```
API Endpoint: GET /tours (returns all tours)
API Endpoint: GET /tours?category=europe (optional filter)

Without category parameter: API returns all tours

✗ Don't use ProviderCategory - categories are optional filters
✓ Use Pattern A (Simple REST)
```

**Scenario 3: Category as tag (DON'T use ProviderCategory)**
```
API Endpoint: GET /tours
Response:
{
  "tours": [
    {"id": "T001", "name": "Tour 1", "tags": ["europe", "adventure"]},
    {"id": "T002", "name": "Tour 2", "tags": ["asia", "cultural"]}
  ]
}

Categories embedded as tags in tour data, not required parameters

✗ Don't use ProviderCategory - categories are metadata
✓ Use Pattern A (Simple REST)
```

**When to use ProviderCategory**:
- ✅ API requires category parameter (cannot fetch tours without it)
- ✅ Categories represent destinations, regions, or tour types
- ✅ Finite set of categories (e.g., 5-50 categories)
- ✅ Categories are documented or discoverable
- ✅ Need to enable/disable certain category syncs
- ✅ Want to control sync order by category priority

**When NOT to use ProviderCategory**:
- ❌ API returns all tours without category parameter
- ❌ Categories are optional filters or tags
- ❌ Categories are embedded metadata in tour data
- ❌ Infinite or user-generated categories
- ❌ Categories change frequently or unpredictably

### Step 4: Generate Provider Mapper

Based on API structure analysis, generate the mapper class:

**Template location**: `wholesale/provider_mappers.py`

**Mapper class structure**:
```python
class {Provider}Mapper(ProviderDataMapper):
    """
    Maps {Provider} API responses to Django model fields.

    API Structure:
    - Countries: {describe endpoint and structure}
    - Tours: {describe endpoint and structure}
    - Periods: {describe endpoint and structure}
    - Flights: {describe endpoint and structure}
    """

    def __init__(self, normalizer):
        """
        Initialize mapper with normalizer for data transformations.

        Args:
            normalizer: Instance of ProviderNormalizer or {Provider}Normalizer
        """
        self.normalizer = normalizer

    def map_country_data(self, raw_data, provider=None):
        """
        Map {Provider} country/destination data to Country model fields.

        Args:
            raw_data: Dict with {Provider} country data
            provider: Provider model instance

        Returns:
            Dict with Country model fields
        """
        return {
            'provider': provider,
            'name': raw_data.get('country_name', ''),
            'code': self.normalizer.normalize_country_code(
                raw_data.get('country_code', '')
            ),
            'provider_country_id': str(raw_data.get('id', '')),
        }

    def map_tour_data(self, raw_data, provider=None):
        """
        Map {Provider} tour data to ProgramTour model fields.

        Args:
            raw_data: Dict with {Provider} tour data
            provider: Provider model instance

        Returns:
            Dict with ProgramTour model fields
        """
        return {
            'provider': provider,
            'provider_tour_id': str(raw_data.get('id', '')),
            'name': raw_data.get('title', raw_data.get('name', '')),
            'total_days': int(raw_data.get('duration', 0)),
            'total_nights': int(raw_data.get('duration', 0)) - 1,
            'description': raw_data.get('description', ''),
            # Add country FK lookup if country data is embedded
            # 'country': self._lookup_country(raw_data.get('destination')),
        }

    def map_period_data(self, raw_data, program_tour=None, provider=None):
        """
        Map {Provider} period/date data to Period model fields.

        Args:
            raw_data: Dict with {Provider} period data
            program_tour: ProgramTour model instance
            provider: Provider model instance

        Returns:
            Dict with Period model fields
        """
        return {
            'provider': provider,
            'program_tour': program_tour,
            'provider_period_id': str(raw_data.get('period_id', raw_data.get('id', ''))),
            'start_date': self.normalizer.normalize_date(raw_data.get('start_date')),
            'end_date': self.normalizer.normalize_date(raw_data.get('end_date')),
            'price_adult': self.normalizer.normalize_price(
                raw_data.get('price', {}).get('amount', 0)
            ),
            'available_seats': int(raw_data.get('available_seats', 0)),
        }

    def map_flight_data(self, raw_data, period=None, provider=None):
        """
        Map {Provider} flight data to Flight model fields.

        Args:
            raw_data: Dict with {Provider} flight data
            period: Period model instance
            provider: Provider model instance

        Returns:
            Dict with Flight model fields
        """
        return {
            'provider': provider,
            'period': period,
            'flight_no': raw_data.get('flight_number', ''),
            'airline_code': raw_data.get('airline_code', ''),
            'airline_name': raw_data.get('airline_name', ''),
            'departure_airport': raw_data.get('departure_airport', ''),
            'arrival_airport': raw_data.get('arrival_airport', ''),
            'departure_time': self.normalizer.normalize_datetime(
                raw_data.get('departure_time')
            ),
            'arrival_time': self.normalizer.normalize_datetime(
                raw_data.get('arrival_time')
            ),
        }

    def map_itinerary_data(self, raw_data, program_tour=None, provider=None):
        """
        Map {Provider} itinerary/day-by-day data to Itinerary model fields.

        Args:
            raw_data: Dict with {Provider} itinerary data
            program_tour: ProgramTour model instance
            provider: Provider model instance

        Returns:
            Dict with Itinerary model fields
        """
        return {
            'provider': provider,
            'program_tour': program_tour,
            'day_number': int(raw_data.get('day', 0)),
            'title': raw_data.get('title', ''),
            'description': raw_data.get('description', ''),
            'meals': raw_data.get('meals', ''),
            'accommodation': raw_data.get('hotel', ''),
        }
```

**Key patterns to follow**:
1. Always accept `provider` parameter for FK assignment
2. Use `self.normalizer` for data transformations
3. Provide safe defaults with `.get(field, default)`
4. Convert types explicitly (int(), str(), etc.)
5. Handle nested objects carefully
6. Return dict matching Django model fields exactly

### Step 5: Generate Provider Normalizer (if needed)

If the provider has unique data formats, create a custom normalizer:

**Template location**: `wholesale/field_normalizers.py`

**Normalizer class structure**:
```python
class {Provider}Normalizer(ProviderNormalizer):
    """
    Custom normalizer for {Provider} API data formats.

    Handles provider-specific:
    - Date/time formats
    - Price formats
    - Country codes
    - Unique data transformations
    """

    def normalize_date(self, date_value):
        """
        Normalize {Provider} date format to YYYY-MM-DD.

        {Provider} uses format: {describe format, e.g., "DD/MM/YYYY" or "YYYY-MM-DD"}

        Args:
            date_value: Date string from {Provider} API

        Returns:
            Date string in YYYY-MM-DD format or None
        """
        if not date_value:
            return None

        try:
            # Example: "15/03/2026" → "2026-03-15"
            from datetime import datetime
            dt = datetime.strptime(date_value, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return None

    def normalize_price(self, price_value):
        """
        Normalize {Provider} price to Decimal in THB.

        {Provider} provides prices as: {describe format}

        Args:
            price_value: Price value from {Provider} API

        Returns:
            Decimal price in THB
        """
        from decimal import Decimal

        if not price_value:
            return Decimal('0.00')

        try:
            # Handle nested price objects
            if isinstance(price_value, dict):
                amount = price_value.get('amount', 0)
                currency = price_value.get('currency', 'THB')

                # Convert to THB if needed
                if currency != 'THB':
                    # Add currency conversion logic here
                    pass

                return Decimal(str(amount))

            # Handle direct numeric values
            return Decimal(str(price_value))
        except (ValueError, TypeError, decimal.InvalidOperation):
            return Decimal('0.00')

    def normalize_country_code(self, country_value):
        """
        Normalize {Provider} country identifier to ISO code.

        Args:
            country_value: Country name, code, or ID from {Provider}

        Returns:
            ISO country code (TH, JP, etc.) or original value
        """
        # Map provider-specific country identifiers to ISO codes
        country_map = {
            'thailand': 'TH',
            'japan': 'JP',
            'korea': 'KR',
            # Add provider-specific mappings
        }

        if not country_value:
            return ''

        # Try direct lookup
        normalized = country_map.get(str(country_value).lower())
        if normalized:
            return normalized

        # If already looks like ISO code, return as-is
        if len(str(country_value)) == 2:
            return str(country_value).upper()

        return str(country_value)
```

**When to create custom normalizer**:
- Provider uses non-standard date formats
- Price is in non-THB currency and needs conversion
- Country codes are non-standard (names, numeric IDs, etc.)
- Provider has unique data transformations
- Otherwise, reuse existing `ProviderNormalizer` class

### Step 6: Generate Management Command

Create sync command for the provider:

**Template location**: `wholesale/management/commands/sync_{provider}.py`

**Management command structure**:
```python
from django.core.management.base import BaseCommand
from wholesale.models import Provider, Country, ProgramTour, Period, Flight, Itinerary
from wholesale.provider_mappers import {Provider}Mapper
from wholesale.field_normalizers import {Provider}Normalizer  # or ProviderNormalizer
import requests
import traceback


class Command(BaseCommand):
    help = 'Sync {Provider} tour data to database'

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            '--countries-only',
            action='store_true',
            help='Sync only countries/destinations',
        )
        parser.add_argument(
            '--tours-only',
            action='store_true',
            help='Sync only tour packages',
        )
        parser.add_argument(
            '--tour-id',
            type=str,
            help='Sync specific tour by ID',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of tours to sync',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test API connection and authentication',
        )

    def handle(self, *args, **options):
        """Execute sync command."""
        self.stdout.write(self.style.SUCCESS('Starting {Provider} sync...'))

        # Get or create provider
        provider, created = Provider.objects.get_or_create(
            code='{provider_code}',
            defaults={
                'name': '{Provider Name}',
                'api_endpoint': '{API_BASE_URL}',
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created provider: {provider.name}'))

        # Initialize mapper and normalizer
        normalizer = {Provider}Normalizer()  # or ProviderNormalizer()
        mapper = {Provider}Mapper(normalizer)

        # Handle command options
        if options.get('test_connection'):
            self.test_connection(provider)
            return

        if options.get('countries_only'):
            self.sync_countries(provider, mapper)
            return

        if options.get('tours_only'):
            self.sync_tours(provider, mapper, options)
            return

        # Full sync (default)
        self.sync_countries(provider, mapper)
        self.sync_tours(provider, mapper, options)

        self.stdout.write(self.style.SUCCESS('✓ {Provider} sync completed'))

    def test_connection(self, provider):
        """Test API connection and authentication."""
        self.stdout.write('Testing {Provider} API connection...')

        try:
            response = self.make_api_request(
                provider,
                '/test-endpoint'  # Replace with actual test endpoint
            )

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✓ API connection successful'))
                self.stdout.write(f'Response: {response.json()}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ API returned status {response.status_code}')
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Connection failed: {str(e)}'))
            self.stdout.write(traceback.format_exc())

    def make_api_request(self, provider, endpoint, params=None):
        """
        Make authenticated API request to {Provider}.

        Args:
            provider: Provider model instance
            endpoint: API endpoint path
            params: Query parameters dict

        Returns:
            requests.Response object
        """
        url = f"{provider.api_endpoint}{endpoint}"

        # Configure authentication
        headers = {
            'Content-Type': 'application/json',
            # Add provider-specific auth headers
            # 'X-API-Key': provider.api_key,
            # 'Authorization': f'Bearer {provider.api_token}',
        }

        response = requests.get(url, headers=headers, params=params or {})
        response.raise_for_status()

        return response

    def sync_countries(self, provider, mapper):
        """Sync countries/destinations from {Provider} API."""
        self.stdout.write('Syncing {Provider} countries...')

        try:
            # Fetch countries from API
            response = self.make_api_request(provider, '/countries')  # Adjust endpoint
            data = response.json()

            # Extract country array (adjust path based on API structure)
            countries = data.get('data', {}).get('countries', [])

            created_count = 0
            updated_count = 0

            for country_data in countries:
                try:
                    # Map API data to model fields
                    country_fields = mapper.map_country_data(country_data, provider)

                    # Validate required fields
                    if not country_fields.get('name'):
                        self.stdout.write(
                            self.style.WARNING('Skipping country: Missing name')
                        )
                        continue

                    # Create or update country
                    country, created = Country.objects.update_or_create(
                        provider=provider,
                        provider_country_id=country_fields['provider_country_id'],
                        defaults=country_fields
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'ERROR syncing country: {str(e)}')
                    )
                    self.stdout.write(traceback.format_exc())

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Countries: {created_count} created, {updated_count} updated'
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR fetching countries: {str(e)}'))
            self.stdout.write(traceback.format_exc())

    def sync_tours(self, provider, mapper, options):
        """Sync tour packages from {Provider} API."""
        self.stdout.write('Syncing {Provider} tours...')

        try:
            # Build API request parameters
            params = {}

            if options.get('limit'):
                params['limit'] = options['limit']

            if options.get('tour_id'):
                # Fetch specific tour
                tour_id = options['tour_id']
                response = self.make_api_request(
                    provider,
                    f'/tours/{tour_id}'  # Adjust endpoint
                )
                tours = [response.json().get('data', {})]
            else:
                # Fetch all tours
                response = self.make_api_request(provider, '/tours', params)
                data = response.json()
                tours = data.get('data', {}).get('tours', [])  # Adjust path

            created_count = 0
            updated_count = 0

            for tour_data in tours:
                try:
                    # Map API data to model fields
                    tour_fields = mapper.map_tour_data(tour_data, provider)

                    # Validate required fields
                    if not tour_fields.get('provider_tour_id'):
                        self.stdout.write(
                            self.style.WARNING('Skipping tour: Missing provider_tour_id')
                        )
                        continue

                    # Create or update tour
                    tour, created = ProgramTour.objects.update_or_create(
                        provider=provider,
                        provider_tour_id=tour_fields['provider_tour_id'],
                        defaults=tour_fields
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(f'  Created tour: {tour.name}')
                    else:
                        updated_count += 1

                    # Sync related data (periods, flights, itineraries)
                    self.sync_tour_periods(tour, tour_data, provider, mapper)
                    self.sync_tour_itineraries(tour, tour_data, provider, mapper)

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'ERROR syncing tour: {str(e)}')
                    )
                    self.stdout.write(traceback.format_exc())

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Tours: {created_count} created, {updated_count} updated'
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR fetching tours: {str(e)}'))
            self.stdout.write(traceback.format_exc())

    def sync_tour_periods(self, tour, tour_data, provider, mapper):
        """Sync periods/dates for a tour."""
        # Extract periods from tour data (adjust based on API structure)
        periods = tour_data.get('dates', [])  # or tour_data.get('periods', [])

        for period_data in periods:
            try:
                period_fields = mapper.map_period_data(period_data, tour, provider)

                # Validate required fields
                if not period_fields.get('start_date'):
                    continue

                period, created = Period.objects.update_or_create(
                    provider=provider,
                    program_tour=tour,
                    provider_period_id=period_fields.get('provider_period_id', ''),
                    defaults=period_fields
                )

                # Sync flights for this period if available
                if 'flights' in period_data:
                    self.sync_period_flights(period, period_data['flights'], provider, mapper)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'ERROR syncing period: {str(e)}')
                )

    def sync_period_flights(self, period, flights_data, provider, mapper):
        """Sync flights for a period."""
        for flight_data in flights_data:
            try:
                flight_fields = mapper.map_flight_data(flight_data, period, provider)

                # Validate required fields
                if not flight_fields.get('flight_no'):
                    self.stdout.write(
                        self.style.WARNING('Skipping flight: Missing flight_no')
                    )
                    continue

                Flight.objects.update_or_create(
                    provider=provider,
                    period=period,
                    flight_no=flight_fields['flight_no'],
                    defaults=flight_fields
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'ERROR syncing flight: {str(e)}')
                )

    def sync_tour_itineraries(self, tour, tour_data, provider, mapper):
        """Sync day-by-day itinerary for a tour."""
        # Extract itinerary from tour data
        itineraries = tour_data.get('itinerary', [])  # or tour_data.get('days', [])

        for itinerary_data in itineraries:
            try:
                itinerary_fields = mapper.map_itinerary_data(itinerary_data, tour, provider)

                Itinerary.objects.update_or_create(
                    provider=provider,
                    program_tour=tour,
                    day_number=itinerary_fields['day_number'],
                    defaults=itinerary_fields
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'ERROR syncing itinerary: {str(e)}')
                )
```

**Key command patterns**:
1. Always use `.get()` for optional command arguments (not `[]`)
2. Add full traceback logging for all exceptions
3. Validate required fields before save
4. Use `update_or_create()` for idempotency
5. Provide `--test-connection` option
6. Support selective sync (--countries-only, --tours-only, --tour-id)
7. Add `--limit` for testing with small datasets

### Step 7: Update Provider Models (if needed)

If the provider has unique data not in current models, suggest model changes:

**Check existing models**:
```python
# Read wholesale/models.py
# Check if existing fields cover provider's data
# Identify missing fields
```

**Suggest new fields**:
```python
class ProgramTour(models.Model):
    # Existing fields...

    # NEW: Fields for {Provider}
    {new_field_name} = models.CharField(max_length=200, blank=True, default='')
    {new_field_name} = models.TextField(blank=True, default='')
```

**Migration commands**:
```bash
# After adding fields to models.py
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Step 8: Register Provider in Django Admin

Add provider to admin interface for manual sync:

**File**: `wholesale/admin.py`

```python
# Add sync action for new provider
@admin.action(description='Sync {Provider} data now')
def sync_{provider}_action(modeladmin, request, queryset):
    """Trigger {Provider} sync from admin."""
    from django.core.management import call_command

    for provider in queryset:
        if provider.code == '{provider_code}':
            try:
                call_command('sync_{provider}')
                modeladmin.message_user(
                    request,
                    f'Successfully synced {provider.name}',
                    messages.SUCCESS
                )
            except Exception as e:
                modeladmin.message_user(
                    request,
                    f'Error syncing {provider.name}: {str(e)}',
                    messages.ERROR
                )

# Add to ProviderAdmin actions
class ProviderAdmin(admin.ModelAdmin):
    actions = [
        # ... existing actions
        sync_{provider}_action,
    ]
```

### Step 9: Create Documentation

Document the new provider integration:

**File**: `docs/provider-integration/{provider}-guide.md`

```markdown
# {Provider} Integration Guide

## Overview

{Provider} is a {describe provider type, e.g., "B2B tour wholesaler" or "global tour marketplace"}.

**Provider code**: `{provider_code}`
**API base URL**: `{API_BASE_URL}`
**Authentication**: {describe auth method}

## API Endpoints

### Countries
- **Endpoint**: `GET /countries`
- **Response**: {describe structure}
- **Maps to**: `wholesale.Country` model

### Tours
- **Endpoint**: `GET /tours`
- **Response**: {describe structure}
- **Maps to**: `wholesale.ProgramTour` model

### Periods
- **Endpoint**: Embedded in tour response or separate endpoint
- **Response**: {describe structure}
- **Maps to**: `wholesale.Period` model

## Data Mapping

### Country Mapping
| {Provider} Field | Django Field | Transformation |
|------------------|--------------|----------------|
| `country_id` | `provider_country_id` | String conversion |
| `country_name` | `name` | Direct |
| `country_code` | `code` | ISO code normalization |

### Tour Mapping
| {Provider} Field | Django Field | Transformation |
|------------------|--------------|----------------|
| `id` | `provider_tour_id` | String conversion |
| `title` | `name` | Direct |
| `duration` | `total_days` | Integer conversion |
| `price.amount` | Calculated in Period | Decimal normalization |

## Sync Commands

### Full Sync
```bash
docker-compose exec web python manage.py sync_{provider}
```

### Countries Only
```bash
docker-compose exec web python manage.py sync_{provider} --countries-only
```

### Specific Tour
```bash
docker-compose exec web python manage.py sync_{provider} --tour-id TH001
```

### Test Connection
```bash
docker-compose exec web python manage.py sync_{provider} --test-connection
```

### Limited Sync (Testing)
```bash
docker-compose exec web python manage.py sync_{provider} --limit 10
```

## Authentication Setup

{Describe how to configure authentication, e.g.:}

1. Get API key from {Provider} dashboard
2. Add to Provider model in Django admin:
   - API Key field: `{api_key}`
   - API Endpoint: `{API_BASE_URL}`
3. Or set environment variable:
   ```bash
   {PROVIDER}_API_KEY=your_key_here
   ```

## Data Quality

{Describe data quality, completeness, update frequency}

**Strengths**:
- {What data is complete and high quality}

**Limitations**:
- {What data is missing or inconsistent}

**Update frequency**: {How often provider updates data}

## Troubleshooting

### No data syncing
- Check API authentication (use `--test-connection`)
- Verify provider is active in Django admin
- Check model field constraints (see debug-provider-sync skill)

### Partial data syncing
- Check console output for WARNING messages
- Validate required fields in models
- Review mapper field extraction logic

### Connection errors
- Verify API endpoint URL
- Check network connectivity
- Confirm API key is valid

## Related Files

- Mapper: `wholesale/provider_mappers.py` → `{Provider}Mapper`
- Normalizer: `wholesale/field_normalizers.py` → `{Provider}Normalizer`
- Sync command: `wholesale/management/commands/sync_{provider}.py`
- Models: `wholesale/models.py`
```

### Step 10: Provide Implementation Checklist

Give the user a complete checklist:

```markdown
## {Provider} Integration Checklist

### Phase 1: Code Generation
- [ ] Created `{Provider}Mapper` in `wholesale/provider_mappers.py`
- [ ] Created `{Provider}Normalizer` in `wholesale/field_normalizers.py` (if needed)
- [ ] Created `wholesale/management/commands/sync_{provider}.py`
- [ ] Added provider sync action to `wholesale/admin.py`

### Phase 1A: Category Setup (If Category-Based API - Pattern C)
- [ ] Created `wholesale/management/commands/sync_{provider}_categories.py`
- [ ] Identified all provider categories (from API docs or discovery)
- [ ] Tested category discovery command
- [ ] Created ProviderCategory records in database
- [ ] Configured categories in Django Admin:
  - [ ] Set `is_active=True` for categories to sync
  - [ ] Set `priority` values for sync order
  - [ ] Verified `total_tours` counts are accurate
- [ ] Added ProviderCategory admin configuration (if not already exists)

### Phase 2: Testing
- [ ] Created Provider record in Django admin (code: `{provider_code}`)
- [ ] Tested API connection: `python manage.py sync_{provider} --test-connection`
- [ ] **If category-based**: Tested category discovery first
- [ ] **If category-based**: Tested single category sync: `--category-id X --limit 5`
- [ ] Tested limited sync: `python manage.py sync_{provider} --limit 5`
- [ ] Verified data in Django admin (Countries, Tours, Periods)
- [ ] **If category-based**: Verified ProviderCategory metadata updates
- [ ] Checked for error messages in console output

### Phase 3: Validation
- [ ] Validated all required model fields can be populated
- [ ] Confirmed no constraint violations (use validate-models skill)
- [ ] Verified data quality and completeness
- [ ] **If category-based**: Verified all active categories sync correctly
- [ ] **If category-based**: Tested enable/disable category functionality
- [ ] Tested full sync with all data

### Phase 4: Documentation
- [ ] Created `docs/provider-integration/{provider}-guide.md`
- [ ] **If category-based**: Documented category discovery process
- [ ] **If category-based**: Documented category configuration in guide
- [ ] Updated `CLAUDE.md` provider list
- [ ] Updated `docs/README.md` with provider reference
- [ ] Documented authentication setup

### Phase 5: Deployment
- [ ] Added provider credentials to production environment
- [ ] **If category-based**: Synced categories to production database
- [ ] **If category-based**: Configured production categories (is_active, priority)
- [ ] Configured Celery Beat schedule for automatic sync
- [ ] **If category-based**: Scheduled category discovery periodic task (optional)
- [ ] Set up monitoring/alerting for sync failures
- [ ] Informed users of new provider availability
```

## Reference Implementation Patterns

### Pattern A: Simple REST API (CheckIn Group)

**Use when**:
- Provider has simple REST API with standard endpoints
- Complete data in single response (no multi-stage processing)
- Straightforward field mapping

**Key characteristics**:
- Single management command handles all sync
- Direct API → Model mapping
- No intermediate storage (RawVendorData)
- Optional arguments with `.get()` for safe access

**Example structure** (CheckIn Group):
```python
# wholesale/management/commands/sync_checkingroup.py (115 lines)

class Command(BaseCommand):
    def add_arguments(self, parser):
        # CRITICAL: Use .get() for optional args in handle()
        parser.add_argument('--tour-id', type=str, help='Sync specific tour')
        parser.add_argument('--period-id', type=str, help='Sync specific period')
        parser.add_argument('--limit', type=int, help='Limit results')

    def handle(self, *args, **options):
        # ALWAYS use .get() for optional arguments
        tour_id = options.get('tour_id')  # ✓ Safe
        # NOT: tour_id = options['tour_id']  # ✗ KeyError in Django Admin

        # Simple flow
        self.sync_tours(provider, mapper, options)

    def sync_tours(self, provider, mapper, options):
        # Fetch from API
        tours = self.fetch_tours_from_api(options)

        # Process each tour
        for tour_data in tours:
            # Map and save tour
            tour_fields = mapper.map_tour_data(tour_data, provider)
            tour, created = ProgramTour.objects.update_or_create(...)

            # Sync related data inline
            self.sync_periods(tour, tour_data['periods'])
```

**Pros**:
- Simple to understand and maintain
- Fast (no intermediate storage)
- Less database overhead

**Cons**:
- Can't re-process without re-fetching API
- No audit trail of raw API data
- Less debugging visibility

**Use CheckIn Group as reference for**:
- Thai B2B wholesalers
- Providers with complete tour packages in single response
- Simple JSON APIs without complex data transformations

### Pattern B: Two-Stage Pipeline (Unique Inter)

**Use when**:
- Provider has complex data that needs multi-step processing
- Want to preserve raw API data for debugging
- Need to re-process data without re-fetching
- API has rate limits or slow responses

**Key characteristics**:
- Two-stage: Fetch → Process
- Raw data stored in `RawVendorData` model
- Error tracking per record via `error_message` field
- Can re-run processing without API calls
- Separate commands for category discovery

**Example structure** (Unique Inter):
```python
# wholesale/management/commands/sync_unique_inter.py

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--fetch-only', action='store_true')
        parser.add_argument('--process-only', action='store_true')

    def handle(self, *args, **options):
        if options.get('fetch_only'):
            self.fetch_raw_data()
        elif options.get('process_only'):
            self.process_raw_data()
        else:
            self.fetch_raw_data()
            self.process_raw_data()

    def fetch_raw_data(self):
        """Stage 1: Fetch from API and save to RawVendorData."""
        for tour_data in api_response:
            RawVendorData.objects.update_or_create(
                provider=provider,
                external_id=tour_data['mainid'],
                defaults={'data': tour_data, 'processed': False}
            )

    def process_raw_data(self):
        """Stage 2: Process RawVendorData into models."""
        raw_records = RawVendorData.objects.filter(
            provider=provider,
            processed=False
        )

        for raw in raw_records:
            try:
                # Extract and transform
                tour = self.create_tour_from_raw(raw.data)

                # Mark as processed
                raw.processed = True
                raw.error_message = ''
                raw.save()

            except Exception as e:
                # Track error but continue
                raw.error_message = str(e)
                raw.save()
```

**Additional commands** (Category-based providers):
```python
# wholesale/management/commands/sync_unique_inter_categories.py

class Command(BaseCommand):
    """Discover and sync provider categories."""

    def handle(self, *args, **options):
        # Fetch categories from API
        categories = self.fetch_categories()

        # Create ProviderCategory records
        for cat in categories:
            ProviderCategory.objects.update_or_create(
                provider=provider,
                category_id=cat['id'],
                defaults={'category_name': cat['name'], 'is_active': True}
            )
```

**Pros**:
- Raw data preserved for debugging
- Can re-process without API calls
- Error tracking per record
- Easier to iteratively improve processing logic

**Cons**:
- More complex to understand
- Extra database storage
- Need to manage RawVendorData cleanup
- Two-stage debugging required

**Use Unique Inter as reference for**:
- Providers with category/classification systems
- Complex data extraction (e.g., parsing from titles)
- APIs with rate limits or slow responses
- When you need audit trail of raw API data

**Key files**:
- Main sync: `wholesale/management/commands/sync_unique_inter.py`
- Category discovery: `wholesale/management/commands/sync_unique_inter_categories.py`
- Data utilities: `wholesale/data_sync_service.py` (lines 950-1214)
- Country extraction: Lines 1100-1151
- Audit tool: `wholesale/management/commands/audit_tour_countries.py`

### Pattern C: Category-Based API (Unique Inter)

**Use when**:
- Provider API requires category/classification parameter to fetch tours
- Tours cannot be fetched without specifying a category
- Categories represent destinations, regions, or tour classifications
- Provider has a finite set of discoverable categories

**Key characteristics**:
- Uses `ProviderCategory` model for dynamic category management
- Two management commands: category discovery + main sync
- Categories configurable via Django Admin (enable/disable, priority ordering)
- Sync respects `is_active` flag and processes by priority
- Each category tracks metadata (total_tours, last_synced)
- Allows selective sync by category

**When NOT to use**:
- API returns all tours without category parameter → Use Pattern A or B
- Categories are just tags/filters, not required parameters → Use Pattern A or B
- API has infinite or user-generated categories → Consider different approach

#### ProviderCategory Model

The `ProviderCategory` model enables database-driven category management for category-based provider APIs.

**Model**: `wholesale.models.ProviderCategory`

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `provider` | FK(Provider) | Links category to provider | Unique Inter |
| `category_id` | CharField(100) | API category identifier | "59" (Europe) |
| `name` | CharField(200) | English category name | "Europe Tours" |
| `name_local` | CharField(200) | Local language name | "ทัวร์เส้นทางยุโรป" |
| `is_active` | BooleanField | Enable/disable sync | True |
| `priority` | IntegerField | Sync order (higher first) | 10 |
| `total_tours` | IntegerField | Tour count in category | 150 |
| `last_synced` | DateTimeField | Last sync timestamp | 2026-01-17 10:30:00 |

**Key features**:
- **Dynamic enable/disable**: Turn categories on/off without code changes
- **Priority ordering**: Control which categories sync first (useful for rate-limited APIs)
- **Sync metadata**: Track tour counts and last sync times per category
- **Runtime configuration**: Change category settings via Django Admin

**Django Admin configuration**:
```python
# wholesale/admin.py

@admin.register(ProviderCategory)
class ProviderCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'category_id', 'is_active', 'priority', 'total_tours', 'last_synced']
    list_filter = ['provider', 'is_active']
    search_fields = ['name', 'category_id']
    ordering = ['provider', '-priority', 'name']
```

#### Category Discovery Workflow

**Step 1: Discover categories from API**

Create a separate management command to discover available categories:

```python
# wholesale/management/commands/sync_{provider}_categories.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from wholesale.models import Provider, ProviderCategory
import requests


class Command(BaseCommand):
    help = 'Discover and sync {Provider} categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-category',
            type=str,
            help='Test if specific category ID exists in API',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Discovering {Provider} categories...'))

        # Get provider
        provider = Provider.objects.get(code='{provider_code}')

        if options.get('test_category'):
            # Test single category
            self.test_category(provider, options['test_category'])
            return

        # Known categories (from API documentation or discovery)
        known_categories = [
            {'id': '59', 'name': 'Europe Tours', 'name_local': 'ทัวร์ยุโรป', 'priority': 10},
            {'id': '60', 'name': 'Russia Tours', 'name_local': 'ทัวร์รัสเซีย', 'priority': 9},
            {'id': '61', 'name': 'UK Tours', 'name_local': 'ทัวร์อังกฤษ', 'priority': 8},
            {'id': '62', 'name': 'Hong Kong Tours', 'name_local': 'ทัวร์ฮ่องกง', 'priority': 7},
            {'id': '63', 'name': 'Promotions', 'name_local': 'โปรโมชั่น', 'priority': 6},
            {'id': '64', 'name': 'Vietnam Tours', 'name_local': 'ทัวร์เวียดนาม', 'priority': 5},
        ]

        created_count = 0
        updated_count = 0

        for cat_data in known_categories:
            # Test if category exists in API and count tours
            try:
                total_tours = self.test_category_and_count(provider, cat_data['id'])

                # Create or update ProviderCategory
                category, created = ProviderCategory.objects.update_or_create(
                    provider=provider,
                    category_id=cat_data['id'],
                    defaults={
                        'name': cat_data['name'],
                        'name_local': cat_data.get('name_local', ''),
                        'is_active': True,
                        'priority': cat_data.get('priority', 0),
                        'total_tours': total_tours,
                        'last_synced': timezone.now(),
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created: {category.name} ({total_tours} tours)'
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        f'  Updated: {category.name} ({total_tours} tours)'
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ✗ Skipped category {cat_data["id"]}: {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Categories: {created_count} created, {updated_count} updated'
            )
        )

    def test_category_and_count(self, provider, category_id):
        """
        Test if category exists in API and return tour count.

        Args:
            provider: Provider model instance
            category_id: Category ID to test

        Returns:
            int: Number of tours in category

        Raises:
            Exception: If category doesn't exist or API error
        """
        url = f"{provider.api_endpoint}/tours"
        headers = self._get_auth_headers(provider)
        params = {'category_id': category_id, 'limit': 1}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        total_tours = data.get('total', 0)  # Adjust based on API structure

        return total_tours

    def test_category(self, provider, category_id):
        """Test single category and display results."""
        try:
            total_tours = self.test_category_and_count(provider, category_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Category {category_id} exists with {total_tours} tours'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Category {category_id} failed: {str(e)}')
            )

    def _get_auth_headers(self, provider):
        """Build authentication headers for API requests."""
        return {
            'Content-Type': 'application/json',
            # Add provider-specific auth
        }
```

**Step 2: Configure categories in Django Admin**

After discovering categories:
1. Navigate to Django Admin → Wholesale → Provider Categories
2. Review discovered categories
3. Set `is_active=True` for categories to sync
4. Adjust `priority` to control sync order (higher = synced first)
5. Optionally disable categories with `is_active=False`

**Step 3: Main sync uses active categories**

The main sync command queries active categories and processes them:

```python
# wholesale/management/commands/sync_{provider}.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from wholesale.models import Provider, ProviderCategory, ProgramTour, Period
from wholesale.provider_mappers import {Provider}Mapper
from wholesale.field_normalizers import ProviderNormalizer
import requests


class Command(BaseCommand):
    help = 'Sync {Provider} tour data by category'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category-id',
            type=str,
            help='Sync specific category only',
        )
        parser.add_argument(
            '--tour-id',
            type=str,
            help='Sync specific tour only',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit tours per category',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting {Provider} sync...'))

        # Get provider
        provider = Provider.objects.get(code='{provider_code}')

        # Initialize mapper
        normalizer = ProviderNormalizer()
        mapper = {Provider}Mapper(normalizer)

        # Handle specific tour sync
        if options.get('tour_id'):
            self.sync_single_tour(provider, mapper, options['tour_id'])
            return

        # Get categories to sync
        if options.get('category_id'):
            # Sync specific category
            categories = ProviderCategory.objects.filter(
                provider=provider,
                category_id=options['category_id']
            )
        else:
            # Sync all active categories ordered by priority
            categories = ProviderCategory.objects.filter(
                provider=provider,
                is_active=True
            ).order_by('-priority', 'name')

        if not categories.exists():
            self.stdout.write(
                self.style.WARNING(
                    'No active categories found. Run sync_{provider}_categories first.'
                )
            )
            return

        # Sync each category
        total_created = 0
        total_updated = 0

        for category in categories:
            self.stdout.write(f'\n--- Syncing category: {category.name} ---')

            created, updated = self.sync_category(
                provider, mapper, category, options
            )

            total_created += created
            total_updated += updated

            # Update category metadata
            category.last_synced = timezone.now()
            category.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ {Provider} sync completed: {total_created} created, {total_updated} updated'
            )
        )

    def sync_category(self, provider, mapper, category, options):
        """
        Sync tours for a specific category.

        Args:
            provider: Provider model instance
            mapper: Provider mapper instance
            category: ProviderCategory instance
            options: Command options dict

        Returns:
            tuple: (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0

        try:
            # Fetch tours for this category
            tours = self.fetch_category_tours(
                provider,
                category.category_id,
                limit=options.get('limit')
            )

            self.stdout.write(f'  Found {len(tours)} tours')

            # Process each tour
            for tour_data in tours:
                try:
                    # Map tour data
                    tour_fields = mapper.map_tour_data(tour_data, provider)

                    # Validate required fields
                    if not tour_fields.get('provider_tour_id'):
                        self.stdout.write(
                            self.style.WARNING('  Skipping: Missing provider_tour_id')
                        )
                        continue

                    # Create or update tour
                    tour, created = ProgramTour.objects.update_or_create(
                        provider=provider,
                        provider_tour_id=tour_fields['provider_tour_id'],
                        defaults=tour_fields
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(f'  ✓ Created: {tour.name}')
                    else:
                        updated_count += 1

                    # Sync periods for this tour
                    self.sync_tour_periods(tour, tour_data, provider, mapper)

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ERROR syncing tour: {str(e)}')
                    )

            # Update category tour count
            category.total_tours = len(tours)
            category.save()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'ERROR fetching category {category.name}: {str(e)}')
            )

        return created_count, updated_count

    def fetch_category_tours(self, provider, category_id, limit=None):
        """
        Fetch tours for a specific category from API.

        Args:
            provider: Provider model instance
            category_id: Category ID to fetch
            limit: Optional limit on number of tours

        Returns:
            list: Tour data dictionaries
        """
        url = f"{provider.api_endpoint}/tours"
        headers = self._get_auth_headers(provider)
        params = {'category_id': category_id}

        if limit:
            params['limit'] = limit

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        tours = data.get('data', {}).get('tours', [])  # Adjust path

        return tours

    def sync_single_tour(self, provider, mapper, tour_id):
        """Sync a single tour by ID."""
        # Implementation for single tour sync
        pass

    def sync_tour_periods(self, tour, tour_data, provider, mapper):
        """Sync periods for a tour."""
        # Implementation for period sync
        pass

    def _get_auth_headers(self, provider):
        """Build authentication headers."""
        return {'Content-Type': 'application/json'}
```

#### Category-Based Sync Pattern Summary

**Commands to run**:

```bash
# Step 1: Discover categories (one-time setup)
docker-compose exec web python manage.py sync_{provider}_categories

# Step 2: Configure categories in Django Admin
# - Set is_active=True for desired categories
# - Adjust priority for sync order

# Step 3: Sync all active categories
docker-compose exec web python manage.py sync_{provider}

# Sync specific category
docker-compose exec web python manage.py sync_{provider} --category-id 59

# Test with limited tours per category
docker-compose exec web python manage.py sync_{provider} --limit 5
```

**Benefits**:
- **Runtime control**: Enable/disable categories without code changes
- **Selective sync**: Sync only specific categories
- **Priority ordering**: Control sync order for rate-limited APIs
- **Metadata tracking**: Monitor tour counts and sync times per category
- **Easier debugging**: Isolate issues to specific categories

**Reference implementation**:
- **Provider**: Unique Inter
- **Category discovery**: `wholesale/management/commands/sync_unique_inter_categories.py`
- **Main sync**: `wholesale/management/commands/sync_unique_inter.py`
- **Model**: `wholesale/models.ProviderCategory`

## Common Patterns

### Pattern 1: Nested Data Extraction

Many APIs nest related data:

```python
# API response with nested periods
{
  "tour": {
    "id": "T001",
    "name": "Tour Name",
    "dates": [  # Nested periods
      {"start": "2026-03-15", "price": 25000},
      {"start": "2026-04-20", "price": 28000}
    ]
  }
}

# Sync command pattern
def sync_tours(self, provider, mapper, options):
    tours = self.fetch_tours_from_api()

    for tour_data in tours:
        # Create tour
        tour = ProgramTour.objects.create(...)

        # Extract nested periods
        for period_data in tour_data.get('dates', []):
            period_fields = mapper.map_period_data(period_data, tour, provider)
            Period.objects.create(**period_fields)
```

### Pattern 2: Pagination Handling

For APIs with paginated responses:

```python
def fetch_all_tours(self, provider):
    """Fetch all tours handling pagination."""
    all_tours = []
    page = 1

    while True:
        response = self.make_api_request(
            provider,
            '/tours',
            params={'page': page, 'per_page': 100}
        )
        data = response.json()

        tours = data.get('data', [])
        if not tours:
            break

        all_tours.extend(tours)

        # Check if more pages
        if not data.get('has_more', False):
            break

        page += 1

    return all_tours
```

### Pattern 3: Rate Limiting

For APIs with rate limits:

```python
import time

def sync_tours(self, provider, mapper, options):
    tours = self.fetch_tours_from_api()

    for i, tour_data in enumerate(tours):
        # Sync tour
        self.sync_single_tour(tour_data, provider, mapper)

        # Rate limiting: pause every 10 requests
        if (i + 1) % 10 == 0:
            self.stdout.write('  Pausing for rate limit...')
            time.sleep(2)  # Wait 2 seconds
```

## Tools to Use

- **Read** - Read existing mapper/normalizer/command files for patterns
- **Grep** - Search for similar provider implementations
- **Write** - Generate new mapper, normalizer, and command files
- **Edit** - Update existing files (admin.py, models.py)
- **Bash** - Test sync commands and API connectivity
- **WebFetch** - Fetch provider API documentation if available

## Expected Output

Provide the user with:

1. **Complete mapper class** - Ready to add to `wholesale/provider_mappers.py`
2. **Normalizer class** (if needed) - Ready to add to `wholesale/field_normalizers.py`
3. **Management command** - Ready to create as `wholesale/management/commands/sync_{provider}.py`
4. **Admin updates** - Code to add to `wholesale/admin.py`
5. **Model changes** (if needed) - New fields with migration commands
6. **Documentation** - Provider guide in `docs/provider-integration/`
7. **Testing checklist** - Step-by-step verification steps
8. **Example commands** - How to run the sync

## Success Criteria

- ✅ Mapper extracts all relevant fields from API responses
- ✅ Normalizer handles provider-specific data formats
- ✅ Sync command successfully creates database records
- ✅ No constraint violations or silent failures
- ✅ Data appears correctly in Django admin
- ✅ Provider documented in codebase
- ✅ Integration follows existing patterns and conventions
