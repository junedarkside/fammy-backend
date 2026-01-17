# Provider Adapter Evaluation Tool

**Last Updated:** 2026-01-16
**Target Audience:** Backend developers integrating new tour providers
**Access URL:** http://localhost:8000/wholesale/evaluation/

---

## Table of Contents

1. [Overview](#overview)
2. [When to Use This Tool](#when-to-use-this-tool)
3. [How It Works](#how-it-works)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Understanding Analysis Results](#understanding-analysis-results)
6. [Recommendation Scenarios](#recommendation-scenarios)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Examples](#examples)
10. [FAQs](#faqs)

---

## Overview

### What is the Evaluation Tool?

The **Provider Adapter Evaluation Tool** is a web-based assistant that analyzes new provider API responses and recommends the best integration approach. It compares your provider's API structure against existing adapters and provides:

- **Compatibility analysis** with existing adapters (Zego, Unique Inter, Go365, CheckIn Group)
- **Smart recommendations** based on field-level compatibility
- **Auto-generated code** for new adapters
- **Step-by-step implementation guidance**

### Why Use It?

**Saves Time:**
- Identifies adapter reuse opportunities in seconds
- Auto-generates boilerplate code
- Eliminates guesswork in adapter architecture decisions

**Reduces Errors:**
- Field-level compatibility analysis
- Standardized code generation
- Pre-validated against existing patterns

**Improves Quality:**
- Consistent adapter implementation
- Better code reuse
- Clear implementation path

---

## When to Use This Tool

### ✅ Use the Evaluation Tool When:

- **New provider integration** - You have a new tour operator to integrate
- **API evaluation** - You want to assess compatibility before committing to an approach
- **Uncertain architecture** - You're not sure if you should create a new adapter or reuse existing one
- **Code generation** - You want boilerplate code to speed up development

### ❌ Skip the Tool When:

- **Minor updates** - Making small changes to existing adapters
- **Known structure** - You already know the provider has identical structure to an existing adapter
- **Non-standard integration** - Provider requires custom integration outside adapter pattern

---

## How It Works

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Step 1: Create Session                                       │
│  - Provider name, code, base URL                             │
└────────────────────┬─────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 2: Upload API Samples                                   │
│  - Tours (required)                                           │
│  - Periods, Countries, Flights, Itineraries (optional)       │
│  - Smart Paste Helper auto-splits nested data                │
└────────────────────┬─────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 3: Analyze Compatibility                                │
│  - Extract field structure                                    │
│  - Compare with existing adapters                            │
│  - Calculate compatibility scores                             │
│  - Generate recommendation                                    │
└────────────────────┬─────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 4: Follow Recommendations                               │
│  - Perfect Match (≥95%) → Reuse existing adapter             │
│  - High Match (80-94%) → Reuse with minor changes            │
│  - Moderate Match (50-79%) → Create field normalizer         │
│  - Low Match (<50%) → Create new adapter                     │
└──────────────────────────────────────────────────────────────┘
```

### 4-Tier Recommendation System

| Match Score | Recommendation | Action Required |
|-------------|----------------|-----------------|
| ≥95% | **PERFECT_MATCH** | Configure provider, run sync command |
| 80-94% | **REUSE** | Use existing adapter with minor adjustments |
| 50-79% | **REUSE_WITH_NORMALIZER** | Create field normalizer to map field names |
| <50% | **CREATE_NEW** | Create new adapter with generated code |

### Compatibility Scoring Algorithm

The tool calculates compatibility by comparing API field names:

```
Compatibility Score = (Matching Fields / Total Expected Fields) × 100
```

**Example:**
- Zego adapter expects: `ProductID`, `ProductName`, `Days`, `Nights` (4 fields)
- Your API provides: `ProductID`, `ProductName`, `Days`, `tour_duration` (3 match, 1 different)
- Score: (3 / 4) × 100 = **75%** → REUSE_WITH_NORMALIZER

---

## Step-by-Step Guide

### Step 1: Create Evaluation Session

1. **Access the tool:**
   ```
   http://localhost:8000/wholesale/evaluation/
   ```

2. **Click "Create New Session"**

3. **Fill in provider details:**
   - **Provider Name:** Display name (e.g., "Amazing Tours Thailand")
   - **Provider Code:** Lowercase code name (e.g., "amazing_tours")
   - **Base URL:** API base URL (e.g., "https://api.amazingtours.com/v1")

4. **Click "Create Session"**

### Step 2: Upload API Samples

#### Getting API Samples

Use one of these methods to get raw JSON from the provider's API:

**Method 1: curl**
```bash
curl https://api.provider.com/tours | python -m json.tool > tours.json
```

**Method 2: Postman**
1. Make API request in Postman
2. View response
3. Copy raw JSON

**Method 3: Provider Documentation**
- Check provider's API docs for sample responses
- Copy example JSON

#### Using the Smart Paste Helper

The **Smart Paste Helper** automatically splits complex API responses into separate fields.

**For nested API responses like:**
```json
{
  "data": {
    "id": 1,
    "name": "Bangkok Tour",
    "day": 5,
    "night": 4,
    "periods": [
      {"departure_date": "2024-12-01", "price": 25000}
    ],
    "countries": [
      {"code": "TH", "name": "Thailand"}
    ]
  }
}
```

**Steps:**
1. Paste the ENTIRE JSON response into the **Smart Paste** field
2. Click **"✨ Auto-Fill Fields"**
3. The tool automatically:
   - Unwraps `{"data": {...}}` structures
   - Extracts nested arrays (periods, countries, flights, itineraries)
   - Fills each form field separately
   - Removes nested arrays from tour data

**Result:**
- **Tour Sample:** `[{"id": 1, "name": "Bangkok Tour", "day": 5, "night": 4}]`
- **Period Sample:** `[{"departure_date": "2024-12-01", "price": 25000}]`
- **Country Sample:** `[{"code": "TH", "name": "Thailand"}]`

#### Manual Field Entry

If you prefer manual entry or have separate API endpoints:

1. **Tour Sample (Required):**
   - Paste array of tour objects
   - Must be valid JSON array: `[{...}]`
   - Example: `[{"tour_id": "BKK001", "name": "Bangkok 5D4N"}]`

2. **Period Sample (Optional):**
   - Departure dates and pricing
   - Example: `[{"departure_date": "2024-12-01", "adult_price": 25000}]`

3. **Country Sample (Optional):**
   - Destination countries
   - Example: `[{"country_code": "TH", "name": "Thailand"}]`

4. **Flight Sample (Optional):**
   - Flight information
   - Example: `[{"flight_number": "TG123", "airline": "Thai Airways"}]`

5. **Itinerary Sample (Optional):**
   - Day-by-day program
   - Example: `[{"day": 1, "title": "Arrival", "description": "..."}]`

#### Field Validation

- JSON is validated on blur (when you click away from the field)
- ✅ **Green border** = Valid JSON
- ❌ **Red border** = Invalid JSON

#### Click "Save Samples & Analyze"

### Step 3: View Analysis Results

The analysis page shows:

#### Recommendation Card
- **Action:** PERFECT_MATCH / REUSE / REUSE_WITH_NORMALIZER / CREATE_NEW
- **Reasoning:** Why this recommendation was made
- **Recommended Adapter:** Which existing adapter to use (if applicable)
- **Estimated Quality Score:** Expected data quality (0-100)
- **Implementation Steps:** What to do next

#### Compatibility Scores

For each existing adapter (Zego, Unique Inter, Go365, CheckIn Group):

| Adapter | Score | Matching | Missing | Extra |
|---------|-------|----------|---------|-------|
| Zego | 85% | 15 fields | 3 fields | 8 fields |
| CheckIn Group | 100% | 10 fields | 0 fields | 0 fields |

- **Matching fields:** Fields that exist in both
- **Missing fields:** Fields the adapter expects but your API doesn't have
- **Extra fields:** Fields your API has but the adapter doesn't expect

#### Field Structure

Detected fields in your API:
```
Total Fields: 26
Fields Found: id, day, pdf, code, name, note, type, visa, word, night, price, banner, remark, include, vehicle, passport, condition, createdAt, endPeriod, fullprice, highlight, updatedAt, notInclude, serviceFee, startPeriod, airTicketPrice
```

### Step 4: Follow Recommendations

Click **"Generate Adapter Code"** or **"View Implementation Guide"** depending on the recommendation.

---

## Understanding Analysis Results

### Compatibility Scores Explained

#### What Does the Score Mean?

- **95-100%:** Nearly perfect match - likely same provider or API clone
- **80-94%:** Strong compatibility - same structure, minor field name differences
- **50-79%:** Moderate compatibility - similar structure, different naming conventions
- **0-49%:** Low compatibility - different data model

#### Matching vs Missing vs Extra Fields

**Matching Fields:**
- Fields that exist in both your API and the existing adapter
- These fields can be mapped directly without changes

**Missing Fields:**
- Fields the existing adapter expects but your API doesn't provide
- May require default values or alternative data sources

**Extra Fields:**
- Fields your API provides that the existing adapter doesn't use
- Not a problem - can be ignored or added as custom fields

### Quality Score Estimation

The tool estimates data quality based on:
- **Base adapter quality** (Zego: 100, CheckIn Group: 85, Go365: 80, Unique Inter: 60)
- **Compatibility score** (multiplier effect)
- **Formula:** `Estimated Quality = Base Quality × (Compatibility / 100)`

**Example:**
- Base: CheckIn Group (85/100)
- Compatibility: 100%
- Estimated: 85 × (100/100) = **85/100**

---

## Recommendation Scenarios

### Scenario A: Perfect Match (≥95%)

#### What It Means
Your API has the EXACT same field structure as an existing adapter. All fields match directly.

#### Example Output
```
✅ PERFECT MATCH (100%) with CheckIn Group adapter

Your API structure is identical to CheckIn Group. No new code needed!

Implementation Steps:
1. Create Provider in Django Admin
   Set adapter type to: checkingroup

2. Configure API credentials
   Add API token/key in Provider settings

3. Run sync command
   Execute: python manage.py sync_checkingroup
```

#### What to Do
1. **Create Provider in Django Admin:**
   - Navigate to `http://localhost:8000/admin/wholesale/provider/`
   - Click "Add Provider"
   - Fill in:
     - Name: Your provider's name
     - Code: Your provider code (lowercase)
     - **Adapter Type:** Select the recommended adapter from dropdown (e.g., "CheckIn Group")
     - API Token: Your provider's API key
     - Base URL: Your provider's API base URL
   - Click "Save"

2. **Run sync command:**
   ```bash
   docker-compose exec web python manage.py sync_checkingroup
   ```

3. **Done!** The existing adapter handles everything.

#### No Code Changes Needed ✓

---

### Scenario B: Reuse (80-94%)

#### What It Means
Strong compatibility with minor field name differences. Most fields match, some minor adjustments may be needed.

#### Example Output
```
✅ REUSE (85%) with Zego adapter

Most fields match directly. Minor adjustments may be needed.

Implementation Steps:
1. Create Provider in Django Admin
   Set adapter type to: zego

2. Review field mappings
   Check if any field names need adjustment

3. Run sync command
   Execute: python manage.py sync_zego
```

#### What to Do
1. **Create Provider** (same as Perfect Match)
2. **Review field mappings** in `wholesale/provider_mappings.py`
3. **Test sync with --dry-run:**
   ```bash
   docker-compose exec web python manage.py sync_zego --dry-run
   ```
4. **Adjust if needed** (usually minimal changes)
5. **Run full sync**

---

### Scenario C: Normalizer (50-79%)

#### What It Means
Field NAMES differ but structure is similar. Need to create a field normalizer to map your field names to the adapter's expected names.

#### Example Output
```
⚠️ REUSE WITH NORMALIZER (65%) with Zego adapter

Field names differ but structure is similar. Create a field normalizer to map your fields.

Field Mapping Reference:
| Zego Field  | Your Field | Status      |
|-------------|------------|-------------|
| ProductID   | tour_id    | ⚠ Map Needed |
| ProductName | tour_name  | ⚠ Map Needed |
| Days        | days       | ✓ Match     |
| Nights      | nights     | ✓ Match     |

Example Normalizer Code:
```python
class YourProviderNormalizer(FieldNormalizer):
    def normalize_tour(self, raw_data):
        """Normalize your API format to Zego format."""
        return {
            'ProductID': raw_data.get('tour_id'),
            'ProductName': raw_data.get('tour_name'),
            'Days': raw_data.get('days'),
            'Nights': raw_data.get('nights'),
            # ... add more field mappings
        }
```

Implementation Steps:
1. Create normalizer class
   Map your fields to Zego format

2. Register normalizer in mapper
   Update ZegoMapper to use your normalizer

3. Test and sync
   Run sync command: python manage.py sync_zego
```

#### What to Do

**1. Create normalizer file:**

Create `wholesale/field_normalizers.py` (if it doesn't exist) or add to existing:

```python
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime

class YourProviderNormalizer(FieldNormalizer):
    """Normalizes your provider's API format to Zego format."""

    @staticmethod
    def normalize_tour(raw_data: Dict) -> Dict:
        """Transform tour data to Zego format."""
        return {
            # Map your fields to Zego's expected fields
            'ProductID': raw_data.get('tour_id'),
            'ProductName': raw_data.get('tour_name'),
            'Days': raw_data.get('days'),
            'Nights': raw_data.get('nights'),
            'CountryCode': raw_data.get('country_code'),
            'CountryName': raw_data.get('country_name'),
            # Add all other field mappings based on the table
        }

    @staticmethod
    def normalize_period(raw_data: Dict) -> Dict:
        """Transform period data to Zego format."""
        return {
            'PeriodID': raw_data.get('period_id'),
            'PeriodStartDate': raw_data.get('start_date'),
            'PeriodEndDate': raw_data.get('end_date'),
            'Price': raw_data.get('adult_price'),
            # Add all period field mappings
        }
```

**2. Create custom API service:**

Even though you're reusing the adapter pattern, create a service that normalizes before passing to the Zego mapper:

```python
# wholesale/api_service.py

from .field_normalizers import YourProviderNormalizer

class YourProviderAPIService(ZegoAPIService):
    """API service for your provider using Zego adapter with normalization."""

    def get_program_tours(self) -> Optional[List[Dict]]:
        """Fetch and normalize tour data."""
        raw_data = super().get_program_tours()
        if raw_data:
            # Normalize each tour to Zego format
            return [YourProviderNormalizer.normalize_tour(tour) for tour in raw_data]
        return None
```

**3. Register in factory:**

Update `wholesale/api_service.py` factory:

```python
if provider.code == 'your_provider_code':
    return YourProviderAPIService(provider.base_url, provider.api_token)
```

**4. Test:**
```bash
docker-compose exec web python manage.py sync_zego --dry-run
```

---

### Scenario D: Create New (<50%)

#### What It Means
Data structure is significantly different from all existing adapters. You need to create a new adapter.

#### Example Output
```
🆕 CREATE NEW ADAPTER (22% match)

Your API structure is significantly different from existing adapters. New adapter required.

Key Differences:
- Zego: 8 extra fields, 18 missing fields
- Unique Inter: 7 extra fields, 2 missing fields
- CheckIn Group: 10 extra fields, 15 missing fields

Generated code below includes:
✓ API Service class
✓ Mapper class
✓ Management command
✓ Provider mappings config

Implementation Checklist:
[ ] Review generated code
[ ] Update API endpoints (TODO markers)
[ ] Test with sample data
[ ] Create Provider in admin
[ ] Run sync command
```

#### What to Do

**1. Download generated code:**

The tool generates 4 files:
- **API Service** (`yourprovider_service.py`)
- **Mapper** (`yourprovider_mapper.py`)
- **Management Command** (`sync_yourprovider.py`)
- **Provider Mappings** (configuration snippet)

**2. Review and customize:**

Each file has `TODO` markers showing what needs customization:

```python
# TODO: Verify endpoint
response = self._make_request('/tours')
```

**3. Update API endpoints:**

Replace placeholder endpoints with actual provider API endpoints:

```python
# Before
def get_program_tours(self) -> Optional[List[Dict]]:
    response = self._make_request('/tours')  # TODO: Verify endpoint

# After
def get_program_tours(self) -> Optional[List[Dict]]:
    response = self._make_request('/api/v1/tour-packages')
```

**4. Complete field mappings:**

In the generated mapper, complete all field mappings:

```python
# Generated code has placeholders
'TODO_tour_id': raw_data.get('id'),

# Update with correct model field names
'external_id': raw_data.get('id'),
'code': raw_data.get('code'),
'name': raw_data.get('name'),
```

**5. Add to provider_mappings.py:**

Copy the generated mappings config to `wholesale/provider_mappings.py`.

**6. Register in factory:**

Add your service to `APIServiceFactory.create_service()`.

**7. Test with dry-run:**

```bash
docker-compose exec web python manage.py sync_yourprovider --dry-run
```

**8. Full implementation guide:**

See [Adapter Guide](adapter-guide.md) for complete implementation details.

---

## Best Practices

### 1. Get Complete API Samples

**Do:**
- Use REAL API responses from the provider
- Include all available fields
- Get samples for all entity types (tours, periods, countries, etc.)

**Don't:**
- Use mock/fake data
- Manually create sample JSON
- Omit optional fields

### 2. Test All Entity Types

Upload samples for:
- ✅ Tours (required)
- ✅ Periods/Departures (if available)
- ✅ Countries (if available)
- ✅ Flights (if available)
- ✅ Itineraries (if available)

More complete data = better analysis.

### 3. Review Generated Code Carefully

**Always:**
- Read through all generated code
- Update TODO markers
- Verify API endpoints
- Test with --dry-run first

**Never:**
- Copy-paste without review
- Skip TODO markers
- Deploy without testing

### 4. Start with Dry-Run Mode

Test your implementation safely:

```bash
# Test without writing to database
docker-compose exec web python manage.py sync_yourprovider --dry-run

# Check what would be created
docker-compose exec web python manage.py sync_yourprovider --dry-run --limit 5
```

### 5. Use Smart Paste for Complex APIs

If your provider returns nested data structures, use Smart Paste instead of manual field splitting.

---

## Troubleshooting

### Common Issues

#### Issue: "Invalid JSON format"

**Error:**
```
❌ Invalid JSON format: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

**Causes:**
- Single quotes instead of double quotes
- Trailing commas
- Comments in JSON
- Unescaped special characters

**Solutions:**
```bash
# Validate JSON online
# https://jsonlint.com/

# Or use Python
python -c "import json; json.loads(open('sample.json').read())"

# Format JSON properly
cat response.json | python -m json.tool
```

#### Issue: "Tour sample data is required"

**Cause:** The tour field is empty or invalid JSON.

**Solution:**
- Tour sample is the only required field
- Must be a valid JSON array: `[{...}]`
- Use Smart Paste if you have complex nested data

#### Issue: Empty Field Errors

**Error:**
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause:** This has been fixed in the latest version. Empty optional fields now work correctly.

**Solution:** Update to latest code or leave optional fields empty.

#### Issue: "Provider not found in mappings"

**Cause:** Your generated adapter code hasn't been added to `provider_mappings.py`.

**Solution:**
1. Copy the generated "Provider Mappings Configuration" code
2. Add it to `wholesale/provider_mappings.py`
3. Restart Django

#### Issue: Analysis Shows 0% for All Adapters

**Cause:** Your field names are completely different from all existing adapters.

**Expected:** This is fine! The tool will recommend CREATE_NEW and generate code for you.

**Action:** Follow the "Create New Adapter" scenario instructions.

---

## Examples

### Example 1: CheckIn Group Perfect Match

**Scenario:** You have a provider with identical API structure to CheckIn Group.

**API Sample:**
```json
{
  "data": {
    "id": 1,
    "code": "BKK001",
    "name": "Bangkok 5D4N",
    "day": 5,
    "night": 4,
    "price": 25000,
    "startPeriod": "2024-12-01",
    "endPeriod": "2024-12-05"
  }
}
```

**Steps:**

1. **Create Session:**
   - Provider Name: "Amazing Tours Thailand"
   - Provider Code: "amazing_tours"
   - Base URL: "https://api.amazingtours.com/v1"

2. **Upload Sample:**
   - Paste entire JSON into Smart Paste Helper
   - Click "Auto-Fill Fields"
   - Tour, Period fields automatically filled

3. **Analyze:**
   - Result: **PERFECT MATCH (100%)** with CheckIn Group

4. **Implementation:**
   ```bash
   # Create provider in admin with adapter_type = "checkingroup"
   # Then run:
   docker-compose exec web python manage.py sync_checkingroup
   ```

5. **Done!** No code needed.

---

### Example 2: Creating Normalizer for Zego-Like API

**Scenario:** Provider has similar structure to Zego but different field names.

**API Sample:**
```json
[
  {
    "tour_id": "T001",
    "tour_name": "Bangkok Adventure",
    "duration_days": 5,
    "duration_nights": 4,
    "destination_country": "TH"
  }
]
```

**Zego expects:**
```json
[
  {
    "ProductID": "...",
    "ProductName": "...",
    "Days": 5,
    "Nights": 4,
    "CountryCode": "TH"
  }
]
```

**Steps:**

1. **Analyze:** Result shows **REUSE_WITH_NORMALIZER (75%)** with Zego

2. **Review Field Mapping Table:**
   | Zego Field | Your Field | Status |
   |------------|------------|--------|
   | ProductID | tour_id | ⚠ Map Needed |
   | ProductName | tour_name | ⚠ Map Needed |
   | Days | duration_days | ⚠ Map Needed |

3. **Create Normalizer:**
   ```python
   # wholesale/field_normalizers.py
   class AmazingToursNormalizer(FieldNormalizer):
       @staticmethod
       def normalize_tour(raw_data):
           return {
               'ProductID': raw_data.get('tour_id'),
               'ProductName': raw_data.get('tour_name'),
               'Days': raw_data.get('duration_days'),
               'Nights': raw_data.get('duration_nights'),
               'CountryCode': raw_data.get('destination_country'),
           }
   ```

4. **Create Service:**
   ```python
   # wholesale/api_service.py
   class AmazingToursAPIService(ZegoAPIService):
       def get_program_tours(self):
           raw_data = super().get_program_tours()
           if raw_data:
               return [AmazingToursNormalizer.normalize_tour(t) for t in raw_data]
           return None
   ```

5. **Test:**
   ```bash
   docker-compose exec web python manage.py sync_zego --dry-run
   ```

---

### Example 3: Creating New Adapter

**Scenario:** Provider has completely different structure (score <50%).

**Steps:**

1. **Analyze:** Result shows **CREATE_NEW (22%)**

2. **Download all 4 generated files**

3. **Review and update TODOs:**
   - API endpoints
   - Field mappings
   - Authentication method

4. **Add files to project:**
   ```
   wholesale/
   ├── api_service.py (add your service class)
   ├── provider_mappers.py (add your mapper)
   └── management/commands/
       └── sync_yourprovider.py
   ```

5. **Add to provider_mappings.py**

6. **Test:**
   ```bash
   docker-compose exec web python manage.py sync_yourprovider --dry-run --limit 5
   ```

7. **See [Adapter Guide](adapter-guide.md) for full implementation**

---

## FAQs

### Can I reuse adapters across different providers?

**Yes!** That's the whole point of the evaluation tool. If your provider's API structure is compatible with an existing adapter (≥50% match), you can reuse it.

**Perfect Match (≥95%):**
- Use the adapter directly, just configure provider in admin

**High Match (80-94%):**
- Use adapter with minor config tweaks

**Moderate Match (50-79%):**
- Create a field normalizer to map field names

### What if my provider has unique fields the existing adapter doesn't have?

**Not a problem!** Extra fields are fine:
- The adapter ignores fields it doesn't know about
- You can add custom fields to the mapper if needed
- Focus on the fields the adapter expects

**Example:** If Zego adapter expects 10 fields and your provider has 15, as long as your 15 includes those 10, you're good.

### How do I handle nested data?

**Use Smart Paste Helper:**
1. Paste the entire nested JSON response
2. Click "Auto-Fill Fields"
3. Tool automatically extracts and splits nested arrays

**Example:**
```json
{
  "data": {
    "tour": {...},
    "periods": [{...}],
    "countries": [{...}]
  }
}
```

Smart Paste extracts:
- Tour → tour field
- Periods → period field
- Countries → country field

### What if the tool recommends CREATE_NEW but I think I can reuse?

**Review the field mapping table carefully:**
- Check what fields are missing
- See if you can provide those fields through other means
- Consider if the missing fields are critical

**You can override the recommendation:**
- Lower score doesn't prevent reuse
- It just means more manual work
- Field normalizers can handle significant differences

**When in doubt:** Start with CREATE_NEW, it's safer.

### How accurate is the quality score estimation?

**It's an estimate based on:**
- Base adapter's known quality
- Field compatibility percentage
- Not a guarantee

**Use it as a guide:**
- 80-100: High confidence
- 60-79: Medium confidence
- <60: Lower confidence, more testing needed

### Can I edit/improve the generated code?

**Absolutely!** The generated code is a starting point:
- Review all TODO markers
- Add error handling
- Customize for provider's specific needs
- Add logging
- Improve efficiency

**Never use generated code as-is in production without review.**

---

## Related Documentation

- [Adapter Implementation Guide](adapter-guide.md) - Complete adapter development guide
- [Quick Start](quick-start.md) - Fast track for provider integration
- [CheckIn Group Guide](checkingroup-guide.md) - CheckIn Group specific details
- [Multi-Provider Architecture](multi-provider.md) - System design overview

---

## Need Help?

**Tool Issues:**
- Check [Troubleshooting](#troubleshooting) section
- Verify JSON formatting
- Check Django logs: `docker-compose logs -f web`

**Implementation Questions:**
- See [Adapter Guide](adapter-guide.md)
- Review existing adapter implementations (Zego, CheckIn Group)
- Check `wholesale/provider_mappers.py` for patterns

**Feature Requests:**
- Submit to development team
- Describe your use case
- Include example API responses
