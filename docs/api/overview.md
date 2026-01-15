# API Overview

> **Last Updated**: 2026-01-15
> **Status**: Production (Current Implementation documented below)

---

## Quick Facts

| Property | Current Implementation | Planned (Not Yet Implemented) |
|----------|----------------------|-------------------------------|
| **Base URL** | `http://localhost:8000/api/` | `http://localhost:8000/api/v1/` |
| **API Versioning** | None | `/v1/` prefix with backward compatibility |
| **Authentication** | None (all endpoints public) | JWT Bearer tokens, API keys |
| **Rate Limiting** | Not implemented | Per-client tiers (1000-10000/hour) |
| **Format** | JSON | JSON (primary), XML (optional) |
| **Framework** | Django REST Framework | Django REST Framework + drf-spectacular |

---

## Currently Implemented

The following API endpoints are **fully functional** in the current implementation:

### Base URL: `http://localhost:8000/api/`

**All endpoints are PUBLIC (no authentication required)**

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/api/healthcheck/` | GET | System health check |
| `/api/tours/` | GET, POST, PUT, PATCH, DELETE | Tour CRUD operations |
| `/api/wholesale/call-external-api/{company}/` | GET | External API proxy |
| `/api/wholesale/providers/` | GET, POST, PUT, PATCH, DELETE | Provider management |
| `/api/wholesale/providers/{name}/sync-countries/` | POST | Trigger country sync |
| `/api/wholesale/providers/{name}/sync-program-tours/` | POST | Trigger tour sync |
| `/api/wholesale/program-tours/` | GET | Program tours (read-only) |

### Key Features

**Tours API:**
- Custom pagination with enhanced metadata
- Lookup by `slug` (not `id`)
- Nested relationships (operator, airline, countries, locations, travel_dates)
- Full CRUD operations

**Wholesale API:**
- External API proxy with provider authentication
- Provider management with sync triggers
- Program tours with optimized queries (select_related, prefetch_related)
- Filter by provider name
- Nested periods, flights, and itineraries

### Response Formats

**Pagination Response:**
```json
{
  "count": 150,           // Total items
  "total": 15,            // Total pages
  "page_size": 10,        // Items per page
  "current": 1,           // Current page
  "previous": null,       // Previous page URL
  "next": "...",          // Next page URL
  "results": [...]        // Data
}
```

**Error Response:**
```json
{
  "detail": "Error message"
}
```

For complete endpoint documentation with request/response examples, see [API Endpoints](endpoints.md).

---

## Planned Features (Not Yet Implemented)

The following features are planned but NOT yet in the current codebase:

### Authentication & Authorization

**Planned:**
- JWT Bearer token authentication (`/api/v1/auth/login/`, `/api/v1/auth/refresh/`)
- API key authentication for external integrations
- Role-based permissions (Admin, Agent, Sales)
- Protected endpoints for write operations

**Required Changes:**
```python
# Add to requirements.txt:
djangorestframework-simplejwt
drf-spectacular

# Add to settings.py:
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### API Versioning

**Planned:**
- URL path versioning: `/api/v1/`, `/api/v2/`
- Version negotiation via `Accept` header
- Deprecation and Sunset headers
- 6-month backward compatibility guarantee

**Migration Path:**
1. Add version prefix to all URLs
2. Create v1 URL patterns
3. Maintain v1 for 6 months after v2 release
4. Add deprecation warnings to old versions

### Rate Limiting

**Planned:**
- Per-client rate limits based on tier:
  - Basic: 1000 requests/hour
  - Premium: 10000 requests/hour
  - Enterprise: Custom limits
- Rate limit headers in responses
- 429 Too Many Requests responses

**Required Changes:**
```python
# Add to requirements.txt:
django-ratelimit

# Add to views:
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='1000/h')
def list_tours(request):
    ...
```

### OpenAPI/Swagger Documentation

**Planned:**
- Auto-generated OpenAPI 3.0 schema
- Interactive Swagger UI at `/api/docs/`
- Schema download at `/api/schema/`
- Type validation from serializers

**Required Changes:**
```python
# Add to settings.py:
SPECTACULAR_SETTINGS = {
    'TITLE': 'TravelApp B2B API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

### Advanced Features

**Planned:**
- Field selection (partial response): `?fields=id,name,price`
- Advanced filtering: `?price_gt=1000&category=INTERNATIONAL`
- Sorting: `?sort=-price,name`
- Full-text search: `?q=europe+beach`
- Request ID tracking for debugging
- Standardized error response format
- API metrics and monitoring

---

## Migration Path: Current to Planned

### Phase 1: Add Authentication (Priority: HIGH)
1. Install and configure `djangorestframework-simplejwt`
2. Add authentication endpoints (`/api/v1/auth/login/`, `/api/v1/auth/refresh/`)
3. Configure JWT settings (token lifetime, rotation)
4. Update REST_FRAMEWORK settings for default authentication
5. Mark existing endpoints as public with `AllowAny` permission
6. **Breaking Change**: Start requiring auth for write operations

### Phase 2: API Versioning (Priority: MEDIUM)
1. Create new URL patterns with `/api/v1/` prefix
2. Keep existing `/api/` URLs working (backward compatibility)
3. Add deprecation headers to old URLs
4. Update documentation to reference `/api/v1/`
5. Plan 6-month migration window

### Phase 3: Rate Limiting (Priority: HIGH for Production)
1. Install `django-ratelimit`
2. Configure rate limits per user tier
3. Add rate limit decorators to endpoints
4. Implement custom rate limit storage (Redis)
5. Add rate limit headers to responses

### Phase 4: Documentation (Priority: LOW)
1. Install `drf-spectacular`
2. Generate OpenAPI schema
3. Deploy Swagger UI
4. Add detailed field descriptions to serializers
5. Configure auto-documentation

### Phase 5: Advanced Features (Priority: LOW)
1. Implement field selection
2. Add advanced filtering
3. Implement sorting
4. Add full-text search
5. Add request ID tracking

---

## Security Considerations

### Current State ⚠️

**Critical Security Issues:**
1. **No Authentication** - Anyone can access/modify data
2. **No Rate Limiting** - Vulnerable to abuse/DoS
3. **No Input Validation** - Some endpoints lack proper validation
4. **Public Write Access** - Anyone can create/update/delete

**Recommended for Production:**
- Enable JWT authentication immediately
- Implement rate limiting
- Add input validation to all endpoints
- Restrict write operations to authenticated users
- Add HTTPS enforcement
- Implement CORS properly
- Add request logging for audit trails

---

## Testing

### Current Implementation

All endpoints can be tested without authentication:

```bash
# Health Check
curl http://localhost:8000/api/healthcheck/

# List Tours
curl http://localhost:8000/api/tours/

# Get Tour by Slug
curl http://localhost:8000/api/tours/european-highlights-8-days/

# Create Tour (no auth required!)
curl -X POST http://localhost:8000/api/tours/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","slug":"test","price":"999"}'

# Sync Provider Data
curl -X POST http://localhost:8000/api/wholesale/providers/zego/sync-program-tours/
```

### After Authentication Implementation

```bash
# Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Response: {"access":"...","refresh":"..."}

# Use token for authenticated requests
curl http://localhost:8000/api/v1/tours/ \
  -H "Authorization: Bearer <access_token>"
```

---

## Documentation References

### Current Implementation
- **[API Endpoints](endpoints.md)** - Complete endpoint reference with examples
- **[Provider Integration](../provider-integration/adapter-guide.md)** - Wholesale vendor integration
- **[Development Commands](../development/commands-reference.md)** - Management commands

### Historical (Outdated)
These files described the planned API before implementation:
- `~/API_DOCUMENTATION.md` - Original planned API design (now archived)
- `~/API_DOCUMENTATION_CORRECTIONS.md` - Issues identified in original docs (now resolved)

---

## Implementation Files

### Current Implementation

**URL Configuration:**
- `Core/urls.py` - Main URL patterns
- `tours/urls.py` - Tour router
- `wholesale/urls.py` - Wholesale router

**Views:**
- `tours/views.py:29-33` - TourViewSet
- `wholesale/views.py:20-125` - ExternalApiCallViewSet
- `wholesale/views.py:128-207` - ProviderSyncViewSet
- `wholesale/views.py:277-302` - ProgramTourViewSet

**Serializers:**
- `tours/serializers.py:45-54` - TourSerializer
- `wholesale/serializers.py:37-48` - ProgramTourSerializer

**Models:**
- `tours/models.py` - Tour, TravelDate
- `wholesale/models.py` - Provider, ProgramTour, Period

---

## Changelog

### 2026-01-15
- Consolidated API documentation from 3 files into single overview
- Clearly separated current implementation from planned features
- Documented migration path for implementing planned features
- Added security considerations and testing examples
- Referenced complete endpoint documentation

### Previous (see individual endpoint docs)
- Initial API implementation with Tours and Wholesale endpoints
- Custom pagination with enhanced metadata
- External API proxy functionality
- Provider sync triggers

---

## Support

For questions about:
- **Current API**: See [API Endpoints](endpoints.md)
- **Provider Integration**: See [Provider Adapter Guide](../provider-integration/adapter-guide.md)
- **Development**: See [Commands Reference](../development/commands-reference.md)
- **Planned Features**: See [Migration Path](#migration-path-current-to-planned) above
