---
name: validate-models
description: Use before running provider sync to validate Django models can handle API data. Prevents constraint violations and silent failures. Examples - "Check if Country model ready for new provider", "Validate Flight fields before sync", "Test model constraints"
model: sonnet
---

# Model Validator

## Purpose

Validate Django models against actual provider API data BEFORE running sync commands. Identifies potential constraint violations, missing fields, and data incompatibilities that would cause silent failures.

## When to Use This Skill

- Before running first sync with a new provider
- After adding new fields to models
- When sync commands show low success rates
- To identify which model fields need `blank=True` or `null=True`
- Before deploying model changes to production
- When troubleshooting why data isn't saving

## Validation Workflow

### Step 1: Select Provider and Model

Ask the user which provider and model to validate:

**Providers**:
- `zego` - Zego API
- `unique_inter` - Unique Inter API
- `checkingroup` - CheckIn Group API
- `go365` - Go365 API
- Custom provider code

**Models to validate**:
- `Country` - Country/destination data
- `ProgramTour` - Tour package data
- `Period` - Tour dates and pricing
- `Flight` - Flight information
- `Itinerary` - Day-by-day program

**Example questions**:
```
Which provider do you want to validate? (e.g., go365)
Which model should I validate? (Country, ProgramTour, Period, Flight, Itinerary)
Or should I validate all models for this provider?
```

### Step 2: Fetch Sample API Data

Get real data from the provider's API to validate against:

**For testing without full sync**:
```python
# In Django shell
from wholesale.models import Provider
from wholesale.management.commands.sync_{provider} import Command

# Get provider
provider = Provider.objects.get(code='{provider_code}')

# Initialize command
cmd = Command()

# Fetch sample data (modify based on provider API structure)
response = cmd.make_api_request(provider, '/countries')
sample_countries = response.json().get('data', [])[:5]  # First 5 countries

response = cmd.make_api_request(provider, '/tours', {'limit': 5})
sample_tours = response.json().get('data', [])[:5]  # First 5 tours
```

**Save sample data for analysis**:
```bash
# Save to JSON file for inspection
import json
with open('{provider}_sample_countries.json', 'w') as f:
    json.dump(sample_countries, f, indent=2)

with open('{provider}_sample_tours.json', 'w') as f:
    json.dump(sample_tours, f, indent=2)
```

### Step 3: Analyze Model Field Requirements

Read the Django model to understand field constraints:

**File**: `wholesale/models.py`

**For each field, check**:
1. **Required vs Optional**:
   - Required: No `blank=True` and no `null=True` and no `default`
   - Optional: Has `blank=True` or `null=True` or `default`

2. **Constraints**:
   - `unique=True` - Value must be unique across all records
   - `unique_together` - Combination of fields must be unique
   - `max_length` - String length limits
   - `choices` - Value must be in predefined list

3. **Foreign Keys**:
   - `on_delete` behavior
   - Whether FK is required or optional
   - Related model existence

**Example analysis for Flight model**:

```python
# Read wholesale/models.py - Flight model

class Flight(models.Model):
    # REQUIRED fields (no blank, no null, no default)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)  # REQUIRED
    period = models.ForeignKey(Period, on_delete=models.CASCADE)  # REQUIRED
    flight_no = models.CharField(max_length=100)  # REQUIRED

    # OPTIONAL fields (has blank=True or default)
    airline_code = models.CharField(max_length=50, blank=True, default='')  # OPTIONAL
    airline_name = models.CharField(max_length=200, blank=True, default='')  # OPTIONAL
    departure_airport = models.CharField(max_length=100, blank=True, default='')  # OPTIONAL

    # NULLABLE fields (has null=True)
    departure_time = models.DateTimeField(null=True, blank=True)  # NULLABLE

# REQUIRED fields that MUST be populated:
# 1. provider (FK - must exist)
# 2. period (FK - must exist)
# 3. flight_no (string - cannot be empty)

# These fields will cause IntegrityError if not provided or if empty!
```

**Create field requirement report**:
```markdown
## Flight Model Field Requirements

### Required Fields (MUST provide non-empty values)
- `provider` (ForeignKey) - Must reference existing Provider
- `period` (ForeignKey) - Must reference existing Period
- `flight_no` (CharField) - Cannot be empty string

### Optional Fields (Can be empty)
- `airline_code` (CharField) - Has default=''
- `airline_name` (CharField) - Has default=''
- `departure_airport` (CharField) - Has default=''

### Nullable Fields (Can be None)
- `departure_time` (DateTimeField) - null=True
- `arrival_time` (DateTimeField) - null=True

### Constraints
- No unique constraints on individual fields
- No unique_together constraints
```

### Step 4: Map API Data to Model Fields

Use the provider's mapper to transform API data:

**Check mapper implementation**:

```python
# Read wholesale/provider_mappers.py - {Provider}Mapper class

from wholesale.provider_mappers import {Provider}Mapper
from wholesale.field_normalizers import {Provider}Normalizer

# Initialize mapper
normalizer = {Provider}Normalizer()
mapper = {Provider}Mapper(normalizer)

# Test mapping with sample data
for sample in sample_data[:3]:  # Test first 3 records
    try:
        mapped_fields = mapper.map_flight_data(sample, period=None, provider=provider)
        print(f"Mapped fields: {mapped_fields}")

        # Check for missing required fields
        if not mapped_fields.get('flight_no'):
            print("  ⚠ WARNING: flight_no is empty!")

    except KeyError as e:
        print(f"  ✗ ERROR: Missing key in API data: {e}")
    except Exception as e:
        print(f"  ✗ ERROR: Mapping failed: {e}")
```

### Step 5: Validate Field Compatibility

Check if API data can satisfy model requirements:

**Validation checks**:

1. **Required Field Check**:
   ```python
   def validate_required_fields(mapped_data, model_name):
       """Check if all required fields have non-empty values."""
       issues = []

       # Define required fields per model
       required_fields = {
           'Flight': ['provider', 'period', 'flight_no'],
           'Country': ['provider', 'name'],
           'ProgramTour': ['provider', 'provider_tour_id', 'name'],
           'Period': ['provider', 'program_tour', 'start_date'],
           'Itinerary': ['provider', 'program_tour', 'day_number'],
       }

       for field in required_fields.get(model_name, []):
           value = mapped_data.get(field)

           # Check if value is missing or empty
           if value is None:
               issues.append(f"❌ {field}: Value is None")
           elif value == '':
               issues.append(f"❌ {field}: Value is empty string")
           elif isinstance(value, str) and not value.strip():
               issues.append(f"❌ {field}: Value is whitespace only")

       return issues
   ```

2. **Data Type Check**:
   ```python
   def validate_field_types(mapped_data, model_name):
       """Check if field values match expected types."""
       issues = []

       # Define expected types per field
       type_expectations = {
           'Flight': {
               'flight_no': str,
               'departure_time': (datetime, type(None)),  # datetime or None
               'airline_code': str,
           },
           'Period': {
               'start_date': (date, str),
               'price_adult': Decimal,
               'available_seats': int,
           }
       }

       for field, expected_type in type_expectations.get(model_name, {}).items():
           value = mapped_data.get(field)

           if value is not None and not isinstance(value, expected_type):
               issues.append(
                   f"⚠ {field}: Expected {expected_type}, got {type(value).__name__}"
               )

       return issues
   ```

3. **Constraint Check**:
   ```python
   def validate_constraints(mapped_data, model_name, existing_records):
       """Check for potential unique constraint violations."""
       issues = []

       # Check unique fields
       unique_checks = {
           'Flight': [],  # No unique constraints
           'Country': [('provider', 'provider_country_id')],  # unique_together
           'ProgramTour': [('provider', 'provider_tour_id')],
       }

       for unique_fields in unique_checks.get(model_name, []):
           # Build lookup dict
           lookup = {field: mapped_data.get(field) for field in unique_fields}

           # Check if record with these values already exists
           if model_name == 'Country':
               from wholesale.models import Country
               exists = Country.objects.filter(**lookup).exists()
           # ... similar for other models

           if exists:
               issues.append(
                   f"⚠ Unique constraint: Record with {lookup} already exists"
               )

       return issues
   ```

4. **Foreign Key Check**:
   ```python
   def validate_foreign_keys(mapped_data, model_name):
       """Check if foreign key references exist."""
       issues = []

       # Check provider FK
       if 'provider' in mapped_data:
           provider = mapped_data['provider']
           if provider and not Provider.objects.filter(id=provider.id).exists():
               issues.append(f"❌ provider: Provider {provider.id} does not exist")

       # Check period FK for Flight model
       if model_name == 'Flight' and 'period' in mapped_data:
           period = mapped_data['period']
           if period and not Period.objects.filter(id=period.id).exists():
               issues.append(f"❌ period: Period {period.id} does not exist")

       # Similar checks for other FKs...

       return issues
   ```

### Step 6: Run Validation Tests

Execute validation on sample data:

```python
def validate_sample_data(provider_code, model_name, sample_data):
    """
    Validate sample API data against Django model requirements.

    Returns:
        dict with validation results
    """
    from wholesale.models import Provider
    from wholesale.provider_mappers import get_mapper_for_provider
    from wholesale.field_normalizers import get_normalizer_for_provider

    # Get provider
    provider = Provider.objects.get(code=provider_code)

    # Initialize mapper
    normalizer = get_normalizer_for_provider(provider_code)
    mapper = get_mapper_for_provider(provider_code, normalizer)

    results = {
        'total_records': len(sample_data),
        'valid_records': 0,
        'invalid_records': 0,
        'issues': [],
    }

    # Map function based on model type
    map_functions = {
        'Country': mapper.map_country_data,
        'ProgramTour': mapper.map_tour_data,
        'Period': mapper.map_period_data,
        'Flight': mapper.map_flight_data,
        'Itinerary': mapper.map_itinerary_data,
    }

    map_func = map_functions.get(model_name)
    if not map_func:
        return {'error': f'Unknown model: {model_name}'}

    # Validate each record
    for i, record in enumerate(sample_data):
        record_issues = []

        try:
            # Map API data to model fields
            mapped = map_func(record, provider=provider)

            # Run validation checks
            record_issues.extend(validate_required_fields(mapped, model_name))
            record_issues.extend(validate_field_types(mapped, model_name))
            record_issues.extend(validate_constraints(mapped, model_name, []))
            record_issues.extend(validate_foreign_keys(mapped, model_name))

            if record_issues:
                results['invalid_records'] += 1
                results['issues'].append({
                    'record_index': i,
                    'record_id': record.get('id', 'unknown'),
                    'issues': record_issues,
                })
            else:
                results['valid_records'] += 1

        except Exception as e:
            results['invalid_records'] += 1
            results['issues'].append({
                'record_index': i,
                'record_id': record.get('id', 'unknown'),
                'issues': [f"❌ Mapping error: {str(e)}"],
            })

    return results
```

**Run validation**:
```bash
# In Django shell
docker-compose exec web python manage.py shell

# Run validation script
validation_results = validate_sample_data('go365', 'Flight', sample_flights)

# Print results
print(f"Total: {validation_results['total_records']}")
print(f"Valid: {validation_results['valid_records']}")
print(f"Invalid: {validation_results['invalid_records']}")

for issue in validation_results['issues']:
    print(f"\nRecord {issue['record_index']} ({issue['record_id']}):")
    for problem in issue['issues']:
        print(f"  {problem}")
```

### Step 7: Identify Model Changes Needed

Based on validation results, recommend model field changes:

**Common fixes**:

1. **Make field optional** (if API doesn't always provide value):
   ```python
   # BEFORE
   airline_code = models.CharField(max_length=50)

   # AFTER
   airline_code = models.CharField(max_length=50, blank=True, default='')
   ```

2. **Make field nullable** (if value can be legitimately None):
   ```python
   # BEFORE
   departure_time = models.DateTimeField()

   # AFTER
   departure_time = models.DateTimeField(null=True, blank=True)
   ```

3. **Add default value** (if empty is acceptable):
   ```python
   # BEFORE
   available_seats = models.IntegerField()

   # AFTER
   available_seats = models.IntegerField(default=0)
   ```

4. **Increase max_length** (if API values exceed current limit):
   ```python
   # BEFORE
   flight_no = models.CharField(max_length=50)

   # AFTER
   flight_no = models.CharField(max_length=100)  # API has flight_no with 80 chars
   ```

5. **Remove unique constraint** (if API has duplicate values):
   ```python
   # BEFORE
   flight_no = models.CharField(max_length=100, unique=True)

   # AFTER
   flight_no = models.CharField(max_length=100)

   class Meta:
       unique_together = [['provider', 'period', 'flight_no']]  # More specific
   ```

### Step 8: Provide Migration Plan

Generate migration commands for model changes:

**Migration workflow**:

1. **Review current model definition**:
   ```bash
   # Read current model fields
   grep -A 20 "class Flight" wholesale/models.py
   ```

2. **Apply recommended changes to models.py**:
   ```python
   # Edit wholesale/models.py
   # Add blank=True, null=True, or default to fields as identified
   ```

3. **Create migration**:
   ```bash
   docker-compose exec web python manage.py makemigrations
   # Review the generated migration file
   ```

4. **Preview migration SQL** (optional, for safety):
   ```bash
   docker-compose exec web python manage.py sqlmigrate wholesale 0014
   ```

5. **Apply migration**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

6. **Verify migration**:
   ```bash
   docker-compose exec web python manage.py showmigrations wholesale
   ```

**Safe rollback plan** (if migration causes issues):
```bash
# Rollback to previous migration
docker-compose exec web python manage.py migrate wholesale 0013

# Or rollback all migrations for app
docker-compose exec web python manage.py migrate wholesale zero

# Re-apply migrations
docker-compose exec web python manage.py migrate
```

### Step 9: Test After Changes

After applying model changes, re-run validation:

**Validation test script**:
```python
# Test with actual sync command (limited)
from django.core.management import call_command

# Sync 5 records to test
call_command('sync_{provider}', limit=5, verbosity=2)

# Check database
from wholesale.models import Flight, Country, ProgramTour

# Verify counts
print(f"Flights created: {Flight.objects.filter(provider__code='{provider}').count()}")

# Check for validation errors
# Should be 5 flights if all passed validation
```

**Success criteria**:
- All sample records pass validation
- Sync command creates expected number of records
- No IntegrityError exceptions
- No silent failures (processed count == saved count)

### Step 10: Generate Validation Report

Provide comprehensive report to user:

```markdown
## Validation Report: {Provider} - {Model}

### Summary
- **Provider**: {provider_code}
- **Model**: {model_name}
- **Sample size**: {total_records} records
- **Valid**: {valid_records} ({percentage}%)
- **Invalid**: {invalid_records} ({percentage}%)

### Validation Results

#### ✅ Passing Records: {valid_count}
These records can be saved without modification.

#### ❌ Failing Records: {invalid_count}

**Record 1 (ID: {record_id})**:
- ❌ flight_no: Value is empty string
- ❌ airline_code: Value is None
- ⚠ departure_time: Expected datetime, got string

**Record 2 (ID: {record_id})**:
- ❌ period: Foreign key does not exist
- ⚠ flight_no: Length exceeds max_length (75 > 50)

### Required Model Changes

#### High Priority (Prevents saving)

**File**: `wholesale/models.py` (lines 150-160)

1. **Make airline_code optional**:
   ```python
   # BEFORE
   airline_code = models.CharField(max_length=50)

   # AFTER
   airline_code = models.CharField(max_length=50, blank=True, default='')
   ```
   **Reason**: 15/20 sample records have empty airline_code

2. **Make airline_name optional**:
   ```python
   # BEFORE
   airline_name = models.CharField(max_length=200)

   # AFTER
   airline_name = models.CharField(max_length=200, blank=True, default='')
   ```
   **Reason**: 12/20 sample records have empty airline_name

#### Medium Priority (Improves compatibility)

3. **Increase flight_no max_length**:
   ```python
   # BEFORE
   flight_no = models.CharField(max_length=50)

   # AFTER
   flight_no = models.CharField(max_length=100)
   ```
   **Reason**: 2/20 records have flight_no longer than 50 chars (max: 75)

### Migration Commands

```bash
# 1. Apply model changes to wholesale/models.py

# 2. Create migration
docker-compose exec web python manage.py makemigrations

# 3. Apply migration
docker-compose exec web python manage.py migrate

# 4. Verify with limited sync
docker-compose exec web python manage.py sync_{provider} --limit 5

# 5. Check results
docker-compose exec web python manage.py shell
>>> from wholesale.models import Flight
>>> Flight.objects.filter(provider__code='{provider}').count()
5  # Should match --limit value
```

### Next Steps

1. ✅ Apply recommended model changes
2. ✅ Run migrations
3. ✅ Test with `--limit 5` sync
4. ✅ Verify all 5 records saved
5. ✅ Run full sync if successful
6. ✅ Monitor for errors in production

### Potential Issues

⚠ **Foreign Key Dependencies**: Period FK required but API doesn't provide period ID
- **Solution**: Sync periods before flights, or create period inline

⚠ **Data Type Mismatches**: API returns "2026-03-15 10:30:00" as string
- **Solution**: Normalizer should parse to datetime object

⚠ **Duplicate Values**: Multiple flights with same flight_no
- **Solution**: Remove unique=True or use unique_together with provider+period
```

## Validation Checklist

Use this checklist for each provider/model validation:

- [ ] Identified provider and model to validate
- [ ] Fetched sample API data (5-10 records minimum)
- [ ] Analyzed model field requirements (required vs optional)
- [ ] Mapped API data using provider's mapper
- [ ] Validated required fields are populated
- [ ] Checked data types match model expectations
- [ ] Verified foreign key references exist
- [ ] Identified unique constraint conflicts
- [ ] Listed all failing validation checks
- [ ] Recommended specific model field changes
- [ ] Provided migration commands
- [ ] Generated validation report for user
- [ ] Tested changes with limited sync (--limit 5)
- [ ] Confirmed all test records saved successfully

## Provider-Specific Validation Examples

### CheckIn Group Validation

**Data Quality**: 85/100 (High quality, complete pricing)

**Common validation needs**:

1. **JSON Pricing Structure** (base_prices field):
   ```python
   def validate_checkingroup_pricing(period_data):
       """Validate CheckIn Group base_prices JSON structure."""
       issues = []

       base_prices = period_data.get('base_prices', {})
       expected_keys = [
           'priceAdultDouble',
           'priceAdultTriple',
           'priceChild',
           'priceSingle',
           'priceExtraBed'
       ]

       for key in expected_keys:
           if key not in base_prices:
               issues.append(f"Missing price key: {key}")
           elif not isinstance(base_prices[key], (int, float)):
               issues.append(f"Invalid price type for {key}: {type(base_prices[key])}")

       return issues
   ```

2. **Status Normalization**:
   ```python
   # CheckIn Group status values
   valid_statuses = ['on_sale', 'sold_out', 'wait_list', 'cancelled']

   def validate_status(tour_data):
       """Ensure status maps to expected enum."""
       raw_status = tour_data.get('status', '')
       normalized = normalize_status(raw_status)  # From normalizer

       if normalized not in valid_statuses:
           return f"Status '{raw_status}' doesn't map to valid enum"
       return None
   ```

3. **ISO Code Mapping Coverage**:
   ```python
   def validate_country_mapping():
       """Check if all Thai country names map to ISO codes."""
       # CheckIn Group provides Thai names
       thai_countries_from_api = ["ญี่ปุ่น", "เกาหลี", "ไต้หวัน", ...]

       unmapped = []
       for thai_name in thai_countries_from_api:
           iso_code = get_iso_code_from_thai(thai_name)
           if not iso_code:
               unmapped.append(thai_name)

       print(f"Unmapped countries: {len(unmapped)}/{len(thai_countries_from_api)}")
       for country in unmapped:
           print(f"  - {country}")
   ```

4. **Airline Parsing Validation**:
   ```python
   def validate_airline_parsing():
       """Test airline extraction from vehicle string."""
       test_cases = [
           ("Thai Airways (TG)", "Thai Airways", "TG"),
           ("Emirates Airlines (EK)", "Emirates Airlines", "EK"),
           ("Budget Airline", None, None),  # No code
           ("(XX)", None, "XX"),  # No name
       ]

       for vehicle, expected_name, expected_code in test_cases:
           result = parse_airline_from_vehicle(vehicle)
           if result != (expected_name, expected_code):
               print(f"FAIL: {vehicle} → Got {result}, expected ({expected_name}, {expected_code})")
   ```

**Critical files**:
- Mapper: `wholesale/provider_mappers.py` (CheckInGroupMapper, lines 612-924)
- Normalizer: `wholesale/field_normalizers.py` (CheckInGroupNormalizer, lines 443-532)
- Sync: `wholesale/management/commands/sync_checkingroup.py`

### Unique Inter Validation

**Data Quality**: 60/100 (Limited pricing, complex country extraction)

**Common validation needs**:

1. **Country Extraction Pattern Testing**:
   ```python
   def validate_country_extraction():
       """Test country extraction from various title formats."""
       test_titles = [
           "UI_ASIA001A_Vietnam Danang Fun Day Details 5 Days 4 Nights",
           "UI_EU026_Eastern Europe 8 Days",
           "UI_HK001_Hong Kong 4 Days",
           "UI_JP015_Japan 7 Days Details Winter",
           "UI_PROMO99_Christmas Special Europe",  # INVALID - "Christmas" not a country
       ]

       for title in test_titles:
           country = extract_country_from_title(title)
           iso_code = get_iso_code_for_country(country) if country else None

           print(f"Title: {title}")
           print(f"  → Country: {country}")
           print(f"  → ISO: {iso_code}")
           print(f"  → Valid: {iso_code is not None}\n")
   ```

2. **Country FK Consistency Check**:
   ```python
   def validate_country_fk_consistency():
       """Check tours with country_name but no country FK."""
       from wholesale.models import ProgramTour

       # Tours with country_name but null FK
       inconsistent = ProgramTour.objects.filter(
           provider__code='unique_inter',
           country__isnull=True
       ).exclude(country_name='')

       print(f"Tours needing review: {inconsistent.count()}")

       # Sample issues
       for tour in inconsistent[:10]:
           print(f"Tour {tour.provider_tour_id}: country_name='{tour.country_name}', FK=None")

       # Use needs_country_review property
       needs_review = [t for t in inconsistent if t.needs_country_review]
       print(f"Flagged for manual review: {len(needs_review)}")
   ```

3. **RawVendorData Error Tracking**:
   ```python
   def validate_raw_vendor_data():
       """Check for processing errors in two-stage pipeline."""
       from wholesale.models import RawVendorData

       failed = RawVendorData.objects.filter(
           provider__code='unique_inter',
           processed=False
       ).exclude(error_message='')

       print(f"Failed raw records: {failed.count()}")

       # Group by error type
       error_types = {}
       for raw in failed:
           error_msg = raw.error_message[:50]  # First 50 chars
           error_types[error_msg] = error_types.get(error_msg, 0) + 1

       print("\nError breakdown:")
       for error, count in sorted(error_types.items(), key=lambda x: -x[1]):
           print(f"  {count}x: {error}")
   ```

4. **Title Format Variations**:
   ```python
   def validate_title_format_robustness():
       """Test extraction with unusual title formats."""
       edge_cases = [
           # Standard format
           "UI_ASIA001_Thailand Bangkok 5 Days 4 Nights",

           # Multi-word country
           "UI_EU001_United Kingdom London 7 Days",

           # Region instead of country
           "UI_EU015_Eastern Europe 10 Days",

           # No "Details" keyword
           "UI_HK001_Hong Kong",

           # Extra spaces
           "UI_JP001_Japan  Tokyo  5  Days",

           # Missing underscores
           "UI ASIA001 Vietnam 5 Days",
       ]

       for title in edge_cases:
           try:
               country = extract_country_from_title(title)
               status = "✓ Extracted" if country else "✗ Failed"
               print(f"{status}: {title} → {country}")
           except Exception as e:
               print(f"✗ Error: {title} → {str(e)}")
   ```

5. **Category Discovery Validation**:
   ```python
   def validate_category_setup():
       """Ensure all required categories are active."""
       from wholesale.models import ProviderCategory, Provider

       provider = Provider.objects.get(code='unique_inter')

       # Expected categories (from API)
       expected_categories = [59, 60, 61, 62, 63, 64]  # Europe, Russia, UK, HK, Promo, Vietnam

       active = ProviderCategory.objects.filter(
           provider=provider,
           is_active=True
       )

       active_ids = [int(cat.category_id) for cat in active]
       missing = [cat_id for cat_id in expected_categories if cat_id not in active_ids]

       print(f"Active categories: {len(active_ids)}/{len(expected_categories)}")
       if missing:
           print(f"Missing categories: {missing}")
           print("Run: python manage.py sync_unique_inter_categories")
   ```

**Critical files**:
- Sync: `wholesale/management/commands/sync_unique_inter.py`
- Category Discovery: `wholesale/management/commands/sync_unique_inter_categories.py`
- Extraction: `wholesale/data_sync_service.py` (lines 1100-1151)
- Mapper: `wholesale/provider_mappers.py` (UniqueInterMapper, lines 926-1104)
- Models: `wholesale/models.py` (needs_country_review property, lines 436-438)
- Audit: `wholesale/management/commands/audit_tour_countries.py`

## Common Validation Failures

### Failure 1: Required Field Empty

**Symptom**: IntegrityError - NOT NULL constraint failed

**Example**:
```
IntegrityError: NOT NULL constraint failed: wholesale_flight.airline_code
```

**Fix**: Make field optional
```python
airline_code = models.CharField(max_length=50, blank=True, default='')
```

### Failure 2: Foreign Key Missing

**Symptom**: ValueError - Invalid FK reference

**Example**:
```
ValueError: Cannot assign None: "Flight.period" does not allow null values
```

**Fix**: Either make FK nullable or ensure referenced object exists first
```python
# Option 1: Make nullable
period = models.ForeignKey(Period, null=True, blank=True, on_delete=models.SET_NULL)

# Option 2: Create period before flight (better)
period = Period.objects.get_or_create(...)
flight.period = period
```

### Failure 3: Unique Constraint Violation

**Symptom**: IntegrityError - UNIQUE constraint failed

**Example**:
```
IntegrityError: UNIQUE constraint failed: wholesale_country.provider_id, wholesale_country.provider_country_id
```

**Fix**: Use update_or_create instead of create
```python
# Instead of
Country.objects.create(provider=provider, provider_country_id='TH')

# Use
Country.objects.update_or_create(
    provider=provider,
    provider_country_id='TH',
    defaults={'name': 'Thailand'}
)
```

### Failure 4: Max Length Exceeded

**Symptom**: DataError - Value too long

**Example**:
```
DataError: value too long for type character varying(50)
```

**Fix**: Increase max_length
```python
# BEFORE
flight_no = models.CharField(max_length=50)

# AFTER
flight_no = models.CharField(max_length=100)
```

## Tools to Use

- **Read** - Read model files, mapper files, API responses
- **Bash** - Run Django shell, fetch API data, run migrations
- **Grep** - Search for field definitions, constraint patterns
- **Edit** - Apply model field changes
- **Write** - Create validation scripts

## Expected Output

Provide the user with:

1. **Validation summary** - How many records pass/fail
2. **Detailed issues** - Specific validation failures per record
3. **Model changes** - Exact code changes with file paths and line numbers
4. **Migration plan** - Step-by-step migration commands
5. **Testing steps** - How to verify fixes work
6. **Rollback plan** - How to undo changes if needed

## Success Metrics

After validation and fixes:

- ✅ 100% of sample records pass validation
- ✅ No IntegrityError exceptions during sync
- ✅ Processed count equals saved count
- ✅ All model fields compatible with API data
- ✅ Migrations applied successfully
- ✅ Full sync completes without errors
