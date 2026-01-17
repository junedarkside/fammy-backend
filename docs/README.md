# B2B Travel Platform Documentation

Welcome to the documentation for the B2B Travel Platform for Thai Customers. This platform connects travel agencies with wholesale tour operators through automated data synchronization.

## Quick Navigation

### Getting Started
- [Project Overview](getting-started/project-overview.md) - What this platform is and how it works
- [Quick Start](getting-started/quick-start.md) - Docker setup and first run
- [New Developer Guide](getting-started/new-developer-guide.md) - Onboarding for new team members

### Development
- [Commands Reference](development/commands-reference.md) - Common development commands
- [Development Policies](development/policies.md) - Coding standards and best practices

### API Documentation
- [API Overview](api/overview.md) - Current implementation and planned features
- [API Endpoints](api/endpoints.md) - Complete endpoint reference

### Provider Integration
- **[Evaluation Tool](provider-integration/evaluation-tool.md)** ⚡ - Analyze provider APIs and get recommendations (NEW)
- **[Claude Code Skills](../.claude/README.md)** 🤖 - AI-powered debugging and integration tools
  - `/debug-provider-sync` - Diagnose sync failures
  - `/integrate-provider` - Add new providers
  - `/validate-models` - Prevent constraint violations
- [Adapter Guide](provider-integration/adapter-guide.md) - Comprehensive guide for integrating tour operators
- [Quick Start](provider-integration/quick-start.md) - Fast track for provider integration
- [CheckIn Group Guide](provider-integration/checkingroup-guide.md) - CheckIn Group API integration
- [Go365 Guide](provider-integration/go365-guide.md) - Go365-specific integration
- [Multi-Provider Architecture](provider-integration/multi-provider.md) - Design for multiple providers

### Architecture
- [System Design](architecture/system-design.md) - Overall architecture and patterns
- [Database Design](architecture/database-design.md) - Data model and relationships
- [Data Consistency](architecture/data-consistency.md) - Cross-provider data normalization

### Reference
- [Travel Industry Guide](reference/travel-industry.md) - Industry concepts and terminology
- [Admin Improvements](reference/admin-improvements.md) - Django admin enhancements

## Project Root Files

- [`CLAUDE.md`](../CLAUDE.md) - Primary AI assistant instructions (Claude Code)
- [`README.md`](../README.md) - Project quick start and status

## Memory Bank

The [`memory-bank/`](../memory-bank/) directory contains context for AI assistants working on this project:
- `projectbrief.md` - Core requirements and goals
- `productContext.md` - User experience goals
- `activeContext.md` - Current work focus
- `systemPatterns.md` - Architecture patterns
- `techContext.md` - Technology stack
- `progress.md` - Implementation status

## Quick Start

```bash
# Start all services
docker-compose up

# Run migrations
docker-compose exec web python manage.py migrate

# Sync data from providers
docker-compose exec web python manage.py sync_zego
docker-compose exec web python manage.py sync_unique_inter
docker-compose exec web python manage.py sync_checkingroup
```

## Documentation Structure

```
docs/
├── getting-started/     # New developer onboarding
├── development/         # Development workflows and policies
├── api/                 # API documentation
├── provider-integration/# Wholesale vendor integration
├── architecture/        # System design and database
└── reference/           # Industry and auxiliary guides
```

## Contributing

When updating documentation:
1. Keep it simple and focused
2. Update the relevant section in this README if adding new docs
3. Cross-reference related documents
4. Remove outdated content rather than creating "v2" versions

## Support

For questions about:
- **Development setup**: See [Quick Start](getting-started/quick-start.md)
- **Provider integration**: See [Adapter Guide](provider-integration/adapter-guide.md)
- **API usage**: See [API Overview](api/overview.md)
- **Project policies**: See [Development Policies](development/policies.md)
