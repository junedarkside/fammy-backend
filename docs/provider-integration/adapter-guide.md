# Provider Adapter Implementation Guide

**Version:** 3.0
**Last Updated:** 2026-01-15
**Target Audience:** Backend developers integrating new tour operators
**Status**: Enhanced with Mapper Pattern and Data Completeness Tracking

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start Checklist](#quick-start-checklist)
4. [Step 1: Register Provider](#step-1-register-provider)
5. [Step 2: Create API Service](#step-2-create-api-service)
6. [Step 3: Create Mapper Class](#step-3-create-mapper-class)
7. [Step 4: Register in Factory](#step-4-register-in-factory)
8. [Step 5: Create Management Command](#step-5-create-management-command)
9. [Step 6: Test Your Adapter](#step-6-test-your-adapter)
10. [Handling Missing Data](#handling-missing-data)
11. [Standardization Rules](#standardization-rules)
12. [Troubleshooting](#troubleshooting)
13. [Real-World Examples](#real-world-examples)

---

## Overview

### What is a Provider Adapter?

A **Provider Adapter** connects external tour operator APIs to our B2B platform. It handles API communication, data transformation, and integration.

### Current Implementation Status

**Note**: This platform is in **development phase**. Database models are being refined, so full data integration is not yet available.

### Current Providers

| Provider | Code | Status | Notes |
|----------|------|--------|-------|
| Zego Travel | `zego` | ✅ Base Service Implemented | API service created |
| Unique Inter | `unique_inter` | ✅ Base Service Implemented | API service created |

### What's Working
- `BaseAPIService` class for common API operations
- `APIServiceFactory` for service creation
- Authentication handling
- Basic error handling

### What's Being Developed
- Database models (currently commented out)
- Data transformation services
- Synchronization commands
- Advanced error handling

---

## Before You Start: Use the Evaluation Tool

**⚡ New!** Before manually creating an adapter, use the [Provider Adapter Evaluation Tool](evaluation-tool.md) to:
- **Check compatibility** with existing adapters (Zego, Unique Inter, Go365, CheckIn Group)
- **Get automatic code generation** for new adapters
- **Receive step-by-step guidance** for implementation
- **Save development time** by identifying reuse opportunities

The evaluation tool analyzes your provider's API structure and recommends the best integration approach.

### Access the Tool

```
http://localhost:8000/wholesale/evaluation/
```

### When to Use the Evaluation Tool

✅ **Use the tool when:**
- You have a new provider API to integrate
- You want to check compatibility before committing to an approach
- You need help deciding on adapter architecture
- You want boilerplate code generation

❌ **Skip the tool when:**
- Making minor tweaks to existing adapters
- You already know the provider uses identical structure to an existing one
- Working with non-standard integration requirements

### Quick Evaluation Workflow

1. **Gather API samples** from your provider
2. **Access evaluation tool** at http://localhost:8000/wholesale/evaluation/
3. **Upload API responses** (use Smart Paste Helper for nested data)
4. **Review analysis** and compatibility scores
5. **Follow recommendations:**
   - 95-100% match → Reuse existing adapter (no code!)
   - 80-94% match → Reuse with minor changes
   - 50-79% match → Create field normalizer
   - <50% match → Create new adapter (code generated for you)

See [Evaluation Tool Guide](evaluation-tool.md) for complete instructions.

---

## Simple Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Provider API                     │
│                  (e.g., Zego, Unique Inter)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Service Layer                          │
│            (wholesale/api_service.py)                        │
│  - Handles HTTP requests                                     │
│  - Provider-specific authentication                          │
│  - Returns raw JSON responses                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Mapper Layer                          │
│         (wholesale/data_sync_service.py)                     │
│  - Transforms raw API data                                   │
│  - Maps to ProgramTour/Period fields                         │
│  - Standardizes pricing structure                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Models                            │
│              (wholesale/models.py)                           │
│  - Provider (wholesaler info)                                │
│  - ProgramTour (tour programs)                               │
│  - Period (departure dates)                                  │
│  - Country, Itinerary, Flight (related data)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Management Command                         │
│    (wholesale/management/commands/sync_*.py)                 │
│  - Orchestrates sync process                                 │
│  - Handles errors and reporting                              │
│  - Provides CLI interface                                    │
└─────────────────────────────────────────────────────────────┘
```

### Enhanced Architecture (v3.0)

```
┌─────────────────────────────────────────────────────────────┐
│                    External Provider API                     │
│                  (e.g., Zego, Unique Inter)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Service Layer                          │
│            (wholesale/api_service.py)                        │
│  - Handles HTTP requests                                     │
│  - Provider-specific authentication                          │
│  - Returns raw JSON responses                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Field Normalizer Layer                     │
│         (wholesale/field_normalizers.py)                     │
│  - Normalizes prices, dates, booleans                        │
│  - Provider-specific normalizers                             │
│  - Handles format variations                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Mapper Layer                               │
│         (wholesale/provider_mappers.py)                      │
│  - Transforms raw API data to model fields                   │
│  - Provider-specific mapping logic                           │
│  - Handles missing data gracefully                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Models                            │
│              (wholesale/models.py)                           │
│  - Provider (wholesaler info)                                │
│  - ProgramTour (tour programs)                               │
│  - Period (departure dates)                                  │
│  - Country, Itinerary, Flight (related data)                 │
│  - Data completeness tracking fields                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Management Command                         │
│    (wholesale/management/commands/sync_*.py)                 │
│  - Orchestrates sync process                                 │
│  - Handles errors and reporting                              │
│  - Provides CLI interface                                    │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Fetch:** Management command calls API Service
2. **Normalize:** Field Normalizer standardizes data formats
3. **Map:** Provider Mapper converts to model fields
4. **Store:** Django ORM saves to database with completeness flags

### New Features in v3.0

- **Mapper Classes**: Organized provider-specific transformation logic
- **Field Normalizers**: Reusable data normalization utilities
- **Data Completeness Tracking**: Flags for what data each provider has
- **Graceful Degradation**: Handle missing data without errors
- **Centralized Mappings**: Configuration-driven field mappings

---

## Quick Start Checklist

- [ ] Register Provider in database
- [ ] Create API Service class (if not using GenericAPIService)
- [ ] Create Mapper class for your provider
- [ ] Register Mapper in APIServiceFactory
- [ ] Create management command
- [ ] Test with sample data
- [ ] Set data completeness flags appropriately

**Estimated Time:** 2-4 hours for a standard REST API provider

---

## Step 1: Register Provider

### 1.1 Create Provider Record

Open Django shell or admin panel:

```bash
python manage.py shell
```

```python
from wholesale.models import Provider

provider = Provider.objects.create(
    name='Example Travel Wholesale',
    code='example',  # Unique identifier (lowercase, no spaces)
    base_url='https://api.example.com',
    token='your-api-key-here',  # Or leave blank if using other auth
    is_active=True,
    extra={
        # Optional: Store any provider-specific config
        'api_version': 'v2',
        'user_email': 'your-email@example.com',
        'timeout': 60
    }
)
```

### 1.2 Provider Model Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `name` | CharField | Display name | ✅ Yes |
| `code` | CharField | Unique identifier (slug) | ✅ Yes |
| `base_url` | URLField | API base URL | ✅ Yes |
| `token` | CharField | API token/key | ⚠️ If using token auth |
| `is_active` | BooleanField | Enable/disable sync | ✅ Yes (default True) |
| `extra` | JSONField | Custom configuration | ❌ No |

### 1.3 Verify Registration

```bash
python manage.py shell
```

```python
from wholesale.models import Provider

# Check provider exists
provider = Provider.objects.get(code='example')
print(f"Provider: {provider.name}")
print(f"Base URL: {provider.base_url}")
print(f"Active: {provider.is_active}")
```

---

## Step 2: Create API Service

### 2.1 Create API Service Class

**File:** `wholesale/api_service.py`

Add your provider's API service class:

```python
class ExampleAPIService(BaseAPIService):
    """
    API client for Example Travel Wholesale.

    Authentication: API Key in header
    Base URL: https://api.example.com
    """

    def _setup_authentication(self):
        """Setup API key authentication"""
        if self.token:
            self.session.headers.update({
                'X-API-Key': self.token,  # Adjust header name as needed
                'Authorization': f'Bearer {self.token}'  # Or use Bearer token
            })

    def get_countries(self) -> Optional[List[Dict]]:
        """
        Fetch all countries from provider.

        Returns:
            List of country dicts or None if request fails
        """
        return self._make_request('countries')

    def get_program_tours(self, country_code: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Fetch all tour programs.

        Args:
            country_code: Optional filter by country

        Returns:
            List of tour program dicts or None if request fails
        """
        params = {}
        if country_code:
            params['country'] = country_code

        return self._make_request('tours', params=params)

    def get_program_tour_details(self, tour_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific tour.

        Args:
            tour_id: External tour ID from provider

        Returns:
            Tour detail dict or None if request fails
        """
        return self._make_request(f'tours/{tour_id}')

    def get_departures(self, tour_id: str) -> Optional[List[Dict]]:
        """
        Fetch departure dates (periods) for a tour.

        Args:
            tour_id: External tour ID from provider

        Returns:
            List of departure dicts or None if request fails
        """
        return self._make_request(f'tours/{tour_id}/departures')
```

### 2.2 Register in APIServiceFactory

Find the `APIServiceFactory.create_service()` method in `api_service.py` and add your provider:

```python
class APIServiceFactory:
    @staticmethod
    def create_service(provider) -> Optional[BaseAPIService]:
        """Factory method to create appropriate API service based on provider code"""
        service_map = {
            'zego': ZegoAPIService,
            'unique_inter': UniqueInterAPIService,
            'example': ExampleAPIService,  # Add your provider here
        }

        service_class = service_map.get(provider.code)
        if service_class:
            return service_class(provider)
        else:
            logger.warning(f"No API service found for provider: {provider.code}")
            return None
```

### 2.3 Authentication Patterns

**API Key in Header:**
```python
def _setup_authentication(self):
    self.session.headers.update({
        'X-API-Key': self.token
    })
```

**Bearer Token:**
```python
def _setup_authentication(self):
    self.session.headers.update({
        'Authorization': f'Bearer {self.token}'
    })
```

**Basic Auth:**
```python
def _setup_authentication(self):
    from requests.auth import HTTPBasicAuth
    username = self.provider.extra.get('username', '')
    password = self.token
    self.session.auth = HTTPBasicAuth(username, password)
```

**Custom Auth (e.g., OAuth):**
```python
def _setup_authentication(self):
    # Implement OAuth flow
    token = self._get_oauth_token()
    self.session.headers.update({
        'Authorization': f'Bearer {token}'
    })

def _get_oauth_token(self):
    # OAuth token retrieval logic
    pass
```

---

## Step 3: Create Mapper Class

### 3.1 Understanding the Mapper Pattern

Instead of standalone functions, we use **Mapper Classes** that:

1. **Encapsulate** all provider-specific transformation logic
2. **Inherit** from `ProviderMapper` base class
3. **Use** field normalizers for data standardization
4. **Handle** missing data gracefully with completeness flags

### 3.2 Create Your Mapper Class

**File:** `wholesale/provider_mappers.py`

```python
from typing import Dict
from .provider_mappers import ProviderMapper
from .field_normalizers import FieldNormalizer

class ExampleMapper(ProviderMapper):
    """
    Mapper for Example Travel Wholesale provider.

    This provider has:
    - Tour data with duration in "7D6N" format
    - Limited pricing (adult, child only)
    - No flight schedules (only airline names)
    - No itineraries (in PDF documents)
    """

    def __init__(self, provider):
        super().__init__(provider)
        # Use default normalizer or create provider-specific one
        self.normalizer = FieldNormalizer()

    def map_tour_data(self, raw_data: Dict) -> Dict:
        """
        Map Example provider tour data to standard format.

        Returns dict with all ProgramTour fields.
        """
        # Parse duration from "7D6N" format
        duration = raw_data.get('duration', '')
        days, nights = 0, 0
        if 'D' in duration and 'N' in duration:
            parts = duration.split('D')
            days = self.normalizer.normalize_integer(parts[0])
            nights = self.normalizer.normalize_integer(
                parts[1].replace('N', '')
            )

        # Get country
        country_name = raw_data.get('country', '')
        country = self._get_or_create_country(country_name)

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('tour_id', '')),
            'code': raw_data.get('tour_code', ''),
            'name': raw_data.get('tour_name', ''),
            'days': days,
            'nights': nights,
            'country': country,
            'country_name': country_name,
            'airline_name': raw_data.get('airline', ''),
            'file_pdf': raw_data.get('pdf_url', ''),
            'image_url': raw_data.get('image', ''),
            'highlight': raw_data.get('description', ''),
            # Data completeness flags
            'has_flights': False,  # No flight schedules
            'has_itineraries': False,  # Itineraries in PDF
            'has_full_pricing': False,  # Limited pricing
            'data_quality_score': 60,  # Lower due to missing data
        }

    def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        Map Example provider period data to standard format.

        Uses JSONField for pricing flexibility.
        """
        # Build pricing JSONField
        base_prices = {
            'adult': self.normalizer.normalize_price(
                raw_data.get('price_adult')
            ),
            'child': self.normalizer.normalize_price(
                raw_data.get('price_child')
            ),
            # Other pricing types not available - will be null
        }

        # Determine status from availability
        available = self.normalizer.normalize_integer(
            raw_data.get('available_seats')
        )
        if available <= 0:
            status = 'Soldout'
        elif available <= 5:
            status = 'Waitlist'
        else:
            status = 'Book'

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('departure_id', '')),
            'code': raw_data.get('departure_code', ''),
            'program_id': program_tour.id if program_tour else None,
            'start_date': self.normalizer.normalize_date(
                raw_data.get('start_date')
            ),
            'end_date': self.normalizer.normalize_date(
                raw_data.get('end_date')
            ),
            'country_name': raw_data.get('country', ''),
            'airline_name': raw_data.get('airline', ''),
            'seats': available,
            'status': status,
            'base_prices': base_prices,
        }

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        """
        Example provider doesn't provide flight schedules.

        Raise NotImplementedError to make this explicit.
        """
        raise NotImplementedError(
            "Example provider does not provide flight schedule data. "
            "Only airline names are available in tour data."
        )

    def map_itinerary_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        Example provider doesn't provide itinerary data.

        Itineraries are only available in PDF documents.
        """
        raise NotImplementedError(
            "Example provider does not provide itinerary data in API. "
            "Itineraries are only available in PDF documents."
        )
```

### 3.3 Field Normalization

Use the built-in field normalizers for common transformations:

```python
from wholesale.field_normalizers import FieldNormalizer

normalizer = FieldNormalizer()

# Price normalization (handles various formats)
price = normalizer.normalize_price("25,000")  # Decimal('25000')
price = normalizer.normalize_price("25+1")    # Decimal('26')

# Date normalization (handles various formats)
date = normalizer.normalize_date("2025-01-15")      # datetime.date
date = normalizer.normalize_date("15/01/2025")     # datetime.date

# Boolean normalization (Y/N, true/false, 1/0)
has_meals = normalizer.normalize_boolean("Y")      # True
has_meals = normalizer.normalize_boolean("true")   # True

# Text normalization (removes artifacts)
text = normalizer.normalize_text("Line 1\r\nLine 2")  # "Line 1 Line 2"
```

### 3.4 Handling Missing Data

Set the data completeness flags appropriately:

```python
# Full data (like Zego)
'has_flights': True,
'has_itineraries': True,
'has_full_pricing': True,
'data_quality_score': 100,

# Partial data (like Unique Inter)
'has_flights': False,        # No flight schedules
'has_itineraries': False,    # Itineraries in PDF
'has_full_pricing': False,   # Only 3 pricing types
'data_quality_score': 60,    # Lower score

# Unknown provider
'has_flights': True,
'has_itineraries': True,
'has_full_pricing': True,
'data_quality_score': 50,    # Conservative default
```

---

## Step 4: Register in Factory

Register your mapper in the APIServiceFactory.

**File:** `wholesale/api_service.py`

Add your provider to the `create_mapper()` method:

```python
@staticmethod
def create_mapper(provider):
    """Create appropriate mapper for provider"""
    from .provider_mappers import (
        ZegoMapper,
        UniqueInterMapper,
        Go365Mapper,
        GenericMapper,
        ExampleMapper  # Add your mapper
    )

    provider_code = provider.code.lower()

    if provider_code == 'example':  # Add your provider
        return ExampleMapper(provider)
    elif provider_code == 'zego':
        return ZegoMapper(provider)
    # ... rest of the mappings
```

---

## Step 5: Create Management Command
    """
    Map Example provider departure data to Period model fields.

    Args:
        raw_data: Raw JSON from Example API

    Returns:
        dict: Mapped data ready for Period.objects.update_or_create()

    Example raw_data structure:
    {
        "departure_id": "DEP12345",
        "departure_code": "EX-2025-01-15",
        "start_date": "2025-01-15",
        "end_date": "2025-01-21",
        "airline": "Thai Airways",
        "airline_code": "TG",
        "total_seats": 30,
        "booked_seats": 15,
        "available_seats": 15,
        "status": "Available",
        "pricing": {
            "adult": 50000,
            "child_with_bed": 40000,
            "child_no_bed": 35000,
            "infant": 10000,
            "single_supplement": 8000,
            "twin_room": 5000,
            "visa_fee": 2500
        },
        "deposit": 15000,
        "commission": {
            "agent": 2500,
            "sale": 1500
        }
    }
    """
    pricing = raw_data.get('pricing', {})
    commission = raw_data.get('commission', {})

    # IMPORTANT: Use standardized pricing keys (12 keys)
    base_prices = {
        'adult': int(pricing.get('adult', 0)),
        'child': int(pricing.get('child_with_bed', 0)),
        'child_nb': int(pricing.get('child_no_bed', 0)),
        'infant': int(pricing.get('infant', 0)),
        'single_bed': int(pricing.get('single_supplement', 0)),  # Use 'single_bed', not 'single'
        'twin_bed': int(pricing.get('twin_room', 0)),
        'double_bed': int(pricing.get('double_room', 0)),
        'triple_bed': int(pricing.get('triple_room', 0)),
        'join_land': int(pricing.get('land_only', 0)),
        'single_visa': int(pricing.get('visa_fee', 0)),
        'group_visa': int(pricing.get('group_visa', 0)),
        'express_visa': int(pricing.get('express_visa', 0)),
    }

    # If provider has promotional pricing, map to end_prices
    # Otherwise, copy base_prices
    end_prices = base_prices.copy()

    # Calculate available seats
    total_seats = int(raw_data.get('total_seats', 0))
    booked = int(raw_data.get('booked_seats', 0))
    available = total_seats - booked

    # Map status
    status = raw_data.get('status', '')
    if available <= 0:
        status = 'Soldout'
    elif available <= 5:
        status = 'Waitlist'
    else:
        status = 'Book'

    return {
        'external_id': str(raw_data.get('departure_id', '')),
        'code': raw_data.get('departure_code', ''),
        'start_date': raw_data.get('start_date'),
        'end_date': raw_data.get('end_date'),
        'bus': raw_data.get('bus_type', ''),
        'country_name': raw_data.get('country', ''),
        'airline_code': raw_data.get('airline_code', ''),
        'airline_name': raw_data.get('airline', ''),
        'airport': raw_data.get('departure_airport', ''),
        'group_size': total_seats,
        'booked': booked,
        'seats': available,
        'status': status,
        'promotion': raw_data.get('promotion_code', ''),
        'base_prices': base_prices,  # Standardized structure
        'end_prices': end_prices,
        'deposit': raw_data.get('deposit', 0),
        'deposit_end': raw_data.get('deposit', 0),  # Or promotional deposit
        'com_agent': commission.get('agent', 0),
        'com_agent_end': commission.get('agent', 0),
        'com_sale': commission.get('sale', 0),
        'com_sale_end': commission.get('sale', 0),
        'update_date': timezone.now(),
    }
```

### 3.3 Helper Functions

Add utility functions for data cleaning:

```python
def clean_example_price(value: Any) -> int:
    """
    Clean price values from Example provider.

    Handles: strings, floats, None, empty values
    """
    if value is None or value == '':
        return 0

    try:
        # Remove currency symbols and commas
        if isinstance(value, str):
            value = value.replace(',', '').replace('฿', '').replace('$', '').strip()
        return int(float(value))
    except (ValueError, TypeError):
        logger.warning(f"Could not parse price value: {value}")
        return 0

def clean_example_date(value: str) -> Optional[str]:
    """
    Clean and standardize date values.

    Converts various formats to YYYY-MM-DD
    """
    if not value:
        return None

    try:
        # Try parsing common formats
        from datetime import datetime

        # Format: "15/01/2025" -> "2025-01-15"
        if '/' in value:
            dt = datetime.strptime(value, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d')

        # Format: "2025-01-15" (already correct)
        if '-' in value and len(value) == 10:
            return value

        return None
    except ValueError:
        logger.warning(f"Could not parse date: {value}")
        return None
```

---

## Step 4: Create Management Command

### 4.1 Create Command File

**File:** `wholesale/management/commands/sync_example.py`

```python
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from wholesale.models import Provider, ProgramTour, Period
from wholesale.api_service import APIServiceFactory
from wholesale.data_sync_service import (
    map_example_tour_data,
    map_example_period_data,
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync data from Example Travel Wholesale API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider-code',
            type=str,
            default='example',
            help='Provider code (default: example)'
        )
        parser.add_argument(
            '--tours-only',
            action='store_true',
            help='Only sync tours, skip periods'
        )
        parser.add_argument(
            '--periods-only',
            action='store_true',
            help='Only sync periods for existing tours'
        )
        parser.add_argument(
            '--tour-id',
            type=str,
            help='Sync specific tour only'
        )

    def handle(self, *args, **options):
        provider_code = options.get('provider_code', 'example')

        # Get provider
        try:
            provider = Provider.objects.get(code=provider_code)
        except Provider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Provider "{provider_code}" not found. Please create it first.'
                )
            )
            return

        if not provider.is_active:
            self.stdout.write(
                self.style.WARNING(
                    f'Provider "{provider_code}" is not active. Enable it first.'
                )
            )
            return

        # Create API service
        api_service = APIServiceFactory.create_service(provider)
        if not api_service:
            self.stdout.write(
                self.style.ERROR(f'Could not create API service for {provider_code}')
            )
            return

        # Sync tours (unless --periods-only)
        if not options.get('periods_only'):
            self.sync_tours(provider, api_service, options.get('tour_id'))

        # Sync periods (unless --tours-only)
        if not options.get('tours_only'):
            self.sync_periods(provider, api_service, options.get('tour_id'))

        self.stdout.write(
            self.style.SUCCESS(f'✓ Sync completed for {provider.name}')
        )

    @transaction.atomic
    def sync_tours(self, provider, api_service, tour_id_filter=None):
        """Sync tour programs"""
        self.stdout.write(
            self.style.WARNING('Syncing tour programs...')
        )

        # Fetch tours
        if tour_id_filter:
            raw_data = api_service.get_program_tour_details(tour_id_filter)
            raw_tours = [raw_data] if raw_data else []
        else:
            raw_tours = api_service.get_program_tours()

        if not raw_tours:
            self.stdout.write(
                self.style.WARNING('No tours found')
            )
            return

        tours_created = 0
        tours_updated = 0
        errors = 0

        for raw_tour in raw_tours:
            try:
                tour_data = map_example_tour_data(raw_tour)
                external_id = tour_data.pop('external_id')

                tour, created = ProgramTour.objects.update_or_create(
                    provider=provider,
                    external_id=external_id,
                    defaults=tour_data
                )

                if created:
                    tours_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created: {tour.name}')
                    )
                else:
                    tours_updated += 1

            except Exception as e:
                errors += 1
                logger.error(f"Error syncing tour: {e}")
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error: {str(e)}')
                )

        self.stdout.write('')
        self.stdout.write(f'Tours created: {tours_created}')
        self.stdout.write(f'Tours updated: {tours_updated}')
        if errors > 0:
            self.stdout.write(
                self.style.ERROR(f'Errors: {errors}')
            )

    @transaction.atomic
    def sync_periods(self, provider, api_service, tour_id_filter=None):
        """Sync departure periods"""
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING('Syncing departure periods...')
        )

        # Get tours to sync periods for
        queryset = ProgramTour.objects.filter(provider=provider)
        if tour_id_filter:
            queryset = queryset.filter(external_id=tour_id_filter)

        if not queryset.exists():
            self.stdout.write(
                self.style.WARNING('No tours found to sync periods')
            )
            return

        periods_created = 0
        periods_updated = 0
        errors = 0

        for tour in queryset:
            try:
                # Fetch departures for this tour
                raw_departures = api_service.get_departures(tour.external_id)

                if not raw_departures:
                    continue

                for raw_departure in raw_departures:
                    try:
                        period_data = map_example_period_data(raw_departure)
                        external_id = period_data.pop('external_id')

                        period, created = Period.objects.update_or_create(
                            provider=provider,
                            external_id=external_id,
                            program=tour,
                            defaults=period_data
                        )

                        if created:
                            periods_created += 1
                        else:
                            periods_updated += 1

                    except Exception as e:
                        errors += 1
                        logger.error(f"Error syncing period: {e}")

            except Exception as e:
                errors += 1
                logger.error(f"Error syncing periods for tour {tour.code}: {e}")

        self.stdout.write('')
        self.stdout.write(f'Periods created: {periods_created}')
        self.stdout.write(f'Periods updated: {periods_updated}')
        if errors > 0:
            self.stdout.write(
                self.style.ERROR(f'Errors: {errors}')
            )
```

### 4.2 Command Usage Examples

```bash
# Full sync (tours + periods)
python manage.py sync_example

# Sync tours only
python manage.py sync_example --tours-only

# Sync periods only
python manage.py sync_example --periods-only

# Sync specific tour
python manage.py sync_example --tour-id EX12345

# Use custom provider code
python manage.py sync_example --provider-code example_v2
```

---

## Step 5: Test Your Adapter

### 5.1 Test API Connection

```bash
python manage.py shell
```

```python
from wholesale.models import Provider
from wholesale.api_service import APIServiceFactory

# Get provider
provider = Provider.objects.get(code='example')

# Create API service
api_service = APIServiceFactory.create_service(provider)

# Test connection
if api_service.test_connection():
    print("✓ API connection successful")
else:
    print("✗ API connection failed")

# Test data fetch
tours = api_service.get_program_tours()
print(f"Fetched {len(tours)} tours")
print(f"Sample tour: {tours[0]}")
```

### 5.2 Test Data Mapping

```python
from wholesale.data_sync_service import map_example_tour_data, map_example_period_data

# Test tour mapping
sample_tour = {
    "tour_id": "EX12345",
    "tour_code": "EXAMPLE-001",
    "tour_name": "Test Tour",
    "duration": "7D6N",
    "country": "Thailand"
}

mapped_tour = map_example_tour_data(sample_tour)
print("Mapped tour data:")
print(mapped_tour)

# Test period mapping
sample_period = {
    "departure_id": "DEP001",
    "start_date": "2025-01-15",
    "end_date": "2025-01-21",
    "pricing": {"adult": 50000, "single_supplement": 8000}
}

mapped_period = map_example_period_data(sample_period)
print("Mapped period data:")
print(mapped_period['base_prices'])
```

### 5.3 Test Full Sync

```bash
# Dry run: Check what would be synced
python manage.py sync_example --tour-id EX12345

# Check database
python manage.py shell
```

```python
from wholesale.models import ProgramTour, Period

# Verify tour was created
tour = ProgramTour.objects.get(code='EXAMPLE-001')
print(f"Tour: {tour.name}")
print(f"Days: {tour.days}, Nights: {tour.nights}")

# Verify periods
periods = Period.objects.filter(program=tour)
print(f"Periods: {periods.count()}")

# Check pricing structure
if periods.exists():
    period = periods.first()
    print(f"Base prices: {period.base_prices}")
    print(f"Has standard keys: {'single_bed' in period.base_prices}")
```

### 5.4 Validation Checklist

- [ ] API service connects successfully
- [ ] Tours are created/updated correctly
- [ ] Periods are linked to correct tours
- [ ] Pricing JSON has all 12 standardized keys
- [ ] Dates are in YYYY-MM-DD format
- [ ] Available seats calculated correctly
- [ ] No duplicate records (check `unique_together`)
- [ ] Error handling works for invalid data

---

## Best Practices: Management Commands

### Always Use Safe Dictionary Access for Optional Arguments

When writing Django management commands that may be called from multiple contexts (CLI, Django Admin, programmatic), always use `.get()` method for accessing optional arguments:

```python
def handle(self, *args, **options):
    # ✅ GOOD - Safe access, works in all contexts
    tour_id = options.get('tour_id')
    if tour_id:
        tours = [service.get_program_tour_details(tour_id)]
    else:
        tours = service.get_program_tours()

    # ❌ BAD - Raises KeyError when called from Django Admin
    if options['tour_id']:
        tours = [service.get_program_tour_details(options['tour_id'])]
```

**Why This Matters:**

When a management command is called from different contexts:
- **CLI**: `python manage.py sync_provider` - All arguments present (with defaults)
- **Django Admin**: `cmd.handle()` - Optional arguments may NOT exist in dict
- **Programmatic**: `command.handle()` - Same as Admin
- **Celery Tasks**: May not pass all arguments

**The Problem:**
Direct dictionary access `options['key']` raises `KeyError` if the key doesn't exist. When Django Admin calls `handle()` without arguments, the `options` dict may not contain keys for optional arguments.

**The Solution:**
Use `options.get('key')` which returns `None` if the key doesn't exist, preventing the `KeyError`.

### Required vs Optional Arguments

**Required Arguments:**
```python
def add_arguments(self, parser):
    parser.add_argument('provider-code',  # No leading dashes = required
                       type=str,
                       help='Provider code (required)')
```

**Optional Arguments:**
```python
def add_arguments(self, parser):
    parser.add_argument('--tour-id',  # Leading dashes = optional
                       type=int,
                       help='Sync specific tour by ID')
```

### Access Pattern

```python
def handle(self, *args, **options):
    # Required: Can use direct access (but .get() is still safer)
    provider_code = options.get('provider_code')

    # Optional: ALWAYS use .get()
    tour_id = options.get('tour_id')
    dry_run = options.get('dry_run', False)
    tours_only = options.get('tours_only', False)

    # Check for truthiness
    if tour_id:
        # Sync specific tour
        pass
    else:
        # Sync all tours
        pass
```

### Real-World Example: CheckIn Group Fix

**Issue:** When syncing CheckIn Group from Django Admin, the command failed with:
```
Error syncing 'CheckIn Group': 'tour_id'
```

**Root Cause:**
```python
# Line 54 in sync_checkingroup.py (BEFORE)
if options['tour_id']:  # KeyError when key doesn't exist
    tours = [service.get_program_tour_details(options['tour_id'])]
```

**Fix Applied:**
```python
# Line 54-56 in sync_checkingroup.py (AFTER)
tour_id = options.get('tour_id')
if tour_id:
    tours = [service.get_program_tour_details(tour_id)]
```

Also fixed similar issues on lines 66 and 94 for `dry_run` and `tours_only` arguments.

### Checklist for Management Commands

Before deploying a new management command, verify:

- [ ] All optional arguments accessed via `.get()`
- [ ] Required arguments have fallback values in `.get()` if needed
- [ ] Command works from CLI with no arguments
- [ ] Command works from Django Admin "Sync Now" button
- [ ] Command works when called programmatically
- [ ] No direct dictionary access like `options['key']` for optional args

---

## Standardization Rules

### Critical: Pricing Structure

**ALL providers MUST use these 12 pricing keys:**

```python
base_prices = {
    'adult': int,           # Adult price
    'child': int,           # Child with bed
    'child_nb': int,        # Child no bed
    'infant': int,          # Infant price
    'single_bed': int,      # Single room supplement (NOT 'single')
    'twin_bed': int,        # Twin room supplement
    'double_bed': int,      # Double room supplement
    'triple_bed': int,      # Triple room supplement
    'join_land': int,       # Land-only package
    'single_visa': int,     # Individual visa fee
    'group_visa': int,      # Group visa fee
    'express_visa': int,    # Express visa fee
}
```

**If your provider doesn't have a field, set it to `0`**

❌ **WRONG:**
```python
base_prices = {
    'adult': 50000,
    'single': 8000,  # Wrong key name
}
```

✅ **CORRECT:**
```python
base_prices = {
    'adult': 50000,
    'child': 0,
    'child_nb': 0,
    'infant': 0,
    'single_bed': 8000,  # Correct key name
    'twin_bed': 0,
    'double_bed': 0,
    'triple_bed': 0,
    'join_land': 0,
    'single_visa': 0,
    'group_visa': 0,
    'express_visa': 0,
}
```

### Date Format

**Always use:** `YYYY-MM-DD` (ISO 8601)

```python
'start_date': '2025-01-15',  # ✅ Correct
'start_date': '15/01/2025',  # ❌ Wrong
'start_date': '01-15-2025',  # ❌ Wrong
```

### External IDs

**Must be unique per provider:**

```python
# Good: Use provider's unique identifier
'external_id': 'EX12345'

# Bad: Using non-unique field
'external_id': 'Thailand Tour'  # Multiple tours could have same name
```

### Nullable Fields

**Set to empty string or 0 if not provided:**

```python
'airline_code': raw_data.get('airline_code', ''),  # Empty string for missing text
'bus': '',  # Empty if not provided
'airport': '',
'group_size': int(raw_data.get('seats', 0)),  # 0 for missing numbers
```

### Country Handling

**Prefer Country FK over country_name:**

```python
# Good: Create Country object
country_obj, _ = Country.objects.get_or_create(
    provider=provider,
    name=country_name,
    defaults={'iso_code': 'THA'}
)
tour_data['country'] = country_obj

# Acceptable: Store name only if Country not available
tour_data['country'] = None
tour_data['country_name'] = country_name
```

---

## Troubleshooting

### Issue: "Provider not found"

**Cause:** Provider not registered in database

**Solution:**
```python
from wholesale.models import Provider
Provider.objects.create(
    name='Example Travel',
    code='example',
    base_url='https://api.example.com',
    token='your-token'
)
```

### Issue: "No API service found for provider"

**Cause:** API service class not registered in `APIServiceFactory`

**Solution:** Add your service class to the factory's `service_map` dictionary in `wholesale/api_service.py`

### Issue: "UNIQUE constraint failed"

**Cause:** Trying to create duplicate record with same `provider + external_id`

**Solution:**
- Verify `external_id` is truly unique in provider's API
- Use `update_or_create()` instead of `create()`
- Check for duplicate data in API response

### Issue: "KeyError: 'single_bed'"

**Cause:** Frontend/API expecting standardized pricing keys

**Solution:** Ensure your mapper includes all 12 pricing keys (set missing ones to 0)

### Issue: "Invalid date format"

**Cause:** Date not in YYYY-MM-DD format

**Solution:** Add date cleaning function:
```python
def clean_example_date(value: str) -> str:
    from datetime import datetime
    if '/' in value:
        dt = datetime.strptime(value, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    return value
```

### Issue: "Request timeout"

**Cause:** API is slow or unresponsive

**Solution:**
- Increase timeout in `_make_request()` call
- Add retry logic
- Check provider's API status
- Use pagination if API supports it

### Issue: "Authentication failed"

**Cause:** Invalid token or wrong auth method

**Solution:**
- Verify token in Provider model
- Check `_setup_authentication()` method
- Test API with curl/Postman first
- Check API documentation for correct auth headers

---

## Real-World Examples

### Example 1: Zego Provider (Standard REST API)

**API Structure:** Straightforward REST endpoints

**Authentication:** API token in header

**Key Features:**
- Separate endpoints for tours and periods
- Rich pricing structure (12 price types)
- Well-structured JSON responses

**Implementation:**
- **API Service:** `ZegoAPIService` in `api_service.py`
- **Mappers:** `transform_pricing_data()`, `_sync_periods()` in `data_sync_service.py`
- **Command:** `sync_zego_data` management command

**Usage:**
```bash
python manage.py sync_zego_data
python manage.py sync_zego_data --wholesaler "Zego Travel"
python manage.py sync_zego_data --tours-only
```

### Example 2: Unique Inter Provider (Two-Stage Sync)

**API Structure:** Departure-centric (not tour-centric)

**Authentication:** Email-based API key

**Key Features:**
- Categories (destinations) instead of countries
- Each API record = one departure date
- Raw data stored before processing (two-stage)

**Implementation:**
- **API Service:** `UniqueInterAPIService` in `api_service.py`
- **Raw Storage:** `RawVendorData` model for preserving original API responses
- **Mappers:** `map_unique_inter_tour_data()`, `map_unique_inter_period_data()` in `data_sync_service.py`
- **Commands:**
  - `sync_unique_inter_categories` - Discover available categories
  - `sync_unique_inter` - Two-stage sync (fetch → process)

**Usage:**
```bash
# First time setup
python manage.py sync_unique_inter_categories

# Full sync
python manage.py sync_unique_inter

# Fetch only (store raw data)
python manage.py sync_unique_inter --fetch-only

# Process only (map existing raw data)
python manage.py sync_unique_inter --process-only

# Sync specific category
python manage.py sync_unique_inter --category 64
```

**When to use two-stage sync:**
- API responses are complex/nested
- Need to preserve original data for debugging
- Data cleaning logic may need refinement
- Provider data format changes frequently

---

## Advanced Topics

### Custom Category Management

If your provider uses categories/regions:

```python
from wholesale.models import ProviderCategory

# Create categories
ProviderCategory.objects.create(
    provider=provider,
    category_id='asia',
    name='Asia Tours',
    is_active=True,
    priority=1
)

# In your command
def handle(self, *args, **options):
    categories = ProviderCategory.objects.filter(
        provider=provider,
        is_active=True
    ).order_by('-priority')

    for category in categories:
        tours = api_service.get_tours(category=category.category_id)
        # ... sync tours
```

### Incremental Sync

Only sync updated records:

```python
def sync_tours(self, provider, api_service):
    # Get last sync time
    last_sync = provider.last_synced or timezone.now() - timedelta(days=30)

    # Fetch only updated tours
    raw_tours = api_service.get_program_tours(updated_since=last_sync)

    # ... sync process

    # Update last sync time
    provider.last_synced = timezone.now()
    provider.save()
```

### Error Recovery

Store failed records for retry:

```python
from wholesale.models import RawVendorData

def sync_with_error_recovery(self, provider, raw_data):
    try:
        # Attempt to process
        tour_data = map_example_tour_data(raw_data)
        tour, _ = ProgramTour.objects.update_or_create(...)

    except Exception as e:
        # Store for later retry
        RawVendorData.objects.create(
            provider=provider,
            external_id=raw_data.get('tour_id'),
            raw_json=raw_data,
            processed=False,
            error_message=str(e)
        )
        logger.error(f"Failed to sync: {e}")
```

---

## Appendix: Model Reference

### ProgramTour Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `external_id` | CharField | ✅ | Provider's tour ID (unique per provider) |
| `code` | CharField | ✅ | Tour code/SKU |
| `name` | CharField | ✅ | Tour name |
| `days` | IntegerField | ❌ | Duration in days |
| `nights` | IntegerField | ❌ | Duration in nights |
| `country` | ForeignKey | ❌ | Country object (preferred) |
| `country_name` | CharField | ❌ | Country name string (fallback) |
| `highlight` | TextField | ❌ | Tour highlights/description |
| `image_url` | URLField | ❌ | Main tour image |
| `airline_name` | CharField | ❌ | Default airline |
| `file_pdf` | URLField | ❌ | PDF itinerary URL |
| `file_word` | URLField | ❌ | Word document URL |
| `last_synced` | DateTimeField | ✅ | Last sync timestamp |

### Period Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `external_id` | CharField | ✅ | Provider's departure ID (unique per provider) |
| `program` | ForeignKey | ✅ | Related ProgramTour |
| `code` | CharField | ✅ | Period code |
| `start_date` | DateField | ✅ | Departure date |
| `end_date` | DateField | ✅ | Return date |
| `airline_name` | CharField | ❌ | Airline for this departure |
| `airline_code` | CharField | ❌ | Airline code |
| `group_size` | IntegerField | ❌ | Total group capacity |
| `booked` | IntegerField | ❌ | Number of bookings |
| `seats` | IntegerField | ❌ | Available seats |
| `status` | CharField | ❌ | Booking status (Book/Waitlist/Soldout) |
| `base_prices` | JSONField | ✅ | Base pricing (12 keys) |
| `end_prices` | JSONField | ✅ | Promotional pricing (12 keys) |
| `deposit` | DecimalField | ❌ | Deposit amount |
| `com_agent` | DecimalField | ❌ | Agent commission |
| `com_sale` | DecimalField | ❌ | Sales commission |

---

## Summary Checklist

When creating a new provider adapter, ensure you have:

- [ ] Registered Provider in database with correct credentials
- [ ] Created API Service class extending `BaseAPIService`
- [ ] Implemented authentication in `_setup_authentication()`
- [ ] Registered API service in `APIServiceFactory`
- [ ] Created tour data mapper with all required fields
- [ ] Created period data mapper with **standardized 12-key pricing**
- [ ] Created management command with proper error handling
- [ ] Tested API connection and data mapping
- [ ] Documented API field mappings in code comments
- [ ] Verified no duplicate records are created
- [ ] Confirmed dates are in YYYY-MM-DD format
- [ ] Tested full sync with real API data

**Estimated Development Time:** 2-4 hours for standard REST API

**Need Help?** Review the Zego and Unique Inter implementations as reference examples.

---

## Performance Optimization Patterns

### Efficient API Requests

#### 1. Connection Pooling
```python
class OptimizedAPIService(BaseAPIService):
    def __init__(self, provider):
        super().__init__(provider)
        # Reuse connections for multiple requests
        self.session = requests.Session()

        # Configure connection pool
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
```

#### 2. Request Batching
```python
def get_multiple_tours(self, tour_ids: List[str]) -> List[Dict]:
    """
    Fetch multiple tours in a single request if API supports it.
    Falls back to individual requests if needed.
    """
    if len(tour_ids) > 50:  # Prevent overly large requests
        # Split into batches
        results = []
        for i in range(0, len(tour_ids), 50):
            batch = tour_ids[i:i+50]
            results.extend(self._get_batch_tours(batch))
        return results

    # Single batch request
    params = {'ids': ','.join(tour_ids)}
    return self._make_request('tours/batch', params=params)
```

#### 3. Pagination Handling
```python
def get_all_tours_paginated(self) -> List[Dict]:
    """
    Handle API pagination efficiently.
    """
    all_tours = []
    page = 1
    page_size = 100  # Optimal page size for this API

    while True:
        params = {
            'page': page,
            'limit': page_size
        }

        response = self._make_request('tours', params=params)

        if not response or not response.get('tours'):
            break

        all_tours.extend(response['tours'])

        # Check if there are more pages
        if len(response['tours']) < page_size:
            break

        page += 1

        # Add small delay to avoid rate limiting
        time.sleep(0.1)

    return all_tours
```

### Database Performance

#### 1. Bulk Operations
```python
@transaction.atomic
def sync_tours_optimized(self, provider, raw_tours: List[Dict]):
    """
    Use bulk operations for better performance.
    """
    tours_to_create = []
    tours_to_update = []

    existing_tours = {
        tour.external_id: tour
        for tour in ProgramTour.objects.filter(provider=provider)
    }

    for raw_tour in raw_tours:
        tour_data = map_example_tour_data(raw_tour)
        external_id = tour_data['external_id']

        if external_id in existing_tours:
            # Update existing
            tour = existing_tours[external_id]
            for key, value in tour_data.items():
                setattr(tour, key, value)
            tours_to_update.append(tour)
        else:
            # Create new
            tours_to_create.append(
                ProgramTour(provider=provider, **tour_data)
            )

    # Bulk create (much faster than individual creates)
    if tours_to_create:
        ProgramTour.objects.bulk_create(tours_to_create, batch_size=100)

    # Bulk update (more efficient than individual saves)
    if tours_to_update:
        ProgramTour.objects.bulk_update(
            tours_to_update,
            fields=['name', 'days', 'nights', 'country', 'highlight', 'image_url'],
            batch_size=100
        )
```

#### 2. Query Optimization
```python
def get_tours_with_periods(self, provider_code: str):
    """
    Fetch tours with related data efficiently.
    """
    return ProgramTour.objects.filter(
        provider__code=provider_code
    ).select_related(
        'provider', 'country'
    ).prefetch_related(
        'period_set'
    ).annotate(
        period_count=Count('period'),
        min_price=Min('period__base_prices__adult')
    )
```

#### 3. Memory-Efficient Processing
```python
def process_large_dataset(self, provider):
    """
    Process large datasets without memory issues.
    """
    # Use iterator() to avoid loading all objects into memory
    tours = ProgramTour.objects.filter(
        provider=provider
    ).iterator(chunk_size=100)

    for tour in tours:
        # Process one tour at a time
        self.process_tour_periods(tour)

        # Clear cache periodically
        if tour.id % 100 == 0:
            django.db.reset_queries()
```

### Caching Strategies

#### 1. API Response Caching
```python
from django.core.cache import cache
from django.conf import settings

class CachedAPIService(BaseAPIService):
    def get_countries(self) -> Optional[List[Dict]]:
        """
        Cache country data since it changes infrequently.
        """
        cache_key = f'{self.provider.code}_countries'
        countries = cache.get(cache_key)

        if not countries:
            countries = super().get_countries()
            if countries:
                # Cache for 24 hours
                cache.set(cache_key, countries, timeout=86400)

        return countries

    def invalidate_cache(self):
        """
        Clear cache when data is updated.
        """
        cache.delete(f'{self.provider.code}_countries')
        cache.delete(f'{self.provider.code}_tours')
```

#### 2. Session-Level Caching
```python
class SessionCachedAPIService(BaseAPIService):
    def __init__(self, provider):
        super().__init__(provider)
        self._cache = {}  # In-memory cache for this session

    def get_tour_details(self, tour_id: str) -> Optional[Dict]:
        """
        Cache tour details within the same sync session.
        """
        cache_key = f'tour_{tour_id}'

        if cache_key in self._cache:
            return self._cache[cache_key]

        tour_data = super().get_tour_details(tour_id)
        if tour_data:
            self._cache[cache_key] = tour_data

        return tour_data
```

### Background Task Optimization

#### 1. Task Chaining
```python
from celery import chain, group

@shared_task
def sync_provider_data_chain(provider_code: str):
    """
    Chain sync tasks for better resource management.
    """
    # Step 1: Fetch countries
    sync_countries_task = sync_countries.s(provider_code)

    # Step 2: Fetch tours (runs after countries)
    sync_tours_task = sync_tours.s(provider_code)

    # Step 3: Process periods (runs after tours)
    sync_periods_task = sync_periods.s(provider_code)

    # Execute as chain
    return chain(
        sync_countries_task,
        sync_tours_task,
        sync_periods_task
    )()
```

#### 2. Parallel Processing
```python
@shared_task
def sync_multiple_providers():
    """
    Sync multiple providers in parallel.
    """
    active_providers = Provider.objects.filter(is_active=True)

    # Create group of parallel tasks
    tasks = group(
        sync_provider_data.s(provider.code)
        for provider in active_providers
    )

    return tasks()
```

#### 3. Progress Tracking
```python
@shared_task(bind=True)
def sync_with_progress(self, provider_code: str):
    """
    Track sync progress for large datasets.
    """
    provider = Provider.objects.get(code=provider_code)
    total_tours = provider.programtour_set.count()

    self.update_state(
        state='PROGRESS',
        meta={'current': 0, 'total': total_tours, 'status': 'Starting sync'}
    )

    for i, tour in enumerate(provider.programtour_set.all()):
        # Process tour
        sync_tour_periods(tour)

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': total_tours,
                'status': f'Processed {i + 1}/{total_tours} tours'
            }
        )

    return {'status': 'Completed', 'total': total_tours}
```

### Error Recovery & Resilience

#### 1. Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'

            raise e

# Usage in API service
class ResilientAPIService(BaseAPIService):
    def __init__(self, provider):
        super().__init__(provider)
        self.circuit_breaker = CircuitBreaker()

    def get_tours(self):
        return self.circuit_breaker.call(super().get_tours)
```

#### 2. Retry with Exponential Backoff
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, initial_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e

                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff

        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=3)
def fetch_tours_with_retry(self):
    return self._make_request('tours')
```

### Monitoring & Performance Metrics

#### 1. Performance Monitoring
```python
import time
from contextlib import contextmanager

@contextmanager
def performance_monitor(operation_name: str):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"{operation_name} completed in {duration:.2f}s")

        # Send metrics to monitoring system
        metrics.timing(f'api.{operation_name}.duration', duration)

class MonitoredAPIService(BaseAPIService):
    def get_tours(self):
        with performance_monitor('get_tours'):
            return super().get_tours()

    def sync_data(self):
        with performance_monitor('sync_data'):
            # Sync logic here
            pass
```

#### 2. Health Checks
```python
def api_health_check(self) -> Dict[str, Any]:
    """
    Check API health and performance.
    """
    health_status = {
        'api_available': False,
        'response_time': None,
        'last_sync': None,
        'error_rate': None,
        'status': 'unhealthy'
    }

    try:
        start_time = time.time()
        response = self._make_request('health', timeout=5)
        response_time = time.time() - start_time

        health_status.update({
            'api_available': True,
            'response_time': response_time,
            'status': 'healthy' if response_time < 2 else 'degraded'
        })
    except Exception as e:
        logger.error(f"API health check failed: {e}")

    # Check last sync
    last_sync = self.provider.last_synced
    if last_sync:
        health_status['last_sync'] = last_sync.isoformat()

        # Mark as degraded if sync is old
        if timezone.now() - last_sync > timedelta(hours=24):
            health_status['status'] = 'degraded'

    return health_status
```

### Memory Management

#### 1. Generator-Based Processing
```python
def process_tours_generator(self, provider):
    """
    Process tours using generators to reduce memory usage.
    """
    def tour_generator():
        # Fetch tours in batches
        offset = 0
        batch_size = 100

        while True:
            tours = ProgramTour.objects.filter(
                provider=provider
            ).select_related('country')[offset:offset + batch_size]

            if not tours:
                break

            for tour in tours:
                yield tour

            offset += batch_size

    # Process tours one by one
    for tour in tour_generator():
        self.process_single_tour(tour)

        # Force garbage collection periodically
        if tour.id % 1000 == 0:
            import gc
            gc.collect()
```

#### 2. Connection Management
```python
class ConnectionManagedService:
    def __init__(self, provider):
        self.provider = provider
        self._connections = {}

    def get_connection(self):
        """
        Reuse database connections within the same sync session.
        """
        thread_id = threading.current_thread().ident

        if thread_id not in self._connections:
            self._connections[thread_id] = connection.cursor()

        return self._connections[thread_id]

    def cleanup_connections(self):
        """
        Clean up connections when sync is complete.
        """
        for cursor in self._connections.values():
            cursor.close()
        self._connections.clear()
```

## Best Practices Summary

### Performance Guidelines
1. **Use Bulk Operations**: `bulk_create()` and `bulk_update()` for large datasets
2. **Optimize Queries**: Use `select_related()` and `prefetch_related()` appropriately
3. **Implement Caching**: Cache API responses and frequently accessed data
4. **Process in Batches**: Avoid loading entire datasets into memory
5. **Use Background Tasks**: Leverage Celery for long-running operations

### Resilience Guidelines
1. **Implement Circuit Breaker**: Prevent cascade failures from external APIs
2. **Use Retry Logic**: Handle transient failures with exponential backoff
3. **Monitor Performance**: Track API response times and sync performance
4. **Health Checks**: Implement comprehensive health monitoring
5. **Error Recovery**: Store failed records for retry and analysis

### Resource Management
1. **Connection Pooling**: Reuse HTTP and database connections
2. **Memory Management**: Use generators and iterators for large datasets
3. **Task Scheduling**: Use Celery for background processing with proper resource limits
4. **Cache Invalidation**: Clear caches when data is updated
5. **Cleanup Resources**: Properly close connections and clean up resources

---

**Document Version:** 1.1
**Last Updated:** 2025-10-14
**Maintainer:** Backend Development Team
**Updates:** Added performance optimization patterns and monitoring guidelines

---

## Handling Missing Data

### Overview

Different providers provide different levels of data completeness. The mapper pattern allows us to handle missing data gracefully through:

1. **Data completeness flags** - Track what data each provider has
2. **Graceful degradation** - Allow partial data without errors
3. **Null values** - Leave missing pricing types as null (not 0)
4. **Clear indicators** - UI can show appropriate messages

### Completeness Flags

Set these flags in your mapper based on what data the provider provides:

```python
# Full data provider (like Zego)
'has_flights': True,         # Has flight schedules
'has_itineraries': True,     # Has day-by-day itineraries
'has_full_pricing': True,    # Has all pricing types
'data_quality_score': 100,   # Maximum quality

# Limited data provider (like Unique Inter)
'has_flights': False,        # Only airline names
'has_itineraries': False,    # Itineraries in PDF
'has_full_pricing': False,   # Only 3-5 pricing types
'data_quality_score': 60,    # Lower quality

# Unknown provider
'has_flights': True,         # Assume best case
'has_itineraries': True,
'has_full_pricing': True,
'data_quality_score': 50,    # Conservative default
```

### Missing Scenarios

#### Missing Flight Data

**Problem**: Provider doesn't provide flight schedules (only airline names)

**Solution**:
```python
class LimitedProviderMapper(ProviderMapper):
    def map_tour_data(self, raw_data: Dict) -> Dict:
        return {
            # ... other fields
            'airline_name': raw_data.get('Airline', ''),
            'has_flights': False,  # No flight schedules
            'data_quality_score': 70,
        }

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        raise NotImplementedError(
            "This provider doesn't provide flight schedules"
        )
```

**UI Behavior**: Show airline name but display "Contact for flight schedule"

#### Missing Itinerary Data

**Problem**: Provider only has itineraries in PDF documents

**Solution**:
```python
def map_tour_data(self, raw_data: Dict) -> Dict:
    return {
        # ... other fields
        'file_pdf': raw_data.get('pdf_url', ''),
        'has_itineraries': False,  # Itineraries in PDF
        'data_quality_score': 65,
    }
```

**UI Behavior**: Show "Download itinerary (PDF)" button instead of day-by-day view

#### Missing Pricing Types

**Problem**: Provider only has 3 pricing types vs Zego's 12+

**Solution**:
```python
def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
    base_prices = {
        'adult': self.normalizer.normalize_price(raw_data.get('Adult')),
        'child': self.normalizer.normalize_price(raw_data.get('Child')),
        'single_bed': self.normalizer.normalize_price(raw_data.get('Single')),
        # Missing types left as null (not 0)
    }
    return {
        # ... other fields
        'base_prices': base_prices,
        'has_full_pricing': False,
    }
```

**UI Behavior**: Show available prices, hide missing types, show "Call for quote" button

#### Missing Country Data

**Problem**: Provider uses categories instead of actual countries

**Solution**:
```python
def map_tour_data(self, raw_data: Dict) -> Dict:
    country_name = self._extract_country(raw_data.get('title', ''))
    
    # Try to find matching country
    try:
        country = Country.objects.get(
            provider=self.provider,
            normalized_name=normalize_country_name(country_name)
        )
    except Country.DoesNotExist:
        country = None  # Leave empty, don't create invalid countries
    
    return {
        # ... other fields
        'country': country,
        'country_name': country_name,  # Keep snapshot
    }
```

### Data Quality Scoring

Use the `data_quality_score` field to indicate data completeness:

| Score | Quality | Description |
|-------|---------|-------------|
| 100 | Excellent | All data types available |
| 80-90 | Good | Most data available, minor gaps |
| 60-70 | Fair | Significant gaps but usable |
| 40-50 | Limited | Major gaps, use with caution |
| 0-30 | Poor | Minimal data, for reference only |

### API Response Consistency

Regardless of provider, the API response structure should remain consistent:

```json
{
    "id": 123,
    "code": "ZEGO-TOUR-001",
    "name": "Amazing Thailand Tour",
    "has_flights": true,      // Always present
    "has_itineraries": true,  // Always present
    "has_full_pricing": true, // Always present
    "data_quality_score": 100 // Always present
}
```

This allows frontend to:
1. Show/hide sections based on availability
2. Display appropriate UI for missing data
3. Sort/filter by data quality
4. Provide consistent user experience

---

## Standardization Rules

### 1. Use Field Normalizers

Always use the provided normalizer functions for data transformation:

```python
# Good
price = self.normalizer.normalize_price(raw_data.get('price'))
date = self.normalizer.normalize_date(raw_data.get('date'))
boolean = self.normalizer.normalize_boolean(raw_data.get('has_meals'))

# Bad
price = Decimal(raw_data['price'])  # No error handling
date = datetime.strptime(raw_data['date'], '%Y-%m-%d')  # Fragile
```

### 2. Return Null for Missing Data

```python
# Good - Missing data is null
base_prices = {
    'adult': Decimal('50000'),
    'child': None,  # Not available
    'child_nb': None,  # Not available
}

# Bad - Missing data is 0
base_prices = {
    'adult': Decimal('50000'),
    'child': Decimal('0'),  # Looks like price is 0
    'child_nb': Decimal('0'),
}
```

### 3. Set Completeness Flags Accurately

```python
# Always set based on actual data availability
'has_flights': bool(flight_data),  # True if data exists
'has_itineraries': bool(itinerary_data),
'has_full_pricing': len(pricing_types) >= 10,
```

### 4. Use NotImplementedError for Missing Methods

```python
def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
    raise NotImplementedError(
        "ProviderName does not provide flight schedule data"
    )
```

This makes it explicit that the provider doesn't support this data type.

---

## Quick Reference: Mapper Template

```python
from wholesale.provider_mappers import ProviderMapper
from wholesale.field_normalizers import FieldNormalizer

class YourProviderMapper(ProviderMapper):
    """Mapper for YourProvider"""

    def __init__(self, provider):
        super().__init__(provider)
        self.normalizer = FieldNormalizer()

    def map_tour_data(self, raw_data: Dict) -> Dict:
        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('tour_id')),
            'code': raw_data.get('tour_code'),
            'name': raw_data.get('tour_name'),
            'days': self.normalizer.normalize_integer(raw_data.get('days')),
            'nights': self.normalizer.normalize_integer(raw_data.get('nights')),
            'country': self._get_or_create_country(raw_data.get('country')),
            'country_name': raw_data.get('country'),
            'airline_name': raw_data.get('airline'),
            'file_pdf': raw_data.get('pdf_url'),
            'image_url': raw_data.get('image_url'),
            'highlight': raw_data.get('description'),
            # Set based on actual data availability
            'has_flights': True,
            'has_itineraries': True,
            'has_full_pricing': True,
            'data_quality_score': 100,
        }

    def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
        base_prices = {
            'adult': self.normalizer.normalize_price(raw_data.get('price_adult')),
            'child': self.normalizer.normalize_price(raw_data.get('price_child')),
            # Add other pricing types as available
        }

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('departure_id')),
            'code': raw_data.get('departure_code'),
            'program_id': program_tour.id if program_tour else None,
            'start_date': self.normalizer.normalize_date(raw_data.get('start_date')),
            'end_date': self.normalizer.normalize_date(raw_data.get('end_date')),
            'seats': self.normalizer.normalize_integer(raw_data.get('available_seats')),
            'status': raw_data.get('status', 'Book'),
            'base_prices': base_prices,
        }

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        return {
            'provider': self.provider.id,
            'period_id': period.id if period else None,
            'airline_name': raw_data.get('airline'),
            'flight_no': raw_data.get('flight_number'),
            'route': raw_data.get('route'),
        }

    def map_itinerary_data(self, raw_data: Dict, program_tour=None) -> Dict:
        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('itinerary_id')),
            'program_id': program_tour.id if program_tour else None,
            'day': self.normalizer.normalize_integer(raw_data.get('day')),
            'description': raw_data.get('description'),
            'hotel': raw_data.get('hotel'),
        }
```

---

**End of Guide v3.0**

For questions or issues, refer to:
- `wholesale/field_normalizers.py` - Normalization utilities
- `wholesale/provider_mappers.py` - Example mapper implementations
- `wholesale/provider_mappings.py` - Field mapping configurations
