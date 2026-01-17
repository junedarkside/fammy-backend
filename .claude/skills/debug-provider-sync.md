---
name: debug-provider-sync
description: Use when provider sync commands appear successful but no data saves to database. Diagnoses silent failures, constraint violations, and model validation issues. Examples - "sync_go365 shows success but Django admin empty", "Flight sync not working", "Countries not appearing in database"
model: sonnet
---

# Provider Sync Debugger

## Purpose

Diagnose why provider sync commands run without errors but fail to save data to the database. Identifies silent failures, model constraint violations, and validation issues.

## When to Use This Skill

- Sync command completes successfully but Django admin shows no new records
- Logs show "success" messages but database counts don't increase
- No Python exceptions raised but data isn't persisted
- Suspect model field constraints are blocking saves
- Need to trace where data is lost in the sync pipeline

## Debugging Workflow

### Step 1: Identify the Provider

Ask the user which provider is experiencing sync issues:
- `zego` - Zego API provider
- `unique_inter` - Unique Inter API provider
- `checkingroup` - CheckIn Group API provider
- `go365` - Go365 API provider

Get the specific sync command they're running, e.g.:
```bash
python manage.py sync_go365
python manage.py sync_checkingroup --tour-id 12345
```

### Step 2: Run Sync with Verbose Output

Execute the sync command through Docker and capture full output:

```bash
docker-compose exec web python manage.py sync_<provider> --verbosity 2
```

Carefully examine the console output for:
- **WARNING messages** - Often indicate skipped records
- **Success counts** - Compare "processed X items" vs "saved Y items"
- **Silent skips** - Records processed but not mentioned in save confirmations
- **Stack traces** - Even partial tracebacks hint at issues

**Red flags in output**:
- "Successfully processed 50 tours" but no "Saved tour..." messages
- Warnings like "Skipping flight: Missing flight_no"
- Generic exceptions caught and suppressed
- Mismatch between API response count and saved count

### Step 3: Verify Database State

Check actual database records for the provider:

```bash
docker-compose exec web python manage.py shell
```

```python
from wholesale.models import Provider, Country, ProgramTour, Period, Flight, Itinerary

# Get the provider
provider = Provider.objects.get(code='<provider_code>')

# Check actual counts
print(f"Countries: {Country.objects.filter(provider=provider).count()}")
print(f"Tours: {ProgramTour.objects.filter(provider=provider).count()}")
print(f"Periods: {Period.objects.filter(provider=provider).count()}")
print(f"Flights: {Flight.objects.filter(provider=provider).count()}")
print(f"Itineraries: {Itinerary.objects.filter(provider=provider).count()}")

# Check latest records
print("\nLatest 5 tours:")
for tour in ProgramTour.objects.filter(provider=provider).order_by('-id')[:5]:
    print(f"  - {tour.id}: {tour.name}")
```

**Compare**:
- Expected count (from API response or log messages)
- Actual count (from database queries)
- If actual < expected, data is being lost

### Step 4: Analyze Model Constraints

Inspect the Django models for constraint violations that cause silent failures:

**File locations**:
- `wholesale/models.py` - Country, Flight, Itinerary, Period, ProgramTour models

**Common constraint issues**:

1. **NOT NULL violations** - Required fields without `blank=True` or `null=True`:
   ```python
   # PROBLEM: Field required but API may not provide it
   airline_code = models.CharField(max_length=50)

   # FIX: Allow blank/null or provide default
   airline_code = models.CharField(max_length=50, blank=True, default='')
   ```

2. **UNIQUE constraint violations** - Duplicate values for unique fields:
   ```python
   # PROBLEM: Multiple records with same value
   flight_no = models.CharField(max_length=100, unique=True)

   # FIX: Remove unique constraint or add provider to uniqueness
   flight_no = models.CharField(max_length=100)
   # OR
   class Meta:
       unique_together = [['provider', 'flight_no']]
   ```

3. **Missing defaults for required fields**:
   ```python
   # PROBLEM: Required field with no way to set value
   price = models.DecimalField(max_digits=10, decimal_places=2)

   # FIX: Add default or make optional
   price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
   ```

4. **Foreign key validation failures**:
   ```python
   # PROBLEM: Referenced object doesn't exist
   provider = models.ForeignKey(Provider, on_delete=models.CASCADE)

   # CHECK: Does the provider record exist?
   # FIX: Create provider first or use blank=True, null=True
   ```

**How to find constraint issues**:

Read the model file and check each field:
```bash
# Use Read tool on wholesale/models.py
# Look for fields without blank=True or default values
# Compare against API data to see which fields might be empty
```

### Step 5: Trace the Sync Pipeline

Follow the data flow from API to database:

**Typical sync pipeline**:
```
API Response → Mapper → Normalizer → Model.objects.create() → Database
```

**Check each stage**:

1. **API Response** - Does the API return the expected data?
   - Add logging in management command to print raw API response
   - Verify JSON structure matches mapper expectations

2. **Mapper** (`wholesale/provider_mappers.py`) - Does it extract fields correctly?
   - Check `map_country_data()`, `map_tour_data()`, etc.
   - Verify all required model fields are mapped
   - Look for missing keys in raw_data that cause KeyError

3. **Normalizer** (`wholesale/field_normalizers.py`) - Does it transform data correctly?
   - Check normalization methods return valid values
   - Ensure no None/empty returns for required fields
   - Validate data type conversions (str→int, str→date)

4. **Model Save** - Does the save operation succeed?
   - Add try/except around .create() calls with full traceback
   - Log the exact data being saved
   - Check if save succeeds but related objects fail

### Step 6A: Debug Two-Stage Pipelines (Unique Inter Pattern)

Some providers use a two-stage sync process: **Fetch → Process**

**Pattern**: Raw API data saved to `RawVendorData`, then processed into models

**Example**: Unique Inter sync command
```bash
# Stage 1: Fetch raw data from API
python manage.py sync_unique_inter --fetch-only

# Stage 2: Process raw data into models
python manage.py sync_unique_inter --process-only

# Both stages (default)
python manage.py sync_unique_inter
```

**Debugging two-stage pipelines**:

1. **Check RawVendorData for errors**:
   ```python
   from wholesale.models import RawVendorData, Provider

   provider = Provider.objects.get(code='unique_inter')

   # Find failed processing
   failed_raw = RawVendorData.objects.filter(
       provider=provider,
       processed=False
   ).exclude(error_message='')

   print(f"Failed raw records: {failed_raw.count()}")

   # Inspect errors
   for raw in failed_raw[:10]:
       print(f"\nRecord {raw.external_id}:")
       print(f"  Error: {raw.error_message}")
       print(f"  Data: {raw.data[:200]}...")  # First 200 chars
   ```

2. **Identify which stage failed**:
   ```python
   # Stage 1 failure (Fetch)
   # - RawVendorData record doesn't exist
   # - Check API connection, authentication
   # - Review fetch logic in sync command

   # Stage 2 failure (Process)
   # - RawVendorData exists but processed=False
   # - error_message field contains details
   # - Check mapper, normalizer, model constraints
   ```

3. **Trace processing errors**:
   ```python
   # Read the processing code
   # File: wholesale/management/commands/sync_unique_inter.py (lines 95-172)

   # Check what causes processed=False with error_message
   # Common issues:
   # - Country extraction failure
   # - Invalid date format
   # - Missing required field
   # - Model constraint violation
   ```

4. **Verify category setup** (Unique Inter specific):
   ```python
   from wholesale.models import ProviderCategory

   # Check active categories
   active_categories = ProviderCategory.objects.filter(
       provider=provider,
       is_active=True
   )

   print(f"Active categories: {active_categories.count()}")
   for cat in active_categories:
       print(f"  - {cat.category_id}: {cat.category_name}")

   # Missing categories cause tours to be skipped silently
   # Run category discovery:
   # python manage.py sync_unique_inter_categories
   ```

5. **Re-process failed records**:
   ```bash
   # After fixing issues, re-process specific raw records
   python manage.py sync_unique_inter --process-only

   # Or clear error flags and retry
   ```

**Benefits of two-stage pattern**:
- Raw API data preserved for debugging
- Can re-process without re-fetching (API rate limits)
- Error tracking per record via `error_message` field
- Allows iterative improvement of processing logic

**Trade-offs**:
- More complex debugging (need to check two stages)
- Extra database storage for raw data
- Need to manage RawVendorData cleanup/expiry

### Step 6: Identify Error Patterns

**Pattern 1: Silent IntegrityError**

Sync command catches exceptions but doesn't log them:

```python
# BAD: Suppresses errors
try:
    Flight.objects.create(**flight_data)
except Exception:
    pass  # Silent failure!

# GOOD: Log full traceback
try:
    Flight.objects.create(**flight_data)
except Exception as e:
    self.stdout.write(self.style.ERROR(f'ERROR creating flight: {str(e)}'))
    import traceback
    self.stdout.write(traceback.format_exc())
```

**Pattern 2: Validation Errors Not Logged**

Model validation fails but error isn't visible:

```python
# BAD: ValidationError caught but not logged
try:
    flight = Flight(**flight_data)
    flight.full_clean()  # Validates model
    flight.save()
except ValidationError:
    continue  # Silent skip!

# GOOD: Log validation failures
try:
    flight = Flight(**flight_data)
    flight.full_clean()
    flight.save()
except ValidationError as e:
    self.stdout.write(self.style.WARNING(f'Validation failed for flight: {e}'))
```

**Pattern 3: Required Field Missing**

API doesn't provide value for required model field:

```python
# BAD: Assumes field exists in API response
flight_data = {
    'flight_no': raw_data['flightNumber'],  # KeyError if missing!
    'airline_code': raw_data['airlineCode'],  # KeyError if missing!
}

# GOOD: Validate before access
if not raw_data.get('flightNumber'):
    self.stdout.write(self.style.WARNING('Skipping flight: Missing flight_no'))
    continue

flight_data = {
    'flight_no': raw_data['flightNumber'],
    'airline_code': raw_data.get('airlineCode', ''),  # Safe default
}
```

### Step 7: Provide Actionable Fixes

Based on the diagnosis, recommend specific fixes with file paths and line numbers:

**Fix Type 1: Model Field Changes**

```markdown
**Issue**: Flight.airline_code is required but API doesn't always provide it

**Fix**: Make field optional in `wholesale/models.py`

File: `wholesale/models.py` (lines 150-160)

Change:
```python
airline_code = models.CharField(max_length=50)
```

To:
```python
airline_code = models.CharField(max_length=50, blank=True, default='')
```

Then run migration:
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

**Fix Type 2: Add Error Logging**

```markdown
**Issue**: Exceptions are caught but not logged in sync command

**Fix**: Add traceback logging in `wholesale/management/commands/sync_<provider>.py`

File: `wholesale/management/commands/sync_go365.py` (line 234)

Change:
```python
except Exception as e:
    self.stdout.write(self.style.WARNING(f'Error: {str(e)}'))
```

To:
```python
except Exception as e:
    self.stdout.write(self.style.ERROR(f'ERROR syncing flight: {str(e)}'))
    import traceback
    self.stdout.write(traceback.format_exc())
```

**Fix Type 3: Add Validation Before Save**

```markdown
**Issue**: Missing required fields cause silent save failures

**Fix**: Validate fields before creating model instances

File: `wholesale/management/commands/sync_go365.py` (line 200)

Add before Flight.objects.create():
```python
# Validate required fields
if not flight_fields.get('flight_no'):
    self.stdout.write(
        self.style.WARNING(f'Skipping flight: Missing flight_no')
    )
    continue

if not flight_fields.get('departure_airport'):
    self.stdout.write(
        self.style.WARNING(f'Skipping flight {flight_fields.get("flight_no")}: Missing departure_airport')
    )
    continue
```

**Fix Type 4: Change Log Level**

```markdown
**Issue**: Important errors logged as WARNING instead of ERROR

**Fix**: Change log level for visibility

File: `wholesale/management/commands/sync_go365.py` (multiple lines)

Change all:
```python
self.stdout.write(self.style.WARNING(f'Error: ...'))
```

To:
```python
self.stdout.write(self.style.ERROR(f'ERROR: ...'))
```

This makes errors visible in red instead of yellow.

## Common Issues from Real Cases

### Case Study: Go365 Flight Sync (2026-01-16)

**Symptoms**:
- Command reported "Successfully synced Go365 flights"
- Django admin showed 0 flights for Go365 provider
- No Python exceptions or errors in logs

**Root Cause**:
1. `Flight.airline_code` and `Flight.airline_name` were required (no blank=True)
2. API sometimes returned empty strings for these fields
3. Django silently failed to save records with empty required fields
4. Exceptions were logged as WARNING (yellow) instead of ERROR (red)
5. No traceback was printed, hiding the actual IntegrityError

**Fixes Applied**:
1. Added `blank=True, default=''` to 8 Flight model fields (wholesale/models.py:150-160)
2. Changed WARNING to ERROR for exception logging (wholesale/management/commands/sync_go365.py:234, 267, 298)
3. Added full traceback logging with `import traceback; traceback.format_exc()`
4. Added validation before save to skip records with missing required fields
5. Created migration 0013 to update Flight model constraints

**Result**:
- 147 flights successfully saved to database
- Errors now visible with full stack traces
- Invalid records skipped with clear warning messages

### Case Study: Unique Inter Country Extraction (2026-01-17)

**Symptoms**:
- Countries appeared in API response
- Countries extracted to tour.country_name field
- But no Country model records created via FK
- Foreign key tour.country remained null
- Invalid country names extracted: "Christmas", "Winter", "Colorful", "Dreams"

**Root Cause**:
1. Country extraction from tour titles (format: `PREFIX_CODE_CountryName Details Days`)
2. Title parsing depends on exact format, fails with unusual patterns
3. Complex multi-word regions: "Eastern Europe", "Hong Kong", "United Kingdom"
4. No robust fallback beyond API's Country field
5. Country FK assignment happens after extraction but fails silently

**Fixes Applied**:
1. Added audit command: `audit_tour_countries --provider-code unique_inter`
2. Created property `needs_country_review` to flag FK inconsistencies (wholesale/models.py:436-438)
3. Django admin indicators: ✓ Green (valid), ⚠ Orange (needs review), ✗ Red (missing)
4. Manual admin review required for failed extractions
5. Improved title extraction logic in `data_sync_service.py:1100-1151`

**Known Issue (Documented in CLAUDE.md)**:
- Country extraction failures still require manual admin intervention
- Title format sensitivity means new tour patterns may fail extraction
- Two-stage pipeline (RawVendorData → ProgramTour) tracks errors via `error_message` field

**Files Involved**:
- Sync: `wholesale/management/commands/sync_unique_inter.py`
- Extraction: `wholesale/data_sync_service.py` (lines 1100-1151)
- Models: `wholesale/models.py` (needs_country_review property, lines 436-438)
- Audit: `wholesale/management/commands/audit_tour_countries.py`

### Case Study: CheckIn Group Country Creation (2026-01-17)

**Symptoms**:
- API returns countries array in Thai: `["ญี่ปุ่น", "เกาหลี"]` (Japan, Korea)
- ISO code mapping works for common countries
- But uncommon country names fail 2-to-3 letter ISO conversion
- Country FK remains null when mapping fails
- No error logging for failed country creation

**Root Cause**:
1. CheckIn Group provides Thai country names
2. Mapper converts Thai → English → ISO 2-letter code
3. ISO 2 → ISO 3 conversion only covers common countries
4. Missing countries array leaves country FK null
5. No logger imported in sync command (wholesale/management/commands/sync_checkingroup.py)

**Potential Issues**:
1. **Airline Parsing Edge Cases** (provider_mappers.py:659-666):
   - Vehicle format "NAME (CODE)" parsing may fail if format differs
   - Empty airline_code if format doesn't match regex pattern

2. **Status Normalization** (field_normalizers.py:499-509):
   - Unexpected status values fall back to raw API string
   - No validation that status maps to expected enum

3. **Limited Error Tracking**:
   - Generic exception messages without tour/period context
   - No per-tour error tracking (unlike Unique Inter's RawVendorData)

**Recommended Fixes**:
1. Import logger and add comprehensive logging:
   ```python
   import logging
   logger = logging.getLogger(__name__)

   logger.info(f"Processing tour {tour_data['code']}: {tour_data['name']}")
   if not country:
       logger.error(f"Failed to create country for {tour_data.get('countries', [])}")
   ```

2. Validate required fields before save:
   ```python
   if not tour_fields.get('code'):
       self.stdout.write(self.style.WARNING(f"Skipping tour: Missing code"))
       continue
   ```

3. Track airline parsing failures:
   ```python
   vehicle_str = flight_data.get('vehicle', '')
   match = re.match(r'^(.+?)\s*\(([A-Z0-9]+)\)$', vehicle_str)
   if not match:
       logger.warning(f"Failed to parse airline from: {vehicle_str}")
   ```

**Files Involved**:
- Sync: `wholesale/management/commands/sync_checkingroup.py` (115 lines)
- Mapper: `wholesale/provider_mappers.py` (CheckInGroupMapper, lines 612-924)
- Normalizer: `wholesale/field_normalizers.py` (CheckInGroupNormalizer, lines 443-532)
- Admin: `wholesale/admin.py` (lines 95-134)

## Success Metrics

After applying fixes, verify:

1. **Database counts match expectations**:
   ```python
   # Expected: API returned 150 flights
   # Actual: 147 flights in database (3 skipped due to missing data)
   ```

2. **Error logs show actionable information**:
   ```
   ERROR syncing flight: NOT NULL constraint failed: wholesale_flight.airline_code
   Traceback (most recent call last):
     File "...", line 234, in sync_flights
       Flight.objects.create(**flight_data)
   django.db.utils.IntegrityError: NOT NULL constraint failed...
   ```

3. **Skipped records are logged with reasons**:
   ```
   WARNING: Skipping flight AF123: Missing departure_airport
   WARNING: Skipping flight BA456: Missing arrival_airport
   ```

4. **Re-running sync command shows consistent results**:
   ```bash
   # First run: 147 flights created
   # Second run: 0 flights created (all already exist)
   # Third run: 0 flights created (idempotent)
   ```

## Quick Diagnostic Checklist

When debugging provider sync, check these in order:

- [ ] Run sync command with `--verbosity 2`
- [ ] Check console output for WARNING/ERROR messages
- [ ] Count expected vs actual records in database
- [ ] Read model file for required fields without defaults
- [ ] Check mapper for missing field extractions
- [ ] Verify normalizer handles all edge cases
- [ ] Add try/except with full traceback around save operations
- [ ] Validate required fields before save
- [ ] Change WARNING to ERROR for critical issues
- [ ] Test with single record first (`--limit 1`)
- [ ] Verify fix with full sync
- [ ] Confirm database counts match expectations

## Tools to Use

- **Read** - Read model files, mapper files, management commands
- **Grep** - Search for error patterns, field names, exception handling
- **Bash** - Run sync commands, database queries, Django shell
- **Edit** - Apply fixes to model fields, logging, validation
- **WebFetch** - Check provider API documentation if needed

## Expected Output

Provide the user with:

1. **Diagnosis**: Clear explanation of what's preventing data from saving
2. **Root cause**: Specific model fields, constraints, or code issues
3. **Fixes**: Exact code changes with file paths and line numbers
4. **Migration commands**: If model changes are needed
5. **Verification steps**: How to confirm the fix works
6. **Expected results**: What success looks like (counts, logs, behavior)

## Remember

- Always check database counts, don't trust log messages alone
- Silent failures are often model constraint violations
- Required fields without defaults are the #1 cause of sync issues
- Exceptions logged as WARNING are easy to miss
- Full tracebacks are essential for diagnosing IntegrityErrors
- Test fixes with `--limit 1` before running full sync
