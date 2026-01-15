# Product Context

## Why This Project Exists

The Thai B2B travel market lacks a centralized platform for travel agencies to access tour packages from multiple wholesale operators. Agencies must:
- Manually contact multiple tour operators
- Navigate different booking systems
- Deal with inconsistent data formats
- Manage pricing updates manually

This platform solves these problems by:
- **Aggregating** tour data from multiple wholesalers
- **Normalizing** data into a consistent format
- **Automating** data synchronization
- **Providing** a single API for all tour data

## Problems It Solves

**For Travel Agencies:**
- Single integration point for multiple tour operators
- Consistent data format across all providers
- Automated pricing and availability updates
- Reduced manual data entry

**For Tour Operators:**
- API-based distribution to agencies
- Automated inventory management
- Reduced manual booking processing
- Wider market reach

## How It Should Work

**Data Flow:**
1. **Wholesale Operators** expose tour data via APIs (or manual entry)
2. **Provider Adapters** fetch and normalize data from each operator
3. **Django Models** store unified tour data in PostgreSQL
4. **REST API** exposes tours to travel agencies
5. **Django Admin** allows staff to manage and override data

**Key Features:**
- Multi-provider data aggregation
- Provider-specific data normalization
- Bulk data synchronization via Celery
- Manual data management through Django admin
- RESTful API for B2B integration

## User Experience Goals

**For Travel Agencies (API Users):**
- Simple, consistent API endpoints
- Comprehensive tour data with pricing and availability
- Real-time (or near real-time) inventory updates
- Clear documentation and examples

**For Staff (Django Admin):**
- Intuitive interface for managing tours
- Easy provider configuration
- Manual override of automated data
- Data quality monitoring tools

**For Developers:**
- Clear provider adapter pattern
- Comprehensive documentation
- Easy addition of new providers
- Consistent code structure

## Target Market

**Primary: Thai Travel Agencies**
- Need access to international tour packages
- Departures from Thailand (Bangkok primarily)
- Popular destinations: Europe, Japan, Korea, China
- Thai-speaking tour guides and services

**Secondary: Wholesale Tour Operators**
- Want to distribute to Thai market
- Need automated booking systems
- Have varying API capabilities
- Require flexible integration options

## Key Differentiators

1. **Thai Market Focus** - Departures from Thailand, Thai-speaking guides
2. **Multi-Provider Support** - Single platform for multiple wholesalers
3. **Provider Adapter Pattern** - Easy to add new operators
4. **Hybrid Approach** - API integration + manual data entry
5. **Data Normalization** - Consistent format across all providers
