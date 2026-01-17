# Claude Code Skills

This directory contains specialized Claude Code skills for the B2B Travel Platform.

## Available Skills

### `/debug-provider-sync`
**Diagnose provider sync failures**

Use when provider sync commands appear successful but no data saves to database. Diagnoses silent failures, constraint violations, and model validation issues.

**When to use**:
- Sync command completes but Django admin shows no new records
- Logs show "success" but database counts don't increase
- Suspect model field constraints are blocking saves
- Need to trace where data is lost in sync pipeline

**What it does**:
1. Runs sync command with verbose output
2. Compares expected vs actual database counts
3. Analyzes model constraints (NOT NULL, UNIQUE, etc.)
4. Identifies where data is being silently dropped
5. Provides specific fixes with file paths and line numbers

**Example usage**:
```
User: "sync_go365 shows success but Django admin is empty"
Assistant: [Runs debug-provider-sync skill]
Result: Identifies that Flight.airline_code requires blank=True, provides exact model changes and migration commands
```

### `/integrate-provider`
**Add new tour provider/wholesaler API**

Use when integrating a new tour provider. Analyzes API responses and generates mapper, normalizer, and sync command code.

**When to use**:
- Adding completely new tour provider to platform
- Integrating wholesaler API with different data structure
- Creating sync commands for new data source
- Need boilerplate code for provider integration

**What it does**:
1. Asks for provider details (name, API URL, auth method)
2. Analyzes sample API responses
3. Generates `ProviderMapper` class with mapping methods
4. Creates `ProviderNormalizer` if provider has unique formats
5. Generates management command `sync_<provider>.py`
6. Updates Django admin with sync action
7. Creates provider documentation

**Example usage**:
```
User: "I need to integrate TravelHub API"
Assistant: [Runs integrate-provider skill]
Result: Generates complete mapper, normalizer, sync command, and documentation for TravelHub
```

### `/validate-models`
**Validate Django models before sync**

Use before running provider sync to ensure Django models can handle API data. Prevents constraint violations and silent failures.

**When to use**:
- Before first sync with new provider
- After adding new fields to models
- When sync commands show low success rates
- To identify which fields need `blank=True` or `null=True`
- Before deploying model changes to production

**What it does**:
1. Fetches sample data from provider API
2. Maps data through provider's mapper
3. Validates required fields are populated
4. Checks data types match model expectations
5. Verifies foreign key references exist
6. Identifies constraint violations
7. Recommends model field changes with migrations

**Example usage**:
```
User: "Check if Flight model is ready for new provider"
Assistant: [Runs validate-models skill]
Result: Validates 20 sample flights, identifies 3 fields needing blank=True, provides migration commands
```

## How Skills Work

Skills are specialized workflows that Claude Code follows when invoked. Each skill:

1. **Has a specific trigger phrase** - Use `/skill-name` to activate
2. **Follows a defined workflow** - Step-by-step process tailored to the task
3. **Uses appropriate tools** - Read, Grep, Bash, Edit, etc.
4. **Provides actionable output** - Specific fixes with file paths and line numbers

## Skill Design Principles

These skills were designed based on real debugging sessions (particularly the Go365 sync fix):

1. **Systematic approach** - Follow checklist to avoid missing issues
2. **Real data validation** - Test against actual API responses
3. **Specific fixes** - Provide exact code changes with line numbers
4. **Prevention focus** - Catch issues before they cause production failures
5. **Knowledge capture** - Codify debugging patterns for reuse

## When to Use Each Skill

```
Problem: Sync command runs but no data appears
→ Use: /debug-provider-sync

Problem: Need to add new provider
→ Use: /integrate-provider

Problem: Unsure if models ready for sync
→ Use: /validate-models
```

## Skill Workflow Example

**Scenario**: Adding new provider "TravelHub"

1. **First**: Run `/integrate-provider`
   - Analyzes TravelHub API
   - Generates mapper, normalizer, sync command
   - Creates documentation

2. **Second**: Run `/validate-models`
   - Tests generated mapper with sample data
   - Identifies required model changes
   - Provides migration commands

3. **Third**: Apply recommendations
   - Update models with suggested changes
   - Run migrations
   - Test sync with `--limit 5`

4. **If issues occur**: Run `/debug-provider-sync`
   - Diagnoses why data isn't saving
   - Identifies missed constraints
   - Provides additional fixes

## Real-World Success: Go365 Sync Fix

**Problem**: Go365 sync command reported success but 0 flights saved to database

**Solution using these skills' patterns**:
1. Ran sync with verbose output → Found no error messages
2. Checked database counts → Confirmed 0 flights
3. Analyzed Flight model → Found 8 required fields without defaults
4. Checked API data → Many flights had empty airline_code/airline_name
5. Applied fix → Added `blank=True, default=''` to 8 fields
6. Improved logging → Changed WARNING to ERROR, added tracebacks
7. Result → 147 flights successfully synced

These skills codify this debugging process for future use.

## Directory Structure

```
.claude/
├── README.md                           # This file
├── settings.local.json                 # Claude Code settings
└── skills/
    ├── debug-provider-sync.md          # Provider sync debugger
    ├── integrate-provider.md           # Provider integration helper
    └── validate-models.md              # Model validator
```

## Contributing New Skills

When creating new skills:

1. **Follow existing format**:
   ```markdown
   ---
   name: skill-name
   description: When to use (with examples)
   model: sonnet
   ---

   # Skill Title

   ## Purpose
   [Clear description]

   ## When to Use This Skill
   [Specific scenarios]

   ## Workflow
   [Step-by-step process]
   ```

2. **Make it actionable** - Provide specific fixes, not general advice
3. **Use real examples** - Reference actual files and line numbers
4. **Test thoroughly** - Verify skill workflow with real scenarios
5. **Document clearly** - Explain when and how to use the skill

## Provider-Specific Debugging Guide

The skills above work with all providers, but each provider has specific quirks to be aware of:

### CheckIn Group

**Provider Overview**:
- Type: Thai B2B wholesaler
- Data Quality: 85/100 (high quality, complete pricing)
- Pattern: Simple REST API
- Sync Command: `python manage.py sync_checkingroup`

**Common Issues**:
1. **Country Creation Failures**
   - API provides Thai country names: `["ญี่ปุ่น", "เกาหลี"]`
   - ISO 2-to-3 letter code conversion may fail for uncommon countries
   - Country FK remains null when mapping fails
   - **Skill to use**: `/debug-provider-sync` to trace creation failures

2. **Airline Parsing Edge Cases**
   - Vehicle format expected: `"NAME (CODE)"` → e.g., `"Thai Airways (TG)"`
   - Empty airline_code if format doesn't match regex
   - **Skill to use**: `/validate-models` to test format variations

3. **JSON Pricing Validation**
   - base_prices must contain: priceAdultDouble, priceAdultTriple, priceChild, priceSingle
   - Missing keys cause validation errors
   - **Skill to use**: `/validate-models` to check JSON structure

4. **Status Normalization**
   - Unexpected status values fall back to raw API string
   - **Skill to use**: `/validate-models` to verify status mapping

**Critical Files**:
- Sync: `wholesale/management/commands/sync_checkingroup.py` (115 lines)
- Mapper: `wholesale/provider_mappers.py` (CheckInGroupMapper, lines 612-924)
- Normalizer: `wholesale/field_normalizers.py` (CheckInGroupNormalizer, lines 443-532)
- Admin: `wholesale/admin.py` (lines 95-134)

**Quick Diagnostic**:
```bash
# Test sync with single tour
docker-compose exec web python manage.py sync_checkingroup --tour-id 12345

# Check for country creation failures
docker-compose exec web python manage.py shell
>>> from wholesale.models import ProgramTour
>>> tours = ProgramTour.objects.filter(provider__code='checkingroup', country__isnull=True)
>>> tours.count()  # Should be 0
```

### Unique Inter

**Provider Overview**:
- Type: Departure-centric, category-based API
- Data Quality: 60/100 (limited pricing, no flights/itineraries)
- Pattern: Two-stage pipeline (fetch → process) + Category-based (Pattern C)
- Sync Commands:
  - `python manage.py sync_unique_inter_categories` (discover categories)
  - `python manage.py sync_unique_inter` (full sync)
  - `python manage.py sync_unique_inter --fetch-only` (fetch raw data)
  - `python manage.py sync_unique_inter --process-only` (process raw data)

**ProviderCategory Pattern** (Pattern C):

Unique Inter is the **reference implementation** for category-based provider APIs. The provider API requires a category parameter to fetch tours - you cannot fetch tours without specifying a category ID.

**Why ProviderCategory is needed**:
- API endpoint: `GET /tours?category_id=59` (required parameter)
- Without category_id: API returns error or empty results
- Categories represent tour destinations: Europe (59), Russia (60), UK (61), Hong Kong (62), Promotions (63), Vietnam (64)
- Need to enable/disable categories dynamically without code changes
- Need to control sync order by priority (important for rate-limited APIs)

**Model**: `wholesale.models.ProviderCategory`
- Fields: provider, category_id, name, name_local, is_active, priority, total_tours, last_synced
- Configured via Django Admin → Wholesale → Provider Categories
- Enable/disable with `is_active` flag
- Control sync order with `priority` (higher = synced first)
- Track metadata (total_tours, last_synced) per category

**Category Discovery Workflow**:
1. Run `sync_unique_inter_categories` to discover available categories
2. Configure categories in Django Admin (set is_active=True, adjust priority)
3. Run `sync_unique_inter` to sync all active categories
4. Categories sync in priority order, metadata updates automatically

**When to use this pattern for new providers**:
- ✅ API requires category parameter (cannot fetch tours without it)
- ✅ Categories are finite and discoverable (e.g., 5-50 categories)
- ✅ Categories represent destinations, regions, or tour types
- ❌ Don't use if API returns all tours without category parameter
- ❌ Don't use if categories are optional filters or embedded tags

**Reference**: See `/integrate-provider` skill → Pattern C: Category-Based API for complete implementation guide.

**Common Issues**:
1. **Country Extraction Failures** ⚠️ **KNOWN ISSUE**
   - Invalid country names extracted: "Christmas", "Winter", "Colorful", "Dreams"
   - Title parsing depends on format: `PREFIX_TOURCODE_CountryName Details Days`
   - Complex multi-word regions: "Eastern Europe", "Hong Kong", "United Kingdom"
   - **Skill to use**: `/debug-provider-sync` (see Step 6A for two-stage debugging)
   - **Audit tool**: `python manage.py audit_tour_countries --provider-code unique_inter`

2. **Country FK Inconsistency**
   - Tours have country_name but country FK is NULL
   - Property `needs_country_review` flags these (wholesale/models.py:436-438)
   - Django admin indicators: ✓ Green (valid), ⚠ Orange (needs review), ✗ Red (missing)
   - **Skill to use**: `/validate-models` to check FK consistency

3. **Two-Stage Pipeline Debugging**
   - RawVendorData may have `processed=False` with `error_message`
   - Need to trace which stage failed (fetch vs process)
   - **Skill to use**: `/debug-provider-sync` (Step 6A covers two-stage patterns)

4. **Category Management**
   - Categories must be active for sync to work
   - Missing categories skip tours silently
   - **Skill to use**: `/validate-models` to verify category setup

5. **Title Format Sensitivity**
   - Unusual title formats fail extraction
   - No robust fallback beyond API's Country field
   - **Skill to use**: `/validate-models` to test format variations

**Critical Files**:
- Main Sync: `wholesale/management/commands/sync_unique_inter.py`
- Category Discovery: `wholesale/management/commands/sync_unique_inter_categories.py`
- Data Utilities: `wholesale/data_sync_service.py` (lines 950-1214)
- Country Extraction: `wholesale/data_sync_service.py` (lines 1100-1151)
- Mapper: `wholesale/provider_mappers.py` (UniqueInterMapper, lines 926-1104)
- Models: `wholesale/models.py` (needs_country_review property, lines 436-438)
- Audit Tool: `wholesale/management/commands/audit_tour_countries.py`

**Quick Diagnostic**:
```bash
# Check for failed raw data processing
docker-compose exec web python manage.py shell
>>> from wholesale.models import RawVendorData
>>> failed = RawVendorData.objects.filter(provider__code='unique_inter', processed=False).exclude(error_message='')
>>> failed.count()

# Audit country extraction issues
docker-compose exec web python manage.py audit_tour_countries --provider-code unique_inter

# Check active categories
>>> from wholesale.models import ProviderCategory
>>> cats = ProviderCategory.objects.filter(provider__code='unique_inter', is_active=True)
>>> cats.count()  # Should be 6 (59, 60, 61, 62, 63, 64)
```

### Go365

**Provider Overview**:
- Type: Multi-language tour API
- Data Quality: 75/100 (good coverage, detailed flights)
- Pattern: Standard REST API with pagination
- Sync Command: `python manage.py sync_go365`

**Common Issues**:
1. **Flight Model Constraint Violations** (Fixed 2026-01-16)
   - airline_code/airline_name were required but API provides empty strings
   - Silent failures due to NOT NULL constraints
   - **Fix Applied**: Added `blank=True, default=''` to 8 fields
   - **Skill to use**: `/debug-provider-sync` (see Case Study: Go365 Flight Sync)

2. **Logging Improvements** (Fixed 2026-01-16)
   - Exceptions logged as WARNING (yellow) instead of ERROR (red)
   - No full tracebacks, hiding IntegrityErrors
   - **Fix Applied**: Changed to ERROR with traceback.format_exc()
   - **Skill to use**: `/debug-provider-sync` (see Pattern 1: Silent IntegrityError)

**Success Story**: `/debug-provider-sync` skill workflow successfully identified and fixed Go365 flight sync issue, resulting in 147 flights saved after fixes applied.

### Zego

**Provider Overview**:
- Type: Standard tour provider
- Pattern: Simple REST API with separate endpoints
- Sync Command: `python manage.py sync_zego`

**Notes**: Baseline implementation, generally stable with standard patterns.

## Related Documentation

- Project instructions: [`/CLAUDE.md`](../CLAUDE.md)
- Provider integration guides: [`/docs/provider-integration/`](../docs/provider-integration/)
- Development policies: [`/docs/README.md`](../docs/README.md)
- Management commands: [`/wholesale/management/commands/`](../wholesale/management/commands/)

## Support

If you encounter issues with skills:

1. Check the skill's workflow section for step-by-step guidance
2. Review real-world examples in the skill documentation
3. Consult related provider integration guides
4. Check `CLAUDE.md` for project-specific patterns
