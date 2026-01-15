# TravelApp Backend API Documentation (Actual Implementation)

> **Last Updated**: 2026-01-15
> **API Version**: Unversioned (uses `/api/` base path)
> **Status**: Production

---

## Overview

This document describes the **ACTUAL IMPLEMENTED API** for the TravelApp B2B travel platform backend. For the planned/aspirational API design, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md).

### Quick Facts

| Property | Value |
|----------|-------|
| **Base URL** | `http://localhost:8000/api/` (Docker) |
| **API Versioning** | None (no `/v1/` prefix) |
| **Authentication** | None (all endpoints are public) |
| **Rate Limiting** | Not implemented |
| **Format** | JSON |
| **Framework** | Django REST Framework |

### Important Notes

⚠️ **Security Warning**: This API currently has **NO AUTHENTICATION**. All endpoints are publicly accessible.

⚠️ **Documentation Mismatch**: The [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) file describes a planned API with authentication, versioning, and additional features that are NOT yet implemented. Use this document for the actual working API.

---

## Base URL Structure

```
Development: http://localhost:8000/api/
Production:  [Not configured yet]
```

### URL Pattern

All API endpoints use the `/api/` prefix with NO version number:

```
✅ CORRECT:  http://localhost:8000/api/tours/
❌ WRONG:    http://localhost:8000/api/v1/tours/
```

---

## Authentication

### Current Status: NONE

All endpoints are currently **PUBLIC** with no authentication required.

### Planned (Not Implemented)

- JWT Bearer token authentication
- API key authentication
- Role-based permissions
- Rate limiting per client

### What This Means

- Anyone can access any endpoint
- No user identification
- No access control
- Suitable for development/prototype only
- **NOT production-ready for security**

---

## API Endpoints

### Summary

| Endpoint | Methods | Auth | Description |
|----------|---------|------|-------------|
| `/api/healthcheck/` | GET | None | System health check |
| `/api/tours/` | GET, POST, PUT, PATCH, DELETE | None | Tour CRUD operations |
| `/api/wholesale/call-external-api/{company}/` | GET | None | External API proxy |
| `/api/wholesale/providers/` | GET, POST, PUT, PATCH, DELETE | None | Provider management |
| `/api/wholesale/providers/{name}/sync-countries/` | POST | None | Trigger country sync |
| `/api/wholesale/providers/{name}/sync-program-tours/` | POST | None | Trigger tour sync |
| `/api/wholesale/program-tours/` | GET | None | Program tours (read-only) |

---

## 1. Health Check

### GET /api/healthcheck/

Simple health check endpoint to verify the API is running.

**Authentication**: None (public)

**Request**:
```bash
curl http://localhost:8000/api/healthcheck/
```

**Response** (200 OK):
```json
{
  "status": "ok"
}
```

**Implementation**: `Core/urls.py`, `Core/views.py` (HealthCheckViewSet)

---

## 2. Tours API

The Tours API provides full CRUD operations for managing travel tours.

### Base URL: /api/tours/

**Implementation Files**:
- Views: `tours/views.py` (TourViewSet)
- URLs: `tours/urls.py`
- Serializer: `tours/serializers.py` (TourSerializer)
- Model: `tours/models.py` (Tour)

**Lookup Field**: `slug` (not `id`)

**Pagination**: Custom with enhanced metadata

---

### 2.1 List Tours

### GET /api/tours/

Retrieve a paginated list of all tours.

**Authentication**: None (public)

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 10 | Items per page (max: 100) |

**Request**:
```bash
# Default (10 items per page)
curl http://localhost:8000/api/tours/

# Custom page size
curl http://localhost:8000/api/tours/?page_size=20

# Second page with 25 items per page
curl http://localhost:8000/api/tours/?page=2&page_size=25
```

**Response** (200 OK):
```json
{
  "count": 150,
  "total": 15,
  "page_size": 10,
  "current": 1,
  "previous": null,
  "next": "http://localhost:8000/api/tours/?page=2",
  "results": [
    {
      "id": 1,
      "name": "European Highlights 8 Days",
      "slug": "european-highlights-8-days",
      "description": "Experience the best of Europe...",
      "duration": "8 Days",
      "highlight": "Free city tours included",
      "hotel_stars": "5",
      "price": "1299.00",
      "image": "https://example.com/image.jpg",
      "category": "INTERNATIONAL",
      "tour_type": "PACKAGE_TOUR",
      "created_at": "2025-10-14T10:00:00Z",
      "updated_at": "2025-10-14T10:00:00Z",
      "operator": {
        "id": 1,
        "name": "Premium Tours Ltd",
        "code": "PREMIUM"
      },
      "airline": {
        "id": 1,
        "name": "Emirates",
        "code": "EK"
      },
      "countries": [
        {
          "id": 1,
          "name": "France",
          "code": "FR"
        },
        {
          "id": 2,
          "name": "Italy",
          "code": "IT"
        }
      ],
      "locations": [
        {
          "id": 1,
          "name": "Paris",
          "country": {
            "id": 1,
            "name": "France",
            "code": "FR"
          }
        }
      ],
      "travel_dates": [
        {
          "id": 1,
          "date_start": "2025-12-15",
          "date_end": "2025-12-22",
          "rate": "1299.00",
          "date_range": 8,
          "available_seats": 15
        }
      ]
    }
  ]
}
```

**Pagination Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Total number of items |
| `total` | integer | Total number of pages |
| `page_size` | integer | Items per page |
| `current` | integer | Current page number |
| `previous` | string/null | URL to previous page |
| `next` | string/null | URL to next page |
| `results` | array | Array of tour objects |

---

### 2.2 Get Tour by Slug

### GET /api/tours/{slug}/

Retrieve a single tour by its slug.

**Authentication**: None (public)

**URL Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `slug` | string | Yes | Unique tour slug |

**Request**:
```bash
curl http://localhost:8000/api/tours/european-highlights-8-days/
```

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "European Highlights 8 Days",
  "slug": "european-highlights-8-days",
  "description": "Experience the best of Europe...",
  "duration": "8 Days",
  "highlight": "Free city tours included",
  "hotel_stars": "5",
  "price": "1299.00",
  "image": "https://example.com/image.jpg",
  "category": "INTERNATIONAL",
  "tour_type": "PACKAGE_TOUR",
  "created_at": "2025-10-14T10:00:00Z",
  "updated_at": "2025-10-14T10:00:00Z",
  "operator": {
    "id": 1,
    "name": "Premium Tours Ltd",
    "code": "PREMIUM"
  },
  "airline": {
    "id": 1,
    "name": "Emirates",
    "code": "EK"
  },
  "countries": [
    {
      "id": 1,
      "name": "France",
      "code": "FR"
    }
  ],
  "locations": [
    {
      "id": 1,
      "name": "Paris",
      "country": {
        "id": 1,
        "name": "France",
        "code": "FR"
      }
    }
  ],
  "travel_dates": [
    {
      "id": 1,
      "date_start": "2025-12-15",
      "date_end": "2025-12-22",
      "rate": "1299.00",
      "date_range": 8,
      "available_seats": 15
    }
  ]
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Not found."
}
```

---

### 2.3 Create Tour

### POST /api/tours/

Create a new tour.

**Authentication**: None (public)

**Request**:
```bash
curl -X POST http://localhost:8000/api/tours/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Asian Adventure 10 Days",
    "slug": "asian-adventure-10-days",
    "description": "Discover the wonders of Asia...",
    "duration": "10 Days",
    "highlight": "Cultural immersion included",
    "hotel_stars": "4",
    "price": "1899.00",
    "category": "INTERNATIONAL",
    "tour_type": "PACKAGE_TOUR"
  }'
```

**Response** (201 Created):
```json
{
  "id": 2,
  "name": "Asian Adventure 10 Days",
  "slug": "asian-adventure-10-days",
  "description": "Discover the wonders of Asia...",
  "duration": "10 Days",
  "highlight": "Cultural immersion included",
  "hotel_stars": "4",
  "price": "1899.00",
  "image": null,
  "category": "INTERNATIONAL",
  "tour_type": "PACKAGE_TOUR",
  "created_at": "2025-10-14T11:00:00Z",
  "updated_at": "2025-10-14T11:00:00Z",
  "operator": null,
  "airline": null,
  "countries": [],
  "locations": [],
  "travel_dates": []
}
```

**Response** (400 Bad Request):
```json
{
  "slug": [
    "tour with this slug already exists."
  ]
}
```

---

### 2.4 Update Tour (Full)

### PUT /api/tours/{slug}/

Update a tour (full replacement).

**Authentication**: None (public)

**Request**:
```bash
curl -X PUT http://localhost:8000/api/tours/european-highlights-8-days/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "European Highlights 8 Days (Updated)",
    "slug": "european-highlights-8-days",
    "description": "Updated description...",
    "duration": "8 Days",
    "price": "1399.00",
    "category": "INTERNATIONAL",
    "tour_type": "PACKAGE_TOUR"
  }'
```

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "European Highlights 8 Days (Updated)",
  "slug": "european-highlights-8-days",
  "description": "Updated description...",
  "duration": "8 Days",
  "price": "1399.00",
  "category": "INTERNATIONAL",
  "tour_type": "PACKAGE_TOUR",
  ...
}
```

---

### 2.5 Update Tour (Partial)

### PATCH /api/tours/{slug}/

Update specific fields of a tour.

**Authentication**: None (public)

**Request**:
```bash
curl -X PATCH http://localhost:8000/api/tours/european-highlights-8-days/ \
  -H "Content-Type: application/json" \
  -d '{
    "price": "1499.00"
  }'
```

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "European Highlights 8 Days",
  "slug": "european-highlights-8-days",
  "price": "1499.00",
  ...
}
```

---

### 2.6 Delete Tour

### DELETE /api/tours/{slug}/

Delete a tour.

**Authentication**: None (public)

**Request**:
```bash
curl -X DELETE http://localhost:8000/api/tours/european-highlights-8-days/
```

**Response** (204 No Content):
```
(no content)
```

---

## 3. Wholesale API

The Wholesale API manages external provider integration and synchronized tour data.

### Implementation Files
- Views: `wholesale/views.py`
- URLs: `wholesale/urls.py`
- Serializers: `wholesale/serializers.py`
- Models: `wholesale/models.py`

---

## 3.1 External API Proxy

### GET /api/wholesale/call-external-api/{company_name}/

Proxy endpoint to call external provider APIs directly.

**Authentication**: None (public)

**URL Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_name` | string | Yes | Provider name (case-insensitive) |

**How it works**:
1. Fetches provider from database by name
2. Constructs external API URL
3. Adds provider's auth token to headers
4. Returns raw JSON response from external API

**Implementation**: `wholesale/views.py` (ExternalApiCallViewSet)

**Request**:
```bash
curl http://localhost:8000/api/wholesale/call-external-api/zego/
```

**Response** (200 OK):
```json
{
  "countries": [
    {
      "id": 1,
      "name": "France",
      "code": "FR"
    }
  ],
  "total": 50
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Not found."
}
```

**Response** (500 Internal Server Error):
```json
{
  "error": "API endpoint URL not configured for provider 'zego'."
}
```

**Response** (503 Service Unavailable):
```json
{
  "error": "Error connecting to external API for 'Zego': Connection refused"
}
```

---

## 3.2 Provider Management

### Base URL: /api/wholesale/providers/

CRUD operations for wholesale providers.

**Implementation**: `wholesale/views.py` (ProviderSyncViewSet)

**Lookup Field**: `name` (case-insensitive)

---

### 3.2.1 List Providers

### GET /api/wholesale/providers/

Retrieve all providers.

**Authentication**: None (public)

**Request**:
```bash
curl http://localhost:8000/api/wholesale/providers/
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "Zego Travel",
    "code": "zego",
    "base_url": "https://www.zegoapi.com",
    "token": "********",
    "is_active": true,
    "extra": {},
    "created_at": "2025-10-14T10:00:00Z",
    "updated_at": "2025-10-14T10:00:00Z"
  },
  {
    "id": 2,
    "name": "Unique Inter Wholesale",
    "code": "unique_inter",
    "base_url": "https://uniqueinterwholesale.com",
    "token": "********",
    "is_active": true,
    "extra": {
      "user_email": "admin@example.com"
    },
    "created_at": "2025-10-14T10:00:00Z",
    "updated_at": "2025-10-14T10:00:00Z"
  }
]
```

---

### 3.2.2 Get Provider

### GET /api/wholesale/providers/{name}/

Retrieve a single provider by name.

**Authentication**: None (public)

**Request**:
```bash
curl http://localhost:8000/api/wholesale/providers/zego/
```

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "Zego Travel",
  "code": "zego",
  "base_url": "https://www.zegoapi.com",
  "token": "your-api-token-here",
  "is_active": true,
  "extra": {},
  "created_at": "2025-10-14T10:00:00Z",
  "updated_at": "2025-10-14T10:00:00Z"
}
```

---

### 3.2.3 Create Provider

### POST /api/wholesale/providers/

Create a new provider.

**Authentication**: None (public)

**Request**:
```bash
curl -X POST http://localhost:8000/api/wholesale/providers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Provider",
    "code": "new_provider",
    "base_url": "https://newprovider.com",
    "token": "your-token-here",
    "is_active": true
  }'
```

**Response** (201 Created):
```json
{
  "id": 3,
  "name": "New Provider",
  "code": "new_provider",
  "base_url": "https://newprovider.com",
  "token": "your-token-here",
  "is_active": true,
  "extra": {},
  "created_at": "2025-10-14T12:00:00Z",
  "updated_at": "2025-10-14T12:00:00Z"
}
```

---

### 3.2.4 Sync Countries

### POST /api/wholesale/providers/{name}/sync-countries/

Trigger synchronization of countries for a provider.

**Authentication**: None (public)

**Implementation**: `wholesale/views.py:135-170` (sync_countries_for_provider)

**Request**:
```bash
curl -X POST http://localhost:8000/api/wholesale/providers/zego/sync-countries/
```

**Response** (200 OK):
```json
{
  "message": "Countries synchronized successfully",
  "created": 10,
  "updated": 5,
  "errors": 0
}
```

**Response** (502 Bad Gateway):
```json
{
  "message": "Failed to fetch countries from external API",
  "created": 0,
  "updated": 0,
  "errors": 1
}
```

**Response** (500 Internal Server Error):
```json
{
  "error": "An unexpected server error occurred during the sync process.",
  "details": "Exception details..."
}
```

---

### 3.2.5 Sync Program Tours

### POST /api/wholesale/providers/{name}/sync-program-tours/

Trigger synchronization of program tours for a provider.

**Authentication**: None (public)

**Implementation**: `wholesale/views.py:172-207` (sync_program_tours_for_provider)

**Request**:
```bash
curl -X POST http://localhost:8000/api/wholesale/providers/zego/sync-program-tours/
```

**Response** (200 OK):
```json
{
  "message": "Program tours synchronized successfully",
  "created": 50,
  "updated": 20,
  "errors": 0
}
```

**Response** (502 Bad Gateway):
```json
{
  "message": "API request to fetch program tours failed",
  "created": 0,
  "updated": 0,
  "errors": 1
}
```

---

## 3.3 Program Tours

### Base URL: /api/wholesale/program-tours/

Read-only access to synchronized program tours from wholesale providers.

**Implementation**: `wholesale/views.py:277-302` (ProgramTourViewSet)
**Serializer**: `wholesale/serializers.py:37-48` (ProgramTourSerializer)
**Lookup Field**: `code`

**Features**:
- Optimized queries with `select_related` and `prefetch_related`
- Nested serialization for periods, flights, and itineraries
- Filter by provider name

---

### 3.3.1 List Program Tours

### GET /api/wholesale/program-tours/

Retrieve all synchronized program tours.

**Authentication**: None (public)

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | string | No | Filter by provider name (case-insensitive) |

**Request**:
```bash
# All program tours
curl http://localhost:8000/api/wholesale/program-tours/

# Filter by provider
curl http://localhost:8000/api/wholesale/program-tours/?provider=Zego
```

**Response** (200 OK):
```json
{
  "count": 1200,
  "next": "http://localhost:8000/api/wholesale/program-tours/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "code": "2680",
      "external_id": "2680",
      "name": "European Highlights 8 Days",
      "provider": {
        "name": "Zego Travel",
        "code": "zego"
      },
      "country": {
        "name": "France",
        "provider_code": "FR"
      },
      "duration_days": 8,
      "duration_nights": 7,
      "airline_name": "Emirates",
      "image_url": "https://example.com/tour.jpg",
      "file_pdf": "https://example.com/itinerary.pdf",
      "file_word": "https://example.com/itinerary.doc",
      "highlight": "Free city tours included",
      "data_quality_score": 85,
      "created_at": "2025-10-14T08:00:00Z",
      "updated_at": "2025-10-14T08:00:00Z",
      "periods": [
        {
          "id": 1,
          "code": "PERIOD-58543",
          "external_id": "58543",
          "start_date": "2025-12-15",
          "end_date": "2025-12-22",
          "base_prices": {
            "adult": "1299.00",
            "child": "999.00",
            "single": "299.00"
          },
          "end_prices": {
            "adult": "1399.00",
            "child": "1099.00",
            "single": "349.00"
          },
          "seats": 30,
          "booked": 15,
          "group_size": 30,
          "deposit": "300.00",
          "deposit_end": "2025-12-01",
          "com_agent": "150.00",
          "com_agent_end": "2025-12-01",
          "com_sale": "75.00",
          "com_sale_end": "2025-12-01",
          "airline_name": "Emirates",
          "promotion": true,
          "status": "available",
          "created_at": "2025-10-14T08:00:00Z",
          "updated_at": "2025-10-14T08:00:00Z",
          "flights": [
            {
              "id": 1,
              "flight_type": "departure",
              "airline_name": "Emirates",
              "flight_number": "EK450",
              "departure_city": "Bangkok",
              "departure_airport": "BKK",
              "departure_date": "2025-12-15",
              "departure_time": "23:55:00",
              "arrival_city": "Paris",
              "arrival_airport": "CDG",
              "arrival_date": "2025-12-16",
              "arrival_time": "05:45:00",
              "created_at": "2025-10-14T08:00:00Z"
            }
          ]
        }
      ],
      "itineraries": [
        {
          "id": 1,
          "day": 1,
          "title": "Arrival in Paris",
          "description": "Transfer to hotel, free time",
          "meals": "Dinner",
          "created_at": "2025-10-14T08:00:00Z"
        }
      ]
    }
  ]
}
```

---

### 3.3.2 Get Program Tour by Code

### GET /api/wholesale/program-tours/{code}/

Retrieve a single program tour by its code.

**Authentication**: None (public)

**Request**:
```bash
curl http://localhost:8000/api/wholesale/program-tours/2680/
```

**Response** (200 OK):
```json
{
  "id": 1,
  "code": "2680",
  "external_id": "2680",
  "name": "European Highlights 8 Days",
  "provider": {
    "name": "Zego Travel",
    "code": "zego"
  },
  "country": {
    "name": "France",
    "provider_code": "FR"
  },
  "duration_days": 8,
  "duration_nights": 7,
  "airline_name": "Emirates",
  "image_url": "https://example.com/tour.jpg",
  "file_pdf": "https://example.com/itinerary.pdf",
  "file_word": "https://example.com/itinerary.doc",
  "highlight": "Free city tours included",
  "data_quality_score": 85,
  "created_at": "2025-10-14T08:00:00Z",
  "updated_at": "2025-10-14T10:00:00Z",
  "periods": [...],
  "itineraries": [...]
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Not found."
}
```

---

## Pagination

### Custom Pagination Implementation

The Tours API uses a custom pagination class (`tours/views.py:10-27`) that provides enhanced metadata.

### Response Format

```json
{
  "count": 150,           // Total number of items
  "total": 15,            // Total number of pages
  "page_size": 10,        // Items per page
  "current": 1,           // Current page number
  "previous": null,       // URL to previous page (or null)
  "next": "http://...",   // URL to next page (or null)
  "results": [...]        // Array of items
}
```

### Query Parameters

| Parameter | Type | Default | Maximum | Description |
|-----------|------|---------|---------|-------------|
| `page` | integer | 1 | - | Page number |
| `page_size` | integer | 10 | 100 | Items per page |

### Example Requests

```bash
# Default (10 per page)
curl http://localhost:8000/api/tours/

# 25 items per page
curl http://localhost:8000/api/tours/?page_size=25

# Page 3 with 50 items per page
curl http://localhost:8000/api/tours/?page=3&page_size=50
```

### Pagination Limits

- **Default**: 10 items per page
- **Maximum**: 100 items per page
- Exceeding maximum returns 400 Bad Request

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | External API error |
| 503 | Service Unavailable | External API connection error |
| 504 | Gateway Timeout | External API timeout |

### Error Response Format

Errors use Django REST Framework's default format:

```json
{
  "detail": "Error message here"
}
```

For validation errors (400):
```json
{
  "field_name": [
    "Error message for this field"
  ]
}
```

For sync endpoint errors:
```json
{
  "error": "Error message",
  "details": "Additional details"
}
```

### Common Error Scenarios

**1. Resource Not Found (404)**
```json
{
  "detail": "Not found."
}
```

**2. Validation Error (400)**
```json
{
  "slug": [
    "tour with this slug already exists."
  ]
}
```

**3. External API Error (502)**
```json
{
  "error": "API request to fetch program tours failed",
  "message": "Failed to fetch tours from external API"
}
```

**4. Connection Error (503)**
```json
{
  "error": "Error connecting to external API for 'Zego': Connection refused"
}
```

**5. Timeout Error (504)**
```json
{
  "error": "Request to external API for 'Zego' timed out"
}
```

---

## Not Implemented Features

The following features are documented in [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) but are **NOT YET IMPLEMENTED**:

### Authentication
- ❌ JWT Bearer token authentication
- ❌ API key authentication
- ❌ User login/logout endpoints
- ❌ Token refresh endpoints
- ❌ Role-based permissions

### API Versioning
- ❌ `/api/v1/` URL prefix (uses `/api/` instead)
- ❌ Version negotiation
- ❌ Deprecation headers

### Rate Limiting
- ❌ Per-client rate limits
- ❌ Rate limit headers
- ❌ 429 Too Many Requests responses

### Advanced Features
- ❌ Standardized error response format
- ❌ Request ID tracking
- ❌ Field selection (partial response)
- ❌ Advanced filtering beyond provider name
- ❌ Sorting parameters
- ❌ Full-text search

### Monitoring
- ❌ API metrics tracking
- ❌ Response time logging
- ❌ Error rate monitoring

---

## Data Models

### Tour Model (tours/models.py)

```python
class Tour(models.Model):
    # Basic Information
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    duration = models.CharField(max_length=50)
    highlight = models.TextField(blank=True)
    hotel_stars = models.CharField(max_length=10, blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Media
    image = models.ImageField(upload_to='tours/', blank=True)

    # Category
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    tour_type = models.CharField(max_length=50, choices=TYPE_CHOICES)

    # Relations
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True)
    airline = models.ForeignKey(Airline, on_delete=models.SET_NULL, null=True)
    countries = models.ManyToManyField(Country)
    locations = models.ManyToManyField(Location)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### ProgramTour Model (wholesale/models.py)

```python
class ProgramTour(models.Model):
    # Identifiers
    code = models.CharField(max_length=255, unique=True)
    external_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    # Relations
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)

    # Tour Details
    duration_days = models.IntegerField()
    duration_nights = models.IntegerField()
    airline_name = models.CharField(max_length=255)

    # Media
    image_url = models.URLField(blank=True)
    file_pdf = models.URLField(blank=True)
    file_word = models.URLField(blank=True)

    # Content
    highlight = models.TextField(blank=True)

    # Quality
    data_quality_score = models.IntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## Testing Examples

### Using cURL

```bash
# Health Check
curl http://localhost:8000/api/healthcheck/

# List Tours (first page)
curl http://localhost:8000/api/tours/

# List Tours (custom page size)
curl http://localhost:8000/api/tours/?page_size=20

# Get Tour by Slug
curl http://localhost:8000/api/tours/european-highlights-8-days/

# List Program Tours
curl http://localhost:8000/api/wholesale/program-tours/

# Filter Program Tours by Provider
curl http://localhost:8000/api/wholesale/program-tours/?provider=Zego

# Trigger Country Sync
curl -X POST http://localhost:8000/api/wholesale/providers/zego/sync-countries/

# Trigger Program Tours Sync
curl -X POST http://localhost:8000/api/wholesale/providers/zego/sync-program-tours/

# Call External API (proxy)
curl http://localhost:8000/api/wholesale/call-external-api/zego/

# Create Tour
curl -X POST http://localhost:8000/api/tours/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Tour",
    "slug": "test-tour",
    "duration": "5 Days",
    "price": "999.00",
    "category": "DOMESTIC",
    "tour_type": "PACKAGE_TOUR"
  }'

# Update Tour (partial)
curl -X PATCH http://localhost:8000/api/tours/test-tour/ \
  -H "Content-Type: application/json" \
  -d '{
    "price": "1099.00"
  }'

# Delete Tour
curl -X DELETE http://localhost:8000/api/tours/test-tour/
```

### Using HTTPie

```bash
# Health Check
http GET http://localhost:8000/api/healthcheck/

# List Tours
http GET http://localhost:8000/api/tours/

# Get Tour by Slug
http GET http://localhost:8000/api/tours/european-highlights-8-days/

# Create Tour
http POST http://localhost:8000/api/tours/ \
  name="Test Tour" \
  slug="test-tour" \
  duration="5 Days" \
  price="999.00"

# Update Tour
http PATCH http://localhost:8000/api/tours/test-tour/ \
  price="1099.00"

# Delete Tour
http DELETE http://localhost:8000/api/tours/test-tour/
```

### Using Python requests

```python
import requests

base_url = "http://localhost:8000/api"

# Health Check
response = requests.get(f"{base_url}/healthcheck/")
print(response.json())

# List Tours
response = requests.get(f"{base_url}/tours/")
print(response.json())

# Get Tour by Slug
response = requests.get(f"{base_url}/tours/european-highlights-8-days/")
print(response.json())

# Create Tour
data = {
    "name": "Test Tour",
    "slug": "test-tour",
    "duration": "5 Days",
    "price": "999.00",
    "category": "DOMESTIC",
    "tour_type": "PACKAGE_TOUR"
}
response = requests.post(f"{base_url}/tours/", json=data)
print(response.json())

# Update Tour
data = {"price": "1099.00"}
response = requests.patch(f"{base_url}/tours/test-tour/", json=data)
print(response.json())

# Delete Tour
response = requests.delete(f"{base_url}/tours/test-tour/")
print(response.status_code)
```

---

## Development Setup

### Running the API

```bash
# Start Docker containers
docker-compose up

# API will be available at:
# http://localhost:8000/api/
```

### Accessing Django Admin

```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access admin at:
# http://localhost:8000/admin/
```

### Running Management Commands

```bash
# Sync Zego data
docker-compose exec web python manage.py sync_zego

# Sync Unique Inter data
docker-compose exec web python manage.py sync_unique_inter

# Audit tour countries
docker-compose exec web python manage.py audit_tour_countries
```

---

## Related Documentation

- [CLAUDE.md](./CLAUDE.md) - Project background and development guidelines
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - Planned/aspirational API design
- [API_DOCUMENTATION_CORRECTIONS.md](./API_DOCUMENTATION_CORRECTIONS.md) - Documentation issues identified
- [PROVIDER_ADAPTER_GUIDE.md](./PROVIDER_ADAPTER_GUIDE.md) - Provider integration guide

---

## Implementation Files Reference

### URL Configuration
- `Core/urls.py` - Main URL patterns
- `tours/urls.py` - Tour router configuration
- `wholesale/urls.py` - Wholesale router configuration

### Views
- `tours/views.py:29-33` - TourViewSet
- `wholesale/views.py:20-125` - ExternalApiCallViewSet
- `wholesale/views.py:128-207` - ProviderSyncViewSet
- `wholesale/views.py:277-302` - ProgramTourViewSet

### Serializers
- `tours/serializers.py:45-54` - TourSerializer
- `wholesale/serializers.py:37-48` - ProgramTourSerializer

### Models
- `tours/models.py` - Tour, TravelDate models
- `wholesale/models.py` - Provider, ProgramTour, Period models

---

## Changelog

### 2026-01-15
- Initial documentation of actual API implementation
- Documented all 7 working endpoints
- Added testing examples with cURL, HTTPie, and Python
- Clearly documented missing features (authentication, rate limiting, etc.)
- Added warning about security (no authentication)

---

## Support

For questions or issues with the API implementation:
1. Check this documentation first
2. Review the code in the implementation files listed above
3. Check Django logs: `docker-compose logs -f web`
4. Review related documentation files listed above
