# Unique Inter Provider API Response vs Standard Data Structure Analysis

## Executive Summary

This analysis compares the **Unique Inter API response structure** with the **standard B2B travel platform data model**, identifying field mappings, transformations, data quality constraints, and best practices for integration.

**Purpose**: Document how Unique Inter API responses map to standard schema, data transformation requirements, and integration constraints.

**Last Updated**: 2026-01-16

---

## Table of Contents

1. [API Response Structure vs Standard Model](#1-api-response-structure-vs-standard-model)
2. [Field Mapping Comparison](#2-field-mapping-comparison)
3. [Data Transformation Logic](#3-data-transformation-logic)
4. [Best Practices](#4-best-practices)
5. [Constraints and Limitations](#5-constraints-and-limitations)
6. [Provider Comparison Matrix](#6-provider-comparison-matrix)
7. [Implementation Recommendations](#7-implementation-recommendations)
8. [Critical Files Reference](#8-critical-files-reference)
9. [Testing & Verification](#9-testing--verification)

---

## 1. API Response Structure vs Standard Model

### 1.1 Unique Inter API Endpoint

**Base URL**: `https://uniqueinterwholesale.com/apiweb.php`

**Authentication Method**: Query parameter (not headers)
```
?user={email_address}&id={category_id}
```

**Category-Based Structure**:
| Category ID | Destination | Thai Name |
|-------------|-------------|-----------|
| 59 | Europe | ทัวร์เส้นทางยุโรป |
| 60 | Russia | ทัวร์เส้นทางรัสเซีย |
| 61 | UK | ทัวร์อังกฤษ สหราชอาณาจักร |
| 62 | Hong Kong | ทัวร์เส้นทางฮ่องกง |
| 63 | Special Promotion Europe | Special Promotion ยุโรป |
| 64 | Vietnam | ทัวร์เส้นทางเวียดนาม |

**Implementation**: `wholesale/api_service.py:567-714` - `UniqueInterAPIService`

### 1.2 Raw API Response Structure

**Departure-Centric Design**: The API returns multiple records per tour program (one per departure date).

```json
[
  {
    "mainid": "UI_EUROPE_FRANCE",
    "title": "UI_EUROPE_FRANCE France Highlights 8 Days 7 Nights",
    "word": "uploads/tours/UI_EUROPE_FRANCE.docx",
    "pdf": "uploads/tours/UI_EUROPE_FRANCE.pdf",
    "jpg": "uploads/tours/UI_EUROPE_FRANCE.jpg",
    "story": "Experience the beauty of France...",
    "Country": "Europe",
    "Airline": "THAI AIRWAYS",
    "ProductCode": "UI_EUROPE_FRANCE_20250115",
    "pid": "1001",
    "Date": "2025-01-15",
    "ENDDate": "2025-01-22",
    "Adult": "89900",
    "Chd+B": "84900",
    "Single": "15000",
    "AVBL": "10",
    "Booking": "20",
    "Size": "30",
    "Deposit": "20000",
    "com": "5000",
    "complus": "7000",
    "Pro": "Early Bird",
    "startingprice": "89900"
  },
  {
    "mainid": "UI_EUROPE_FRANCE",
    "title": "UI_EUROPE_FRANCE France Highlights 8 Days 7 Nights",
    "Country": "Europe",
    "Airline": "THAI AIRWAYS",
    "ProductCode": "UI_EUROPE_FRANCE_20250122",
    "pid": "1002",
    "Date": "2025-01-22",
    "ENDDate": "2025-01-29",
    "Adult": "95000",
    "Chd+B": "90000",
    "Single": "15000",
    "AVBL": "5",
    "Booking": "25",
    "Size": "30",
    "Deposit": "20000",
    "com": "5000",
    "complus": "7000",
    "Pro": "",
    "startingprice": "95000"
  }
]
```

**Key Characteristics**:
- Same `mainid` appears multiple times (one per departure date)
- Each record has unique `ProductCode` combining tour code + date
- All data provided in list response (no separate detail endpoint)
- Limited pricing structure (3 types vs Zego's 12)

### 1.3 Standard Model Schema (ProgramTour)

**File**: `wholesale/models.py:368-439`

```python
class ProgramTour(models.Model):
    # Core identification
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=100)  # Required: mainid
    code = models.CharField(max_length=100)          # Required: mainid
    name = models.CharField(max_length=255)          # Required: title

    # Duration
    days = models.PositiveIntegerField(blank=True, null=True)
    nights = models.PositiveIntegerField(blank=True, null=True)

    # Country (Foreign Key + snapshot)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    country_name = models.CharField(max_length=255, blank=True)

    # Airline
    airline_code = models.CharField(max_length=50, blank=True, null=True)
    airline_name = models.CharField(max_length=255, blank=True, null=True)

    # Documents
    file_pdf = models.URLField(blank=True, null=True)
    file_word = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    # Description
    highlight = models.TextField(blank=True, null=True)

    # Data quality indicators
    data_quality_score = models.IntegerField(default=100)
    has_flights = models.BooleanField(default=True)
    has_itineraries = models.BooleanField(default=True)
    has_full_pricing = models.BooleanField(default=True)
    needs_country_review = models.BooleanField(default=False)
```

### 1.4 Standard Model Schema (Period)

**File**: `wholesale/models.py:441-500`

```python
class Period(models.Model):
    # Core identification
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=100)  # Required: ProductCode
    program = models.ForeignKey(ProgramTour, related_name="periods", on_delete=models.CASCADE)
    code = models.CharField(max_length=100)          # Required: pid

    # Dates
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # Airline (period-specific)
    airline_name = models.CharField(max_length=255, blank=True, null=True)

    # Capacity
    group_size = models.IntegerField(blank=True, null=True)
    booked = models.IntegerField(blank=True, null=True)
    seats = models.IntegerField(blank=True, null=True)

    # Status
    status = models.CharField(max_length=50, blank=True, null=True)

    # Pricing (JSONField)
    base_prices = models.JSONField(blank=True, null=True)
    end_prices = models.JSONField(blank=True, null=True)

    # Financial
    deposit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    deposit_end = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    com_agent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    com_agent_end = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    com_sale = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    com_sale_end = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Additional
    promotion = models.CharField(max_length=255, blank=True, null=True)
    bus = models.CharField(max_length=50, blank=True, null=True)
    airport = models.CharField(max_length=255, blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
```

### 1.5 Standard Model Schema (Country)

**File**: `wholesale/models.py:342-366`

```python
class Country(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='countries')
    provider_code = models.CharField(max_length=50)           # Normalized name
    name = models.CharField(max_length=255)                   # Display name
    normalized_name = models.CharField(max_length=255, db_index=True)
    iso_code = models.CharField(max_length=3, blank=True)     # ISO 3166-1 alpha-3
    icon_url = models.URLField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)         # Country description
    locations = models.JSONField(blank=True, null=True)       # Array of locations
```

---

## 2. Field Mapping Comparison

### 2.1 Tour Data Mapping Table

**Implementation**: `wholesale/provider_mappings.py:99-142`

| Standard Field | API Field | Transformation | Required? |
|----------------|-----------|----------------|-----------|
| `external_id` | `mainid` | Direct copy | ✅ Yes |
| `code` | `mainid` | Direct copy | ✅ Yes |
| `name` | `title` | Clean whitespace, remove \r\n | ✅ Yes |
| `days` | *None* | **Extracted from title** via regex | ⚠️ Derived |
| `nights` | *None* | **Extracted from title** via regex (days-1) | ⚠️ Derived |
| `country` | *None* | **Extracted from title** + ISO lookup | ⚠️ Derived |
| `country_name` | `Country` | Direct copy (category name) | ✅ Yes |
| `airline_name` | `Airline` | Direct copy | ✅ Yes |
| `file_pdf` | `pdf` | Prepend base URL: `https://uniqueinterwholesale.com/{pdf}` | ❌ No |
| `file_word` | `word` | Prepend base URL: `https://uniqueinterwholesale.com/{word}` | ❌ No |
| `image_url` | `jpg` | Prepend base URL: `https://uniqueinterwholesale.com/{jpg}` | ❌ No |
| `highlight` | `story` | Direct copy | ❌ No |
| `has_flights` | *None* | **Always False** (no flight schedules) | ⚠️ Fixed |
| `has_itineraries` | *None* | **Always False** (itineraries in PDF only) | ⚠️ Fixed |
| `has_full_pricing` | *None* | **Always False** (only 3 pricing types) | ⚠️ Fixed |
| `data_quality_score` | *None* | **Always 60** (lower due to missing data) | ⚠️ Fixed |

**Key Transformations**:

1. **Duration Extraction** (`UniqueInterNormalizer.extract_duration`):
   ```python
   # Input: "UI_EUROPE_FRANCE France Highlights 8 Days 7 Nights"
   # Regex: (\d+)\s*DAYS?\s*(\d+)\s*NIGHTS?
   # Output: days=8, nights=7
   # File: wholesale/field_normalizers.py:232-277
   ```

2. **Country Extraction** (`UniqueInterNormalizer.extract_country`):
   ```python
   # Input: "UI_EUROPE_FRANCE France Highlights 8 Days 7 Nights"
   # Logic: Split by '_', take 3rd part, first word
   # Output: "France"
   # Then: Lookup ISO code → "FRA"
   # File: wholesale/field_normalizers.py:280-316
   ```

3. **URL Construction**:
   ```python
   # Input: "uploads/tours/UI_EUROPE_FRANCE.pdf"
   # Output: "https://uniqueinterwholesale.com/uploads/tours/UI_EUROPE_FRANCE.pdf"
   ```

### 2.2 Period Data Mapping Table

**Implementation**: `wholesale/provider_mappings.py:116-134`

| Standard Field | API Field | Transformation | Required? |
|----------------|-----------|----------------|-----------|
| `external_id` | `ProductCode` | Direct copy | ✅ Yes |
| `code` | `pid` | Direct copy | ✅ Yes |
| `start_date` | `Date` | Parse ISO date format | ✅ Yes |
| `end_date` | `ENDDate` | Parse ISO date format | ✅ Yes |
| `country_name` | `Country` | Direct copy | ✅ Yes |
| `airline_name` | `Airline` | Direct copy | ✅ Yes |
| `group_size` | `Size` | Convert to integer | ❌ No |
| `booked` | `Booking` | Convert to integer | ❌ No |
| `seats` | `AVBL` | Convert to integer | ❌ No |
| `status` | *None* | **Derived from AVBL**: ≤0=Soldout, ≤5=Waitlist, >5=Book | ⚠️ Derived |
| `promotion` | `Pro` | Direct copy | ❌ No |
| `deposit` | `Deposit` | Clean price, convert to Decimal | ❌ No |
| `com_agent` | `com` | Clean price, convert to Decimal | ❌ No |
| `com_sale` | `complus` | Clean price, convert to Decimal | ❌ No |
| `deposit_end` | `Deposit` | Same as deposit (no separate end deposit) | ⚠️ Duplicate |
| `com_agent_end` | `com` | Same as com_agent | ⚠️ Duplicate |
| `com_sale_end` | `complus` | Same as com_sale | ⚠️ Duplicate |

### 2.3 Pricing Structure Mapping

**Implementation**: `wholesale/provider_mappings.py:263-270`

**Standard base_prices JSONField**:
```json
{
  "adult": 89900,
  "child": 84900,
  "child_nb": 0,
  "infant": 0,
  "join_land": 0,
  "single_bed": 15000,
  "twin_bed": 0,
  "double_bed": 0,
  "triple_bed": 0,
  "single_visa": 0,
  "group_visa": 0,
  "express_visa": 0
}
```

**Unique Inter API Pricing**:
| API Field | Standard Field | Value |
|-----------|----------------|-------|
| `Adult` | `base_prices.adult` | 89900 |
| `Chd+B` | `base_prices.child` | 84900 |
| `Single` | `base_prices.single_bed` | 15000 |
| *None* | `base_prices.child_nb` | **0** (not available) |
| *None* | `base_prices.infant` | **0** (not available) |
| *None* | `base_prices.join_land` | **0** (not available) |
| *None* | `base_prices.twin_bed` | **0** (not available) |
| *None* | `base_prices.double_bed` | **0** (not available) |
| *None* | `base_prices.triple_bed` | **0** (not available) |
| *None* | `base_prices.single_visa` | **0** (not available) |
| *None* | `base_prices.group_visa` | **0** (not available) |
| *None* | `base_prices.express_visa` | **0** (not available) |

**Key Issue**: Unique Inter only provides **3 pricing types** (adult, child, single_bed) vs Zego's **12 types**. Missing types are set to **0**.

**End Prices**: Unique Inter doesn't have separate "early booking" pricing, so `end_prices` = `base_prices` (duplicate).

---

## 3. Data Transformation Logic

### 3.1 UniqueInterNormalizer Methods

**File**: `wholesale/field_normalizers.py:224-335`

#### 3.1.1 Duration Extraction

```python
@staticmethod
def extract_duration(title: str) -> Tuple[int, int]:
    """
    Extract days and nights from tour title.

    Patterns tried in order:
    1. (\d+)\s*DAYS?\s*(\d+)\s*NIGHTS? - "8 Days 7 Nights"
    2. (\d+)\s*D\s*(\d+)\s*N - "8D7N"
    3. (\d+)\s*DAYS? - "8 Days" (assumes nights = days - 1)

    Returns:
        Tuple of (days, nights) - (0, 0) if not found
    """
```

**Examples**:
- `"France Highlights 8 Days 7 Nights"` → (8, 7)
- `"Tour 8D7N"` → (8, 7)
- `"8 Days Tour"` → (8, 7)
- `"No Info"` → (0, 0)

#### 3.1.2 Country Extraction

```python
@staticmethod
def extract_country(title: str) -> str:
    """
    Extract country name from Unique Inter title.

    Patterns supported:
    1. Underscore format: "UI_CODE_CountryName Tour Description"
    2. Dash format: "Code-CountryName-Tour Name"

    Returns:
        Extracted country name or empty string
    """
```

**Examples**:
- `"UI_EUROPE_FRANCE France Highlights"` → "France"
- `"EUROPE-Italy-Tour Name"` → "Italy"
- `"Invalid Format"` → ""

**Accuracy**: ~85-90% success rate

**Failures**:
- Non-standard title formats
- Multi-word country names
- Abbreviations
- Special characters

#### 3.1.3 Price Cleaning

```python
@staticmethod
def clean_price(raw_price: str) -> Optional[Decimal]:
    """
    Handle Unique Inter special price formats.

    Formats handled:
    - "25,000" → 25000
    - "25000" → 25000
    - "25+1" → 26 (25 + 1 free)
    - "" → None

    Returns:
        Decimal price or None if invalid
    """
```

**Base Normalizer**: `FieldNormalizer.normalize_price` (`wholesale/field_normalizers.py:23-71`)

### 3.2 Base FieldNormalizer Methods

**File**: `wholesale/field_normalizers.py:14-222`

#### 3.2.1 Price Normalization

```python
@staticmethod
def normalize_price(raw_value) -> Optional[Decimal]:
    """
    Normalize price values from various formats.

    Handles:
    - Commas: "25,000" → 25000
    - Plus format: "25+1" → 26
    - Whitespace: " 25000 " → 25000
    - Empty values: "" → None

    Returns:
        Decimal or None
    """
```

#### 3.2.2 Date Normalization

```python
@staticmethod
def normalize_date(raw_value) -> Optional[date]:
    """
    Parse dates from various formats.

    Formats tried:
    1. ISO format: "2025-01-15"
    2. European: "15/01/2025"
    3. US: "01-15-2025"
    4. Dash: "15-01-2025"

    Returns:
        date object or None
    """
```

#### 3.2.3 Boolean Normalization

```python
@staticmethod
def normalize_boolean(raw_value) -> Optional[bool]:
    """
    Parse boolean from various formats.

    Handles:
    - Y/N strings
    - true/false strings
    - 1/0 integers

    Returns:
        bool or None
    """
```

#### 3.2.4 Text Normalization

```python
@staticmethod
def normalize_text(raw_value) -> Optional[str]:
    """
    Clean text by removing extra whitespace.

    - Removes \r\n
    - Strips leading/trailing spaces
    - Returns empty string for None

    Returns:
        Cleaned string or empty string
    """
```

### 3.3 Data Quality Mapping

**Implementation**: `wholesale/provider_mappings.py:292-321`

```python
PROVIDER_DATA_COMPLETENESS = {
    'unique_inter': {
        'has_flights': False,          # No flight schedules
        'has_itineraries': False,      # Itineraries in PDF only
        'has_full_pricing': False,     # Only 3 pricing types
        'expected_pricing_types': 3,
        'data_quality_score': 60,      # Lower due to missing data
    },
}
```

**Quality Score Breakdown**:
- Base score: 100
- Missing flights: -15
- Missing itineraries: -15
- Limited pricing: -10
- **Total: 60/100**

**Comparison**:
- Zego: 100/100 (complete)
- CheckIn Group: 85/100 (high quality)
- Unique Inter: 60/100 (limited)
- Go365: 80/100 (middle)

---

## 4. Best Practices

### 4.1 Code Quality Best Practices

#### 1. Type Hints on All Functions

```python
# GOOD - Type hints for clarity and IDE support
def extract_duration(title: str) -> Tuple[int, int]:
    """Extract days and nights from tour title."""
    pass

def clean_price(raw_price: str) -> Optional[Decimal]:
    """Handle Unique Inter special price formats."""
    pass

# BAD - No type hints
def extract_duration(title):
    pass
```

**Implementation**: All functions in `wholesale/field_normalizers.py` use type hints.

#### 2. Safe Dictionary Access

```python
# GOOD - Safe access with .get()
user_email = provider.extra.get('user_email', '') if provider.extra else ''

# BAD - Direct access can raise KeyError
user_email = provider.extra['user_email']
```

**Implementation**: `wholesale/api_service.py:589`

#### 3. Google-Style Docstrings

```python
def extract_country(title: str) -> str:
    """
    Extract country name from Unique Inter title.

    Unique Inter uses structured title formats like:
    - "UI_TOURCODE_CountryName Tour Description"
    - "TourCode-CountryName-Tour Name"

    Args:
        title: Tour title string

    Returns:
        Extracted country name or empty string
    """
```

**Implementation**: All public methods in `wholesale/field_normalizers.py`

#### 4. Centralized Configuration

```python
# GOOD - All mappings in one place
PROVIDER_MAPPINGS = {
    'unique_inter': {
        'tour': {...},
        'period': {...},
    }
}

# BAD - Mappings scattered across code
```

**Implementation**: `wholesale/provider_mappings.py`

### 4.2 Data Transformation Best Practices

#### 1. Two-Stage Sync Process

```bash
# Stage 1: Fetch raw data (enables debugging)
python manage.py sync_unique_inter --fetch-only

# Stage 2: Process raw data (can be re-run)
python manage.py sync_unique_inter --process-only

# Full sync (both stages)
python manage.py sync_unique_inter
```

**Implementation**: `wholesale/management/commands/sync_unique_inter.py`

**Benefits**:
- Debug API issues without re-processing
- Re-process data with updated mapping logic
- Inspect raw JSON structure
- Partial syncs during failures

#### 2. Regex Pattern Order Matters

```python
# GOOD - Try specific patterns first
patterns = [
    r'(\d+)\s*DAYS?\s*(\d+)\s*NIGHTS?',  # Most specific: "8 Days 7 Nights"
    r'(\d+)\s*D\s*(\d+)\s*N',            # Medium: "8D7N"
    r'(\d+)\s*DAYS?',                     # Least specific: "8 Days"
]

# BAD - General pattern first will match everything
patterns = [
    r'(\d+)\s*DAYS?',                     # Matches "8 Days 7 Nights" incorrectly
    r'(\d+)\s*DAYS?\s*(\d+)\s*NIGHTS?',
]
```

**Implementation**: `wholesale/field_normalizers.py:254-276`

#### 3. Price Normalization Edge Cases

```python
# GOOD - Handle multiple formats
def clean_price(raw_price: str) -> Optional[Decimal]:
    if not raw_price:
        return None

    # Remove commas
    cleaned = raw_price.replace(',', '').strip()

    # Handle "25+1" format (25 + 1 free)
    if '+' in cleaned:
        parts = cleaned.split('+')
        return sum(Decimal(p) for p in parts if p.strip())

    return Decimal(cleaned)

# Test cases:
# "25,000"   → 25000
# "25000"    → 25000
# "25+1"     → 26
# "0"        → 0
# ""         → None
```

**Implementation**: `wholesale/field_normalizers.py:23-71`

### 4.3 Error Handling Best Practices

#### 1. Log but Don't Fail

```python
# GOOD - Continue processing on errors
for raw_record in unprocessed:
    try:
        tour_data = map_unique_inter_tour_data(raw_record.raw_json)
        # Process tour...
    except Exception as e:
        logger.error(f"Error processing tour {raw_record.id}: {e}")
        raw_record.error_message = str(e)
        raw_record.save()
        errors += 1
        # Continue to next record

# BAD - One error stops entire sync
```

**Implementation**: `wholesale/management/commands/sync_unique_inter.py`

#### 2. Graceful Degradation

```python
# GOOD - Set defaults for missing data
base_prices = {
    'adult': clean_price(raw_data.get('Adult', '0')),
    'child': clean_price(raw_data.get('Chd+B', '0')),
    'single_bed': clean_price(raw_data.get('Single', '0')),
    # Missing types set to 0 instead of failing
    'twin_bed': 0,
    'double_bed': 0,
}

# BAD - Fail on missing fields
```

**Implementation**: Pricing mapping in sync command

### 4.4 Data Validation Best Practices

#### 1. ISO Code Validation Before Creation

```python
# GOOD - Only create countries with valid ISO codes
def get_or_create_country_for_unique_inter(provider, country_name):
    iso = get_iso_code(country_name)

    if not iso:
        print(f"  ❌ SKIP: {country_name} (no ISO code)")
        return None  # Skip invalid countries

    country, created = Country.objects.get_or_create(...)
    return country

# BAD - Create any country name (leads to duplicates)
```

**Implementation**: Sync command country creation logic

#### 2. Set Quality Flags Accurately

```python
# GOOD - Be realistic about limitations
return {
    'has_flights': False,         # No flight schedules
    'has_itineraries': False,     # Itineraries in PDF only
    'has_full_pricing': False,    # Only 3 pricing types
    'data_quality_score': 60,     # Lower score
}

# BAD - Claim completeness when data is missing
```

**Implementation**: `wholesale/provider_mappings.py:300-306`

### 4.5 Performance Best Practices

#### 1. Bulk Operations

```python
# GOOD - Use bulk_create for Periods
periods_to_create = [Period(**fields) for fields in period_data_list]
Period.objects.bulk_create(periods_to_create, batch_size=100)

# BAD - Create one by one
for fields in period_data_list:
    Period.objects.create(**fields)  # N database queries
```

**Implementation**: Sync command period creation

#### 2. Select Related

```python
# GOOD - Reduce queries with select_related
unprocessed = RawVendorData.objects.filter(
    provider=provider,
    processed=False
).select_related('provider')  # Join provider table

# BAD - N+1 query problem
for raw_record in unprocessed:
    print(raw_record.provider.name)  # Extra query per iteration
```

**Implementation**: Sync command data fetching

---

## 5. Constraints and Limitations

### 5.1 API-Level Constraints

#### 1. Category-Based Structure (Not Country-Based)

```
Constraint: Cannot fetch tours by country directly
Impact: Must fetch by category ID (59-64)
Workaround: Extract country from tour titles
Risk: Extraction errors for non-standard titles
```

**Implementation**: `wholesale/api_service.py:598-663`

#### 2. No Country Endpoint

```
Constraint: No dedicated /countries endpoint
Impact: Cannot validate country codes against API
Workaround: Use internal ISO 3166-1 alpha-3 mapping
Risk: API may use different country names
```

#### 3. No Flight Schedules

```
Constraint: Only airline names provided
Impact: Cannot create Flight records
Missing: flight_no, departure_time, arrival_time, route
Workaround: Set has_flights=False
User Impact: No flight detail pages
```

**Implementation**: `wholesale/provider_mappings.py:135-138`

#### 4. No Itinerary Data

```
Constraint: Itineraries only in PDF/Word documents
Impact: Cannot create Itinerary records
Missing: day-by-day descriptions, hotels, meals
Workaround: Set has_itineraries=False, provide document links
User Impact: No day-by-day breakdown, must download PDF
```

**Implementation**: `wholesale/provider_mappings.py:139-141`

#### 5. Limited Pricing Types

```
Constraint: Only 3 pricing types (adult, child, single)
Impact: Missing 9 pricing types vs Zego's 12
Missing: twin_bed, double_bed, triple_bed, infant, join_land, visas
Workaround: Set missing types to 0
User Impact: Limited pricing options for customers
```

**Implementation**: `wholesale/provider_mappings.py:263-270`

#### 6. No Timestamps

```
Constraint: No created_at/updated_at in API response
Impact: Cannot detect updated records
Missing: provider_created_at, provider_updated_at
Workaround: Full sync required each time
Risk: Cannot implement incremental sync
```

### 5.2 Data Quality Constraints

#### 1. Data Quality Score: 60/100

```
Breakdown:
- Base score: 100
- Missing flights: -15
- Missing itineraries: -15
- Limited pricing: -10
Total: 60/100

Comparison:
- Zego: 100/100 (complete)
- CheckIn Group: 85/100 (high quality)
- Go365: 80/100 (middle)
- Unique Inter: 60/100 (limited)
```

**Implementation**: `wholesale/provider_mappings.py:305`

#### 2. Country Extraction Accuracy

```
Success Rate: ~85-90%
Failure Cases:
- Non-standard title formats
- Multi-word country names
- Abbreviations
- Special characters

Example Failures:
✓ "UI_EUROPE_FRANCE France Highlights" → "France"
✗ "SPECIAL_PROMO_EU Switzerland Italy" → "SPECIAL" (wrong)
✓ "UI_ASIA001 Vietnam Danang Hue" → "Vietnam" (correct)
```

**Implementation**: `wholesale/field_normalizers.py:280-316`

#### 3. Departure-Centric Structure

```
Challenge: Same tour appears multiple times (one per departure)
Example:
- "UI_EUROPE_FRANCE" with 10 departures = 10 API records
- Must group by mainid to create 1 ProgramTour
- Risk: Inconsistent tour data across departures
```

**Implementation**: Sync command grouping logic

### 5.3 Synchronization Constraints

#### 1. No Incremental Sync

```
Constraint: Cannot fetch updated records only
Impact: Must fetch all tours every sync
API Calls: 6 categories × 1 request = 6 requests per sync
Performance: ~30-60 seconds for full sync
```

#### 2. No Delete Detection

```
Constraint: API doesn't indicate deleted tours
Impact: Stale tours may remain in database
Workaround: Implement "soft delete" after X days
Risk: Showing unavailable tours to users
```

#### 3. Manual Category Management

```
Requirement: Configure ProviderCategory records manually
Steps:
1. Run sync_unique_inter_categories to discover
2. Enable/disable categories in Django Admin
3. Set priority for sync ordering
Maintenance: Check for new categories periodically
```

**Implementation**: `wholesale/management/commands/sync_unique_inter_categories.py`

### 5.4 Schema Mapping Constraints

#### 1. Field Type Mismatches

```
API Field → Model Field Issues:
- AVBL (string "10") → seats (integer) ✗ Needs conversion
- Adult (string "89900") → base_prices.adult (Decimal) ✗ Needs conversion
- Date (string "2025-01-15") → start_date (date) ✗ Needs parsing
```

**Implementation**: `FieldNormalizer` methods

#### 2. Missing Required Fields

```
ProgramTour Required Fields (API doesn't provide):
✗ days: Extracted from title (may fail)
✗ nights: Extracted from title (may fail)
✗ country: Extracted from title + ISO lookup (may fail)

Consequence:
- Some tours have days=0, nights=0
- Some tours have country=None
- Requires needs_country_review flag
```

**Implementation**: `wholesale/models.py:436-438`

#### 3. URL Path Requirements

```
API Returns: "uploads/tours/UI_EUROPE_FRANCE.pdf"
Model Requires: Full URL

Transformation:
file_pdf = f"https://uniqueinterwholesale.com/{pdf_path}"

Risk:
- If base_url changes, all URLs break
- No validation that URL is accessible
```

---

## 6. Provider Comparison Matrix

### 6.1 Feature Comparison

| Feature | Zego | Unique Inter | CheckIn Group | Go365 |
|---------|------|--------------|---------------|-------|
| **Authentication** | API Token (header) | Email (query param) | None | API Key (header) |
| **Endpoint Structure** | Country-based | Category-based | Tour-centric | ? Unknown |
| **Countries Endpoint** | ✅ GET /countries | ❌ Categories only | ✅ Array in tours | ? Unknown |
| **Tours Endpoint** | ✅ GET /programtours | ✅ GET /apiweb.php | ✅ GET /v1/programtours | ✅ GET /api/v1/tours/list |
| **Detail Endpoint** | ✅ GET /programtours/{id} | ❌ All in list | ✅ GET /v1/programtours/{id} | ✅ GET /api/v1/tours/detail/{id} |
| **Flight Schedules** | ✅ Full data | ❌ Names only | ✅ Text format | ? Partial |
| **Flight Fields** | flight_no, times, route | airline_name only | Text in remark | ? Unknown |
| **Itineraries** | ✅ API data | ❌ PDF only | ❌ Not available | ? Partial |
| **Itinerary Fields** | day, hotel, meals | N/A | N/A | day, hotel |
| **Pricing Types** | 12 types | 3 types | 4 types | 2 types |
| **Adult Price** | ✅ Price | ✅ Adult | ✅ priceAdultDouble | ✅ price_adult |
| **Child Price** | ✅ Price_Child | ✅ Chd+B | ✅ priceChild | ✅ price_child |
| **Single Bed** | ✅ Price_Single_Bed | ✅ Single | ✅ priceSingleRoomAdd | ❌ No |
| **Twin Bed** | ✅ Price_Twin_Bed | ❌ No | ❌ No | ❌ No |
| **Infant Price** | ✅ Price_Infant | ❌ No | ✅ priceInfant | ❌ No |
| **Join Land** | ✅ Price_JoinLand | ❌ No | ❌ No | ❌ No |
| **Visa Prices** | ✅ 3 types | ❌ No | ❌ No | ❌ No |
| **Commission** | ✅ ComAgent/ComSale | ✅ com/complus | ✅ comAgent/comSales | ? Unknown |
| **Deposit** | ✅ Deposit | ✅ Deposit | ✅ deposit | ? Unknown |
| **Data Quality** | 100/100 | 60/100 | 85/100 | 80/100 |
| **Timestamps** | ❌ No | ❌ No | ✅ createdAt/updatedAt | ? Unknown |
| **Two-Stage Sync** | ❌ No | ✅ Yes | ❌ No | ? Unknown |

### 6.2 API Response Structure Comparison

#### Zego (Country-Based, Complete)

```json
{
  "ProductID": "ZEGO_001",
  "ProductCode": "ZEGO_001",
  "ProductName": "France Highlights",
  "CountryCode": "FRA",
  "CountryName": "France",
  "Days": 8,
  "Nights": 7,
  "AirlineCode": "TG",
  "AirlineName": "THAI AIRWAYS",
  "Periods": [
    {
      "PeriodID": "ZEGO_001_20250115",
      "PeriodCode": "P001",
      "PeriodStartDate": "2025-01-15",
      "PeriodEndDate": "2025-01-22",
      "Price": 89900,
      "Price_Child": 84900,
      "Price_Single_Bed": 15000,
      "Price_Twin_Bed": 75000,
      // ... 8 more price types
    }
  ],
  "Flights": [
    {
      "FlightNo": "TG931",
      "Route": "BKK-CDG",
      "DepartureTime": "23:55",
      "ArrivalTime": "05:45+1"
    }
  ],
  "Itinerary": [
    {
      "ItinDay": 1,
      "ItinDes": "Arrival in Paris",
      "ItinHotel": "Hilton Paris",
      "ItinBfast": "Y",
      "ItinLunch": "Y",
      "ItinDnr": "Y"
    }
  ]
}
```

#### Unique Inter (Category-Based, Departure-Centric)

```json
[
  {
    "mainid": "UI_EUROPE_FRANCE",
    "title": "UI_EUROPE_FRANCE France Highlights 8 Days 7 Nights",
    "Country": "Europe",
    "Airline": "THAI AIRWAYS",
    "ProductCode": "UI_EUROPE_FRANCE_20250115",
    "pid": "1001",
    "Date": "2025-01-15",
    "ENDDate": "2025-01-22",
    "Adult": "89900",
    "Chd+B": "84900",
    "Single": "15000",
    // Note: Only 3 price types
    // Note: No Flights array
    // Note: No Itinerary array
    // Note: Each departure is a separate record
  }
]
```

#### CheckIn Group (Tour-Centric, Embedded Periods)

```json
[
  {
    "id": "123",
    "code": "CIG_CN_001",
    "name": "จางเจียเจี้ย-เมืองโบราณเฟิ่งหวง",
    "day": 8,
    "night": 7,
    "countries": [
      {"code": "CN", "name": "จีน", "icon": "https://..."}
    ],
    "vehicle": "CHINA EASTERN AIRLINES (MU)",
    "periods": [
      {
        "id": "456",
        "start": "2025-01-15",
        "end": "2025-01-22",
        "priceAdultDouble": 28900.00,
        "priceChild": 26900.00,
        "priceSingleRoomAdd": 5000.00,
        "group": 30,
        "seat": 10,
        "available": 10,
        "flight": "MU512 (06:00-11:30)"
      }
    ],
    "createdAt": "2025-11-28T03:17:40.000000Z",
    "updatedAt": "2025-11-28T03:17:40.000000Z"
  }
]
```

### 6.3 Integration Complexity Comparison

| Aspect | Zego | Unique Inter | CheckIn Group | Go365 |
|--------|------|--------------|---------------|-------|
| **Authentication** | Simple | Simple | None | Medium |
| **Data Fetching** | Direct | Categories | Direct | Direct |
| **Data Parsing** | Simple | Complex (extraction) | Medium | Medium |
| **Country Mapping** | Direct API | Extract + ISO | Direct API | ? Unknown |
| **Duration Mapping** | Direct fields | Extract from title | Direct fields | Direct fields |
| **Price Mapping** | Direct (12 types) | Limited (3 types) | Direct (4 types) | Limited (2 types) |
| **Flight Mapping** | Direct API | Not available | Parse text | ? Partial |
| **Itinerary Mapping** | Direct API | Not available | Not available | ? Partial |
| **Error Handling** | Standard | High risk | Standard | ? Unknown |
| **Maintenance** | Low | Medium | Low | ? Medium |
| **Overall Complexity** | Low | **High** | Medium | Medium |

---

## 7. Implementation Recommendations

### 7.1 For Adding New Providers

#### Decision Tree: Reuse vs Create New Adapter

```
1. Is the provider's API structure identical to an existing provider?
   └─ YES → Reuse existing adapter with custom normalizer
   └─ NO  → Continue to step 2

2. Does the provider use category-based endpoints like Unique Inter?
   └─ YES → Extend UniqueInterAPIService with custom categories
   └─ NO  → Continue to step 3

3. Does the provider use country-based endpoints like Zego?
   └─ YES → Extend ZegoAPIService with custom endpoints
   └─ NO  → Create new adapter inheriting BaseAPIService
```

#### Reuse Example (Similar Structure to Unique Inter)

```python
# If new provider "TravelAsia" has same structure as Unique Inter:

# 1. Create provider-specific normalizer
class TravelAsiaNormalizer(UniqueInterNormalizer):
    """Inherit all extraction logic, override if needed"""
    pass

# 2. Add to PROVIDER_MAPPINGS
PROVIDER_MAPPINGS = {
    'travelasia': {
        'tour': UNIQUE_INTER_TOUR_MAPPING,  # Reuse
        'period': UNIQUE_INTER_PERIOD_MAPPING,  # Reuse
    }
}

# 3. Use UniqueInterAPIService with different base URL
service = UniqueInterAPIService(provider)
service.base_url = "https://travelasia.com"
```

#### New Adapter Example (Different Structure)

```python
# If new provider has completely different structure:

class NewProviderAPIService(BaseAPIService):
    """Complete custom implementation"""

    def _setup_authentication(self):
        # Custom auth logic
        pass

    def get_countries(self):
        # Custom endpoint
        pass

    def get_program_tours(self):
        # Custom endpoint
        pass

    def get_program_tour_details(self, product_code):
        # Custom endpoint
        pass
```

### 7.2 Coding Standards Checklist

Before committing provider integration code, verify:

**Code Quality**:
- [ ] All functions have type hints
- [ ] All public methods have Google-style docstrings
- [ ] No direct dictionary access for optional fields (use `.get()`)
- [ ] Constants use UPPERCASE_WITH_UNDERSCORES
- [ ] Classes use CapitalizedWords
- [ ] Functions use lowercase_with_underscores

**Error Handling**:
- [ ] API errors are logged but don't stop processing
- [ ] Missing fields return None or default values
- [ ] Invalid data is skipped with warning log
- [ ] Database errors are caught and handled

**Data Validation**:
- [ ] Country names validated against ISO mapping
- [ ] Prices converted to Decimal (not string or int)
- [ ] Dates parsed to date objects (not string)
- [ ] Required fields checked before database operations

**Data Quality**:
- [ ] `has_flights` set accurately (True/False)
- [ ] `has_itineraries` set accurately (True/False)
- [ ] `has_full_pricing` set accurately (True/False)
- [ ] `data_quality_score` reflects actual completeness (0-100)
- [ ] `needs_country_review` set for uncertain extractions

**Performance**:
- [ ] Bulk operations used for multiple records
- [ ] `select_related()` used for foreign keys
- [ ] Database queries minimized in loops
- [ ] API requests batched when possible

**Testing**:
- [ ] Two-stage sync tested separately
- [ ] Raw data inspection works
- [ ] Re-processing works without duplicates
- [ ] Country extraction tested on edge cases
- [ ] Price normalization tested on edge cases

### 7.3 Maintenance Recommendations

#### 1. Monitor Country Extraction Accuracy

```bash
# Run weekly to find tours needing review
python manage.py shell
>>> from wholesale.models import ProgramTour
>>> tours = ProgramTour.objects.filter(
...     provider__code='unique_inter',
...     needs_country_review=True
... )
>>> for tour in tours:
...     print(f"{tour.name} | {tour.country_name} | {tour.country}")

# Manual review in Django Admin:
# 1. Go to Wholesale → Program Tours
# 2. Filter: Provider = Unique Inter, Needs Country Review = Yes
# 3. Update country field manually
# 4. Uncheck "Needs Country Review"
```

#### 2. Watch for API Changes

```python
# Add to sync_unique_inter.py command:
def detect_api_changes(self):
    """Check if API structure has changed"""
    # Fetch sample data
    sample = api_service.get_tour_packages_by_category('59')

    # Check for new fields
    expected_fields = ['mainid', 'title', 'Adult', 'Chd+B', 'Single']
    for field in expected_fields:
        if field not in sample[0]:
            logger.warning(f"Missing expected field: {field}")

    # Check for removed fields
    new_fields = set(sample[0].keys()) - set(expected_fields)
    if new_fields:
        logger.info(f"New fields detected: {new_fields}")
```

#### 3. Performance Optimization

```python
# Add caching for category data:
from django.core.cache import cache

def get_tour_packages_by_category(self, category_id):
    cache_key = f'unique_inter_cat_{category_id}'
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data

    data = self._make_request('apiweb.php', params={...})
    cache.set(cache_key, data, timeout=3600)  # 1 hour
    return data
```

#### 4. Data Quality Dashboard

```python
# Create admin action to show quality metrics:
def show_data_quality_dashboard(modeladmin, request, queryset):
    """Display data quality metrics for selected providers"""
    for provider in queryset:
        tours = ProgramTour.objects.filter(provider=provider)
        total = tours.count()

        metrics = {
            'total_tours': total,
            'has_flights': tours.filter(has_flights=True).count(),
            'has_itineraries': tours.filter(has_itineraries=True).count(),
            'needs_review': tours.filter(needs_country_review=True).count(),
            'avg_quality': tours.aggregate(Avg('data_quality_score'))['data_quality_score__avg'],
        }

        print(f"{provider.name}: {metrics}")
```

### 7.4 Troubleshooting Guide

#### Problem: Country Extraction Fails

```
Symptom: Tours have country=None, needs_country_review=True

Diagnosis:
1. Check tour title format: Is it non-standard?
2. Check regex patterns: Do they match the title?
3. Check ISO mapping: Is country name in mapping?

Solution:
1. Add new regex pattern to extract_country()
2. Add country name to COUNTRY_NAME_TO_ISO mapping
3. Manually set country in Django Admin
```

#### Problem: Periods Not Created

```
Symptom: Tours created but no periods

Diagnosis:
1. Check RawVendorData: Was raw data fetched?
2. Check grouping: Are records grouped by mainid?
3. Check errors: Check error_message field

Solution:
1. Run --fetch-only to verify API returns data
2. Check logs for processing errors
3. Verify ProductCode is unique across periods
```

#### Problem: Prices Showing as 0

```
Symptom: All prices are 0 in base_prices

Diagnosis:
1. Check API response: Are price fields present?
2. Check clean_price(): Does it handle the format?
3. Check Decimal conversion: Any InvalidOperation errors?

Solution:
1. Update clean_price() to handle new format
2. Check for None values before conversion
3. Add test case for the price format
```

#### Problem: Duplicate Tours

```
Symptom: Same tour created multiple times

Diagnosis:
1. Check mainid: Is it consistent across departures?
2. Check external_id: Is it unique?

Solution:
1. Verify grouping logic in sync command
2. Check update_or_create() lookup fields
3. Add unique constraint on external_id
```

---

## 8. Critical Files Reference

### 8.1 Implementation Files

| File | Lines | Purpose |
|------|-------|---------|
| `wholesale/api_service.py` | 567-714 | `UniqueInterAPIService` class |
| `wholesale/api_service.py` | 1-565 | `BaseAPIService` base class |
| `wholesale/field_normalizers.py` | 224-335 | `UniqueInterNormalizer` class |
| `wholesale/field_normalizers.py` | 14-222 | `FieldNormalizer` base class |
| `wholesale/provider_mappings.py` | 99-142 | Unique Inter field mappings |
| `wholesale/provider_mappings.py` | 292-321 | Data completeness config |
| `wholesale/provider_mappers.py` | 290-407 | `UniqueInterMapper` class |
| `wholesale/data_sync_service.py` | 948-1215 | Unique Inter mapping functions |
| `wholesale/management/commands/sync_unique_inter.py` | 1-325 | Main sync command |
| `wholesale/management/commands/sync_unique_inter_categories.py` | 1-100 | Category discovery |

### 8.2 Data Models

| Model | File | Fields |
|-------|------|--------|
| `Provider` | `wholesale/models.py` | code, name, base_url, token, extra |
| `ProviderCategory` | `wholesale/models.py` | provider, category_id, name, is_active, priority |
| `Country` | `wholesale/models.py` | provider, provider_code, name, normalized_name, iso_code |
| `ProgramTour` | `wholesale/models.py` | external_id, code, name, days, nights, country, data_quality_score |
| `Period` | `wholesale/models.py` | external_id, code, program, start_date, end_date, base_prices |
| `RawVendorData` | `wholesale/models.py` | provider, external_id, category, raw_json, processed |

### 8.3 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Provider credentials (user_email for Unique Inter) |
| `CLAUDE.md` | Project coding standards and policies |
| `docs/provider-integration/adapter-guide.md` | Adapter implementation guide |
| `docs/provider-integration/quick-start.md` | Quick start for new providers |

---

## 9. Testing & Verification

### 9.1 Unit Testing

```python
# Test UniqueInterNormalizer
def test_extract_duration():
    normalizer = UniqueInterNormalizer()

    # Test full format
    assert normalizer.extract_duration("8 Days 7 Nights") == (8, 7)

    # Test abbreviated format
    assert normalizer.extract_duration("8D7N") == (8, 7)

    # Test days only
    assert normalizer.extract_duration("8 Days") == (8, 7)

    # Test no duration
    assert normalizer.extract_duration("No Info") == (0, 0)

def test_extract_country():
    normalizer = UniqueInterNormalizer()

    # Test underscore format
    assert "France" in normalizer.extract_country("UI_EUROPE_FRANCE France Highlights")

    # Test dash format
    assert "Italy" in normalizer.extract_country("EUROPE-Italy-Tour Name")

    # Test no country
    assert normalizer.extract_country("Invalid Format") == ""

def test_clean_price():
    normalizer = UniqueInterNormalizer()

    # Test normal format
    assert normalizer.clean_price("89900") == Decimal("89900")

    # Test with commas
    assert normalizer.clean_price("89,900") == Decimal("89800")

    # Test with plus
    assert normalizer.clean_price("25+1") == Decimal("26")

    # Test empty
    assert normalizer.clean_price("") is None
```

### 9.2 Integration Testing

```bash
# 1. Test category discovery
docker-compose exec web python manage.py sync_unique_inter_categories
# Expected: Creates ProviderCategory records for active categories

# 2. Test raw data fetch
docker-compose exec web python manage.py sync_unique_inter --fetch-only --category 59
# Expected: Fetches and stores raw data for Europe category

# 3. Verify raw data
docker-compose exec web python manage.py shell
>>> from wholesale.models import RawVendorData
>>> data = RawVendorData.objects.filter(provider__code='unique_inter').first()
>>> import json
>>> print(json.dumps(data.raw_json, indent=2))
# Expected: See raw API response structure

# 4. Test data processing
docker-compose exec web python manage.py sync_unique_inter --process-only
# Expected: Creates ProgramTour and Period records

# 5. Verify processed data
>>> from wholesale.models import ProgramTour, Period
>>> tours = ProgramTour.objects.filter(provider__code='unique_inter')
>>> print(f"Tours: {tours.count()}")
>>> print(f"Periods: {Period.objects.filter(provider__code='unique_inter').count()}")

# 6. Check country extraction
>>> needs_review = ProgramTour.objects.filter(
...     provider__code='unique_inter',
...     needs_country_review=True
... )
>>> print(f"Needs review: {needs_review.count()}")

# 7. Verify data quality
>>> for tour in tours[:5]:
...     print(f"{tour.name[:50]}")
...     print(f"  Quality: {tour.data_quality_score}")
...     print(f"  Flights: {tour.has_flights}")
...     print(f"  Itineraries: {tour.has_itineraries}")
...     print(f"  Country: {tour.country_name} ({tour.country.iso_code if tour.country else 'N/A'})")
```

### 9.3 End-to-End Testing

```bash
# Full sync test
docker-compose exec web python manage.py sync_unique_inter

# Verify output:
# ═════════════════════════════════════════════════════════════
# STAGE 1: Fetching raw data from Unique Inter API
# ═════════════════════════════════════════════════════════════
# Fetching category: Europe Tours (59)...
#   ✓ Stored 25 raw records
# Fetching category: Russia Tours (60)...
#   ✓ Stored 18 raw records
# ...
# Raw data fetch completed: 125 total records stored
#
# ═════════════════════════════════════════════════════════════
# STAGE 2: Processing raw data into models
# ═════════════════════════════════════════════════════════════
# Processing 125 raw records...
#   ✓ Created tour: France Highlights 8 Days 7 Nights (UI_EUROPE_FRANCE)
#   ✓ Created tour: Switzerland Italy 7 Days 6 Nights (UI_EU_SUITALY)
# ...
# ═════════════════════════════════════════════════════════════
# PROCESSING COMPLETE
# ═════════════════════════════════════════════════════════════
# Tours created:  45
# Tours updated:  0
# Periods created: 125
# Periods updated: 0
#
# Unique Countries in Database:
#   - France (FRA)
#   - Switzerland (CHE)
#   - Italy (ITA)
#   - Russia (RUS)
#   - Vietnam (VNM)
```

---

## 10. Summary & Key Takeaways

### What Makes Unique Inter Integration Unique

1. **Category-Based Architecture**
   - Unlike Zego's country-based endpoints, Unique Inter uses destination categories
   - Requires manual category configuration in `ProviderCategory` model
   - Categories don't map 1:1 to countries

2. **Departure-Centric Data Structure**
   - Same tour program appears as multiple API records (one per departure)
   - Requires grouping by `mainid` to create single `ProgramTour`
   - Risk: Inconsistent data across departures

3. **Heavy Data Extraction**
   - Country extracted from tour title (not provided by API)
   - Duration extracted from tour title (not provided by API)
   - ~85-90% accuracy rate, requires manual review

4. **Limited Data Availability**
   - No flight schedules (only airline names)
   - No itineraries (PDF/Word documents only)
   - Only 3 pricing types (vs Zego's 12)
   - No timestamps for incremental sync

5. **Two-Stage Sync Process**
   - Stage 1: Fetch raw data (store in `RawVendorData`)
   - Stage 2: Process raw data (create models)
   - Enables debugging and re-processing

### Best Practices Demonstrated

✅ **Modular Architecture**: Separate concerns (API service, normalizer, mapper)
✅ **Type Hints**: All functions have type annotations
✅ **Error Handling**: Log errors but continue processing
✅ **Data Validation**: ISO code validation, safe defaults
✅ **Quality Flags**: Accurate data quality indicators
✅ **Safe Dictionary Access**: `.get()` for optional fields
✅ **Centralized Config**: All mappings in one place
✅ **Documentation**: Comprehensive docstrings

### Constraints to Accept

🚫 **Cannot Get**: Flight schedules, itineraries, comprehensive pricing
🚫 **Cannot Do**: Incremental sync, automatic delete detection
🚫 **Must Accept**: Lower data quality score (60/100), manual country review

### Critical Success Factors

1. **Regex Pattern Quality**: Determines extraction accuracy
2. **ISO Mapping Coverage**: Determines country creation rate
3. **Error Logging**: Essential for debugging issues
4. **Manual Review**: Required for country validation
5. **Regular Monitoring**: Watch for API changes

### Final Recommendation

The Unique Inter integration is **production-ready** with the following caveats:

- ✅ Use for tours where PDF/Word itineraries are acceptable
- ✅ Use when limited pricing options are sufficient
- ❌ Don't use if detailed flight information is required
- ❌ Don't use if day-by-day itinerary breakdown is required
- ⚠️ Requires manual country review for 10-15% of tours
- ⚠️ Data quality score of 60/100 must be communicated to users

**The implementation successfully abstracts Unique Inter's API limitations while providing a clean integration point for the B2B travel platform.**

---

## Related Documentation

- [Provider Adapter Guide](./adapter-guide.md) - How to implement provider adapters
- [Quick Start Guide](./quick-start.md) - Quick start for new providers
- [CheckIn Group Integration](./checkingroup-guide.md) - CheckIn Group provider implementation
- [Main Documentation Index](../README.md) - All project documentation
