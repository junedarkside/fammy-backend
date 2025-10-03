# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations and start development server
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Create new Django app
python manage.py startapp [appname]
```

### Docker Development
```bash
# Start local development with Docker
docker-compose -f docker-compose.yml up

# Create superuser in Docker environment
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py createsuperuser"

# View Docker logs
docker-compose -f docker-compose.yml logs

# Production mode (with RDS)
docker-compose -f docker-compose-rds.yml up
```

### Data Synchronization

#### Zego Data Sync
```bash
# Sync all data from active wholesalers
python manage.py sync_zego_data

# Sync specific wholesaler
python manage.py sync_zego_data --wholesaler "WholesalerName"

# Sync only countries or tours
python manage.py sync_zego_data --countries-only
python manage.py sync_zego_data --tours-only

# Check for updates before syncing
python manage.py sync_zego_data --check-updates
```

#### Unique Inter Wholesale Sync
```bash
# 1. First time setup: Discover and sync categories
python manage.py sync_unique_inter_categories

# 2. Full sync (fetch raw data + process into models)
python manage.py sync_unique_inter

# 3. Fetch only (store raw data without processing)
python manage.py sync_unique_inter --fetch-only

# 4. Process only (clean and map existing raw data)
python manage.py sync_unique_inter --process-only

# 5. Sync specific category only (e.g., category 64 = Vietnam)
python manage.py sync_unique_inter --category 64

# 6. Combine options (fetch only for specific category)
python manage.py sync_unique_inter --fetch-only --category 59
```

## Project Architecture

### Core Structure
- **Core/**: Django project configuration with settings, URLs, Celery setup
- **Accounts/**: Custom user authentication using email-based login
- **tours/**: Travel tour management with categories, types, locations, and flash sales
- **wholesale/**: Wholesale travel provider integration with external API synchronization
- **management/**: Custom Django management commands for data operations

### Database Configuration
The project uses conditional database settings:
- **Docker mode** (`DOCKER=true`): PostgreSQL with configurable credentials
- **Local development**: SQLite3 database
- Configuration managed through environment variables with `python-decouple`

### Key Models and Relationships

#### Tours App
- **Tour**: Main tour entity with operator, locations, categories, and travel dates
- **TravelDate**: Specific departure dates with pricing and availability
- **FlashSale**: Time-based discount system for travel dates
- **Location, Country, Airline, Operator**: Supporting entities for tour organization

#### Wholesale App
- **Provider**: External API providers (e.g., Zego, Unique Inter) with authentication tokens and configuration
- **ProviderCategory**: Dynamic category management for providers (e.g., destination regions)
- **RawVendorData**: Raw API response storage for data preservation and debugging
- **ProgramTour**: Synchronized tour programs from providers with detailed itineraries
- **Period**: Specific tour periods with pricing, availability, and booking status
- **Flight, Itinerary**: Detailed tour components including flight schedules and daily activities
- **Country, Location**: Geographical entities linked to providers

### Celery Configuration
- **Redis**: Used as message broker and result backend
- **Celery Beat**: Scheduled task management using django-celery-beat
- **Workers**: Background task processing for data synchronization
- Environment-aware Redis connection (Docker vs local)

### API Integration
- RESTful endpoints for tour management and wholesale data
- External API synchronization with wholesaler systems
- Custom management commands for bulk data operations
- Django REST Framework for API serialization

### Environment Configuration
Key environment variables:
- `DOCKER`: Boolean flag for deployment mode
- `DB_*`: Database connection parameters
- `SECRET_KEY`, `DEBUG`: Standard Django settings
- `CELERY_BROKER_URL`, `CACHE_LOCATION_URL`: Redis configuration
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`: Security settings

### Data Synchronization Pattern
The wholesale app implements a comprehensive data sync service that:
1. Fetches data from external provider APIs
2. Synchronizes countries, locations, and program tours
3. Maintains relationship integrity between entities
4. Provides status tracking and error handling
5. Supports incremental updates and full synchronization

#### Two-Stage Sync Pattern (Unique Inter)
For vendors with complex data formats, the system uses a two-stage approach:
1. **Fetch Stage**: Store raw API responses in `RawVendorData` model
2. **Process Stage**: Clean, validate, and map raw data to `ProgramTour` and `Period` models

Benefits:
- Preserves original API responses for debugging
- Allows reprocessing without re-fetching
- Enables data validation and error tracking
- Supports iterative data cleaning improvements

### Provider Configuration

#### Zego Provider Setup
```python
Provider.objects.create(
    name='Zego Travel',
    code='zego',
    base_url='https://zegoapi.com',
    token='your-api-token',
)
```

#### Unique Inter Provider Setup
```python
Provider.objects.create(
    name='Unique Inter Wholesale',
    code='unique_inter',
    base_url='https://uniqueinterwholesale.com',
    extra={'user_email': 'your-email@example.com'}
)
```

**Important**: After creating Unique Inter provider, run `python manage.py sync_unique_inter_categories` to discover and configure available categories.

### Category Management (Unique Inter)
Categories are managed via Django Admin or can be auto-discovered:

1. **Auto-discover**: `python manage.py sync_unique_inter_categories`
2. **Manage in Admin**: Navigate to `Wholesale > Provider Categories`
   - Enable/disable categories with `is_active` flag
   - Set sync priority (higher priority = syncs first)
   - View tour counts per category
   - Add custom categories manually

Known Categories:
- `59` - Europe Tours
- `60` - Russia Tours
- `61` - UK Tours
- `62` - Hong Kong Tours
- `63` - Special Promotion Europe
- `64` - Vietnam Tours

### Unique Inter Data Mapping

The Unique Inter API is **departure-centric** (not tour-centric). Each API record represents a specific departure date for a tour program.

#### API Response Structure
```json
{
  "mainid": "2680",           // Tour program ID
  "ProductCode": "58543",     // Departure ID
  "title": "Tour Name 8 Days",
  "Country": "Category Name", // NOT actual country - it's the category
  "Airline": "Emirates",
  "jpg": "image_url",
  "word": "path/to/doc",
  "pdf": "path/to/pdf",
  "Date": "2025-10-21",       // Departure date
  "ENDDate": "2025-10-28",    // Return date
  "Adult": "65900",
  "Single": "15000",
  "Booking": "16",            // Number booked
  "AVBL": "0",                // Available seats
  "com": "3000",              // Commission
  "Deposit": "30000"
}
```

#### Model Mapping

**ProgramTour** (Tour Programs):
| API Field | Model Field | Notes |
|-----------|-------------|-------|
| `mainid` | `external_id`, `code` | Unique tour program ID |
| `title` | `name`, `days`, `nights` | Duration extracted from title |
| `Airline` | `airline_name` | Airline name only (no code) |
| `jpg` | `image_url` | Tour image |
| `word` | `file_word` | Word document URL |
| `pdf` | `file_pdf` | PDF document URL |
| `story` | `highlight` | Tour highlights/period info |

**Period** (Departure Dates):
| API Field | Model Field | Notes |
|-----------|-------------|-------|
| `ProductCode` | `external_id` | Unique departure ID |
| `pid` | `code` | Period identifier |
| `Date` | `start_date` | Departure date |
| `ENDDate` | `end_date` | Return date |
| `Airline` | `airline_name` | Airline for this departure |
| `AVBL` | `seats` | Available seats |
| `Booking` | `booked` | Number of bookings |
| `Size` | `group_size` | Total group size |
| `Adult` | `base_prices['adult']` | Adult price |
| `Single` | `base_prices['single']` | Single supplement |
| `Deposit` | `deposit`, `deposit_end` | Deposit amount |
| `com` | `com_agent`, `com_agent_end` | Agent commission |
| `complus` | `com_sale`, `com_sale_end` | Sales commission |
| `Pro` | `promotion` | Promotion flag |

**NOT Mapped** (Data Not Available in API):
- ❌ **Country Model**: API `Country` field is category name, not actual country
- ❌ **Flight Model**: No flight schedules (airline name only)
- ❌ **Itinerary Model**: No day-by-day breakdown

**Important**: Flight schedules and detailed itineraries exist only in the PDF/Word documents, not in the API response.

## Data Quality Management

### Country Validation for Unique Inter

Due to inconsistent title formats in Unique Inter API data, some tours may have invalid country names extracted (e.g., "Christmas", "Winter", "AURORA" instead of actual countries).

#### Identifying Invalid Country Data

**Via Command Line:**
```bash
# Audit all tours with invalid country names
python manage.py audit_tour_countries

# Audit specific provider only
python manage.py audit_tour_countries --provider-code unique_inter
```

**Via Django Admin:**
1. Navigate to **Wholesale > Program Tours**
2. Use **Country Status** filter → Select "Needs Review (extracted but no FK)"
3. Tours with invalid country names will be shown with orange ⚠ indicator

#### Fixing Invalid Country Data

**Manual Fix (Recommended for small datasets):**
1. Open tour in Django Admin
2. Select correct Country from dropdown (or leave empty if unknown)
3. Save changes

**Automatic Fix (Re-sync after improving extraction):**
```bash
# Re-process existing raw data with improved extraction
python manage.py sync_unique_inter --process-only
```

**Visual Indicators in Admin:**
- ✓ Green: Valid country (has Country FK)
- ⚠ Orange: Needs review (extracted name but no valid Country FK)
- ✗ Red: Missing (no country data)

**Note**: Tours will function normally even without valid country data. The Country field is optional and used primarily for filtering and organization.

### Custom User Model
Uses `Accounts.Account` as the custom user model for email-based authentication instead of username-based login.