# Provider Adapter Post-Evaluation Implementation Guide

**Last Updated:** 2026-01-16
**Target Audience:** Backend developers implementing adapters after using evaluation tool
**Prerequisites:** Completed evaluation at http://localhost:8000/wholesale/evaluation/

---

## Table of Contents

1. [Overview](#overview)
2. [Understanding Your Evaluation Results](#understanding-your-evaluation-results)
3. [Path 1: Reusing Existing Adapters (95-100% or 80-94%)](#path-1-reusing-existing-adapters)
4. [Path 2: Creating Field Normalizers (50-79%)](#path-2-creating-field-normalizers)
5. [Path 3: Creating New Adapters (< 50%)](#path-3-creating-new-adapters)
6. [Decision Matrix](#decision-matrix)
7. [Testing Checklist](#testing-checklist)
8. [AI Helper Prompts](#ai-helper-prompts)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This guide explains **the three main paths** for implementing provider adapters after using the Provider Adapter Evaluation Tool.

### The Evaluation Process

After running the evaluation tool, you'll receive one of four recommendations:

| Compatibility Score | Action | Scenario |
|---------------------|--------|----------|
| 95-100% | `PERFECT_MATCH` | Use existing adapter directly |
| 80-94% | `REUSE` | Use existing adapter with minor tweaks |
| 50-79% | `REUSE_WITH_NORMALIZER` | Create field normalizer + use existing adapter |
| < 50% | `CREATE_NEW` | Generate new adapter code |

### Key Principles

1. **Reuse is always preferred** - Only create new adapters when necessary
2. **Field normalizers bridge the gap** - They allow reuse even with different field names
3. **Generated code is a starter** - Always review and customize for production
4. **Testing is mandatory** - Verify data quality before going live

---

## Understanding Your Evaluation Results

### Interpreting the Recommendation

**PERFECT_MATCH (95-100%)**
- Your API has the EXACT same field structure as an existing adapter
- All fields match directly
- No code changes needed
- Implementation time: 15-30 minutes

**REUSE (80-94%)**
- Strong compatibility with minor field name differences
- Most fields match, some minor adjustments may be needed
- Implementation time: 30-60 minutes

**REUSE_WITH_NORMALIZER (50-79%)**
- Field NAMES differ but structure is similar
- Need to create a field normalizer to map field names
- Implementation time: 2-4 hours

**CREATE_NEW (< 50%)**
- Data structure is significantly different
- New adapter required
- Implementation time: 4-8 hours

### Using AI Helper Prompts

The evaluation tool provides **"📋 Copy AI Helper Prompt"** button that generates a detailed prompt you can paste into an AI assistant (like Claude Code) to get help with implementation.

**When to use AI helper prompts:**
- Uncertain about implementation steps
- Need code examples for specific scenarios
- Troubleshooting errors during implementation
- Want to ensure best practices

---

## Path 1: Reusing Existing Adapters (95-100% or 80-94%)

**When to use:** The evaluation tool indicates `PERFECT_MATCH` or `REUSE` action.

### How It Works

When the new provider's API structure closely matches an existing adapter, you **don't need to write new code**. Instead, you:

1. Register the provider in Django Admin
2. Configure it to use the existing adapter
3. Run the existing sync command

### Step-by-Step Implementation

#### Step 1: Create Provider in Django Admin

**Via Django Admin UI (Recommended):**
1. Navigate to `http://localhost:8000/admin/wholesale/provider/`
2. Click "Add Provider"
3. Fill in the **Basic Information** section:
   - Name: Your provider's name
   - Code: Unique lowercase code (e.g., "newprovider")
   - **Adapter Type:** Select from dropdown (e.g., "checkingroup")
   - Is Active: Check the box
4. Fill in the **API Configuration** section:
   - Base URL: API base URL
   - Token: API token/key (if required)
   - API Version: API version (if applicable)
5. Click "Save"

**The Adapter Type dropdown will:**
- Show all available adapters: Zego, Unique Inter, Go365, CheckIn Group
- Store your selection in the provider's `extra` JSON field
- Display the adapter type in the provider list view

```python
# Alternatively, via Django shell
from wholesale.models import Provider

provider = Provider.objects.create(
    name='New Travel Wholesale',
    code='newprovider',  # Unique code
    base_url='https://api.newprovider.com',
    token='your-api-token',
    is_active=True,
    extra={
        'adapter_type': 'checkingroup'  # Use the recommended adapter
    }
)
```

#### Step 2: Configure API Credentials

If the provider uses different authentication than the original adapter:

```python
provider.extra = {
    'adapter_type': 'checkingroup',
    'api_version': 'v2',
    'timeout': 60,
    # Add any provider-specific settings
}
provider.save()
```

#### Step 3: Test the Connection

```python
from wholesale.models import Provider
from wholesale.api_service import APIServiceFactory

provider = Provider.objects.get(code='newprovider')
service = APIServiceFactory.create_service(provider)

# Test connection
if service.test_connection():
    print("✓ Connection successful")
else:
    print("✗ Connection failed - check credentials")
```

#### Step 4: Run the Existing Sync Command

```bash
# Use the EXISTING command for the adapter you're reusing
docker-compose exec web python manage.py sync_checkingroup

# Or with provider code filter (if supported)
docker-compose exec web python manage.py sync_checkingroup --provider-code newprovider
```

**Key Point:** You use the **existing adapter's command**, not a new one. The provider configuration tells it which provider to sync.

### Example Scenario

**Evaluation Result:**
- Action: `PERFECT_MATCH`
- Recommended Adapter: `checkingroup`
- Score: 98%

**Implementation:**
```python
# 1. Register provider using checkingroup adapter
Provider.objects.create(
    name='Thai B2B Tours',
    code='thai_b2b',
    base_url='https://api.thaib2b.com',
    token='abc123',
    extra={'adapter_type': 'checkingroup'}  # Reuse CheckIn Group adapter
)

# 2. Run CheckIn Group sync command
# docker-compose exec web python manage.py sync_checkingroup
```

### Advantages

✅ **No code needed** - Reuse existing implementation
✅ **Fast integration** - Can be done in < 30 minutes
✅ **Tested code** - Existing adapter is already proven
✅ **Easy maintenance** - Benefits from existing bug fixes

---

## Path 2: Creating Field Normalizers (50-79%)

**When to use:** The evaluation tool indicates `REUSE_WITH_NORMALIZER` action.

### How It Works

The provider's data **structure is similar** but **field names differ**. You create a **field normalizer** that maps your provider's fields to match an existing adapter's format.

### Two Sub-Options

#### Option A: Create Field Normalizer Class (Recommended)

Create a custom normalizer that transforms your provider's API responses to match an existing adapter's expected format.

**File:** `wholesale/field_normalizers.py`

```python
class ThaiB2BNormalizer(FieldNormalizer):
    """Normalizes Thai B2B Tours API to CheckIn Group format"""

    def normalize_tour(self, raw_data):
        """
        Transform Thai B2B tour format to CheckIn Group format.

        Thai B2B format:
        {
            "TOUR_ID": "TB123",
            "TOUR_NAME": "Amazing Thailand",
            "DURATION_DAYS": 7,
            "PRICE_THB": 25000
        }

        CheckIn Group expects:
        {
            "id": "TB123",
            "name": "Amazing Thailand",
            "day": 7,
            "price": 25000
        }
        """
        return {
            'id': raw_data.get('TOUR_ID'),
            'code': raw_data.get('TOUR_CODE'),
            'name': raw_data.get('TOUR_NAME'),
            'day': self.normalize_integer(raw_data.get('DURATION_DAYS')),
            'night': self.normalize_integer(raw_data.get('DURATION_NIGHTS')),
            'price': self.normalize_price(raw_data.get('PRICE_THB')),
            # Map all other fields...
        }

    def normalize_period(self, raw_data):
        """Transform departure data format"""
        return {
            'id': raw_data.get('DEP_ID'),
            'start': self.normalize_date(raw_data.get('DEPART_DATE')),
            'end': self.normalize_date(raw_data.get('RETURN_DATE')),
            'price': self.normalize_price(raw_data.get('ADULT_PRICE')),
            # Map all other fields...
        }
```

**Register the normalizer in the mapper:**

```python
# wholesale/provider_mappers.py
class ThaiB2BMapper(CheckInGroupMapper):
    """Reuse CheckIn Group mapper with custom normalizer"""

    def __init__(self, provider):
        super().__init__(provider)
        # Use custom normalizer instead of default
        from .field_normalizers import ThaiB2BNormalizer
        self.normalizer = ThaiB2BNormalizer()

    def map_tour_data(self, raw_data):
        # Normalize to CheckIn Group format first
        normalized = self.normalizer.normalize_tour(raw_data)
        # Then use parent mapper logic
        return super().map_tour_data(normalized)
```

#### Option B: Extend Provider Mappings Configuration

Add field mappings to `wholesale/provider_mappings.py`:

```python
PROVIDER_MAPPINGS['thai_b2b'] = {
    'tour': {
        'external_id': 'TOUR_ID',     # API field → Model field
        'code': 'TOUR_CODE',
        'name': 'TOUR_NAME',
        'days': 'DURATION_DAYS',
        'price': 'PRICE_THB',
        # ... all field mappings
    },
    'period': {
        'external_id': 'DEP_ID',
        'start_date': 'DEPART_DATE',
        'end_date': 'RETURN_DATE',
        # ... all field mappings
    },
}
```

### Implementation Steps

#### Step 1: Create Provider Record

**Via Django Admin UI:**
1. Navigate to `http://localhost:8000/admin/wholesale/provider/`
2. Click "Add Provider"
3. Fill in:
   - Name: Thai B2B Tours
   - Code: thai_b2b
   - **Adapter Type:** Select "CheckIn Group" from dropdown
   - Base URL: https://api.thaib2b.com
   - Is Active: Check the box
4. Click "Save"

```python
# Alternatively, via Django shell
Provider.objects.create(
    name='Thai B2B Tours',
    code='thai_b2b',
    base_url='https://api.thaib2b.com',
    extra={'adapter_type': 'checkingroup'}  # Base adapter
)
```

#### Step 2: Create Field Normalizer or Mappings

Choose **Option A** (normalizer class) or **Option B** (mappings config) based on complexity.

- **Option A** is better for complex transformations
- **Option B** is better for simple field name changes

#### Step 3: Register Mapper in Factory

```python
# wholesale/api_service.py
@staticmethod
def create_mapper(provider):
    from .provider_mappers import (
        CheckInGroupMapper,
        ThaiB2BMapper  # Your custom mapper
    )

    if provider.code == 'thai_b2b':
        return ThaiB2BMapper(provider)
    elif provider.code == 'checkingroup':
        return CheckInGroupMapper(provider)
    # ... other providers
```

#### Step 4: Run Sync Command

```bash
# Use the base adapter's command
docker-compose exec web python manage.py sync_checkingroup
```

### Example Scenario

**Evaluation Result:**
- Action: `REUSE_WITH_NORMALIZER`
- Recommended Adapter: `checkingroup`
- Score: 65%
- Field differences:
  - `id` vs `TOUR_ID`
  - `name` vs `TOUR_NAME`
  - `day` vs `DURATION_DAYS`

**Implementation:**

```python
# wholesale/field_normalizers.py
class ThaiB2BNormalizer(FieldNormalizer):
    def normalize_to_checkingroup_format(self, raw_data):
        return {
            'id': raw_data.get('TOUR_ID'),
            'name': raw_data.get('TOUR_NAME'),
            'day': int(raw_data.get('DURATION_DAYS', 0)),
            'price': Decimal(str(raw_data.get('PRICE_THB', 0))),
        }

# wholesale/provider_mappers.py
class ThaiB2BMapper(CheckInGroupMapper):
    def __init__(self, provider):
        super().__init__(provider)
        from .field_normalizers import ThaiB2BNormalizer
        self.normalizer = ThaiB2BNormalizer()

    def map_tour_data(self, raw_data):
        # Normalize to CheckIn Group format first
        normalized = self.normalizer.normalize_to_checkingroup_format(raw_data)
        # Then use parent mapper logic
        return super().map_tour_data(normalized)
```

### Advantages

✅ **Less code than new adapter** - Reuse existing logic
✅ **Consistent with base adapter** - Inherits improvements
✅ **Flexible** - Handle field name differences easily
✅ **Maintainable** - Single source of transformation logic

---

## Path 3: Creating New Adapters (< 50%)

**When to use:** The evaluation tool indicates `CREATE_NEW` action and provides generated code.

### How It Works

The provider's API structure is **fundamentally different**. The evaluation tool generates starter code that you customize.

### Implementation Steps

#### Step 1: Review Generated Code

After evaluation, click **"Generate Code"** to download:
- `{provider_code}_service.py` - API service class
- `{provider_code}_mapper.py` - Data mapper class
- `sync_{provider_code}.py` - Management command
- `{provider_code}_mappings.py` - Field mappings config

#### Step 2: Customize Generated Files

**Update API endpoints:**

```python
# wholesale/yourprovider_service.py
class YourProviderAPIService(BaseAPIService):
    def get_program_tours(self):
        # Update endpoint to match actual API
        response = self._make_request('/api/v2/tours/all')  # ← Update this
        return response.get('data', [])
```

**Update field mappings:**

```python
# wholesale/yourprovider_mappings.py
PROVIDER_MAPPINGS['yourprovider'] = {
    'tour': {
        'external_id': 'tourCode',     # ← Update with actual field names
        'code': 'tourCode',
        'name': 'packageName',
        'days': 'duration',
        # ... complete all mappings
    },
}
```

#### Step 3: Register in Factory

```python
# wholesale/api_service.py
class APIServiceFactory:
    @staticmethod
    def create_service(provider):
        service_map = {
            'zego': ZegoAPIService,
            'checkingroup': CheckInGroupAPIService,
            'yourprovider': YourProviderAPIService,  # Add your service
        }
        return service_map.get(provider.code)

    @staticmethod
    def create_mapper(provider):
        if provider.code == 'yourprovider':
            return YourProviderMapper(provider)  # Add your mapper
        # ... other providers
```

#### Step 4: Create Provider and Test

```python
Provider.objects.create(
    name='Your Provider',
    code='yourprovider',
    base_url='https://api.yourprovider.com',
    token='your-token'
)
```

```bash
# Test with dry run
docker-compose exec web python manage.py sync_yourprovider --limit 1

# Full sync
docker-compose exec web python manage.py sync_yourprovider
```

### Example Scenario

**Evaluation Result:**
- Action: `CREATE_NEW`
- Score: 35% (best match)
- Reasoning: "Data structure is significantly different"

**Generated Files:**
```python
# Auto-generated by evaluation tool
# wholesale/yourprovider_service.py
class YourProviderAPIService(BaseAPIService):
    # TODO: Implement authentication
    # TODO: Update endpoints
    # TODO: Handle pagination

# wholesale/yourprovider_mapper.py
class YourProviderMapper(ProviderMapper):
    # TODO: Map fields based on sample data
    # TODO: Handle missing data
```

### Advantages

✅ **Custom fit** - Tailored to your provider's API
✅ **Starter code** - Don't start from scratch
✅ **Full control** - Implement provider-specific logic
✅ **Independent** - Not tied to other adapters

---

## Decision Matrix

| Scenario | Path | Time Required | Code to Write |
|----------|------|---------------|---------------|
| 95-100% match | Path 1: Reuse directly | 15-30 min | None (config only) |
| 80-94% match | Path 1: Reuse with tweaks | 30-60 min | Minimal (auth tweaks) |
| 50-79% match | Path 2: Field normalizer | 2-4 hours | Normalizer class (100-300 lines) |
| < 50% match | Path 3: New adapter | 4-8 hours | Full adapter (500-1000 lines) |

---

## Testing Checklist

### For All Paths

- [ ] Provider created in Django Admin
- [ ] API credentials configured
- [ ] Connection test successful
- [ ] Sample data fetched successfully
- [ ] Data mapping produces correct fields
- [ ] No duplicate records created
- [ ] Pricing JSON has correct structure
- [ ] Dates in YYYY-MM-DD format
- [ ] Error handling works for invalid data
- [ ] Full sync completes without errors

### Path-Specific Tests

**Path 1 (Reuse):**
```bash
# Test with existing command
docker-compose exec web python manage.py sync_checkingroup --limit 1
```

**Path 2 (Normalizer):**
```bash
# Test field transformation
docker-compose exec web python manage.py shell
```
```python
from wholesale.field_normalizers import ThaiB2BNormalizer
normalizer = ThaiB2BNormalizer()
result = normalizer.normalize_to_checkingroup_format(sample_data)
# Verify field mapping is correct
```

**Path 3 (New Adapter):**
```bash
# Test command with --limit flag
docker-compose exec web python manage.py sync_yourprovider --limit 1

# Verify database records
docker-compose exec web python manage.py shell
```
```python
from wholesale.models import ProgramTour
tour = ProgramTour.objects.filter(provider__code='yourprovider').first()
print(tour.name, tour.days, tour.base_prices)
```

---

## AI Helper Prompts

The evaluation tool provides context-specific AI helper prompts. Click the **"📋 Copy AI Helper Prompt"** button on the analysis results page to get a formatted prompt.

### Prompt 1: Perfect Match / Reuse Scenarios

**Use when evaluation shows 80-100% compatibility:**

````markdown
# Task: Configure Provider to Use Existing Adapter

## Evaluation Result
- Compatibility: 98%
- Recommended Adapter: checkingroup
- Action: PERFECT_MATCH

## What I Need
1. Register provider in Django Admin to use checkingroup adapter
2. Configure API credentials
3. Test connection
4. Run sync command

## Provider Details
- Name: Thai B2B Tours
- Code: thai_b2b
- Base URL: https://api.thaib2b.com

Please provide:
1. Django shell commands to register the provider
2. Command to test API connection
3. Command to run sync
4. Any additional configuration needed
````

### Prompt 2: For Field Normalizer Scenario

**Use when evaluation shows 50-79% compatibility:**

````markdown
# Task: Create Field Normalizer for Provider

## Evaluation Result
- Compatibility: 65%
- Recommended Adapter: checkingroup
- Action: REUSE_WITH_NORMALIZER

## Field Differences
The tool found these field mapping differences:
- tour_id → id
- tour_name → name
- duration_days → day

## Sample API Response
```json
[{"TOUR_ID": "TB123", "TOUR_NAME": "Amazing Thailand", "DURATION_DAYS": 7}]
```

## Target Adapter Format
The checkingroup adapter expects these fields:
- id: string
- name: string
- day: integer

Please create:
1. A FieldNormalizer class that transforms my provider's format to checkingroup format
2. A custom Mapper class that extends CheckInGroupMapper
3. Registration in APIServiceFactory
4. Example of how to run the sync

Follow the patterns in:
- wholesale/field_normalizers.py
- wholesale/provider_mappers.py
- wholesale/api_service.py
````

### Prompt 3: For New Adapter Scenario

**Use when evaluation shows < 50% compatibility:**

````markdown
# Task: Create New Provider Adapter

## Evaluation Result
- Compatibility: 35%
- Action: CREATE_NEW
- Reasoning: Data structure is significantly different

## Generated Code
The evaluation tool generated these files:
- yourprovider_service.py
- yourprovider_mapper.py
- sync_yourprovider.py
- yourprovider_mappings.py

## Provider API Details
- Base URL: https://api.provider.com
- Authentication: Bearer token
- Endpoints:
  - Tours: /api/v2/tours
  - Periods: /api/v2/tours/{id}/periods

## Sample API Responses
```json
// Tours endpoint
[{"tourId": "T001", "tourName": "Bangkok Tour"}]
```

## What I Need
1. Review and customize the generated API Service class
2. Review and customize the generated Mapper class
3. Complete field mappings in provider_mappings.py
4. Register in APIServiceFactory
5. Create Provider in Django Admin
6. Test the implementation

Please:
1. Review the generated code and identify TODO items
2. Help me implement the missing pieces
3. Provide testing commands
4. Suggest any improvements or error handling

Reference existing implementations:
- wholesale/api_service.py (ZegoAPIService, CheckInGroupAPIService)
- wholesale/provider_mappers.py (ZegoMapper, CheckInGroupMapper)
- wholesale/provider_mappings.py (existing mappings)
````

---

## Troubleshooting

### Issue: "Provider not found in mappings"

**Cause:** Your provider code isn't registered in the factory.

**Solution:**
```python
# wholesale/api_service.py
@staticmethod
def create_service(provider):
    if provider.code == 'yourprovider':
        return YourProviderAPIService(provider)
    # ... other providers
```

### Issue: Field mapping not working

**Cause:** Field names in normalizer don't match API response.

**Solution:**
```python
# Test your normalizer
from wholesale.field_normalizers import YourNormalizer
normalizer = YourNormalizer()
sample = {"YOUR_API_FIELD": "value"}
result = normalizer.normalize_tour(sample)
print(result)  # Check output
```

### Issue: Sync creates duplicates

**Cause:** External ID not properly mapped or unique constraint issue.

**Solution:**
```python
# Verify external_id is being set correctly
tour = ProgramTour.objects.filter(provider=provider).first()
print(tour.external_id)  # Should match API's unique ID
```

### Issue: Authentication errors

**Cause:** Token or authentication method not configured correctly.

**Solution:**
```python
# Check provider configuration
provider = Provider.objects.get(code='yourprovider')
print(provider.token)
print(provider.extra)

# Test authentication
service = APIServiceFactory.create_service(provider)
service.test_connection()
```

---

## Related Documentation

- [Evaluation Tool Guide](evaluation-tool.md) - How to use the evaluation tool
- [Adapter Implementation Guide](adapter-guide.md) - Complete adapter development
- [Quick Start](quick-start.md) - Fast track for provider integration
- [Field Normalizers Reference](../api/field-normalizers.md) - Normalizer API documentation

---

## Quick Reference Card

```markdown
## Provider Adapter Quick Reference

### Evaluation Tool
🔗 http://localhost:8000/wholesale/evaluation/

### Compatibility Scores
🟢 95-100% → Use as-is (no code)
🟡 80-94%  → Minor config (15-30 min)
🟠 50-79%  → Field normalizer (2-4 hours)
🔴 < 50%   → New adapter (4-8 hours)

### Key Commands
# Test connection
docker-compose exec web python manage.py shell
>>> from wholesale.api_service import APIServiceFactory
>>> service = APIServiceFactory.create_service(provider)
>>> service.test_connection()

# Sync data
docker-compose exec web python manage.py sync_[adapter] --limit 1

# Verify data
docker-compose exec web python manage.py shell
>>> from wholesale.models import ProgramTour
>>> ProgramTour.objects.filter(provider__code='[code]').count()

### File Locations
📁 Adapter Guide:      docs/provider-integration/adapter-guide.md
📁 API Services:       wholesale/api_service.py
📁 Provider Mappers:   wholesale/provider_mappers.py
📁 Field Normalizers:  wholesale/field_normalizers.py
📁 Provider Mappings:  wholesale/provider_mappings.py
📁 Models:             wholesale/models.py
📁 Management Cmds:    wholesale/management/commands/
```
