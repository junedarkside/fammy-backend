# Active Context

## Current Work Focus (2026-01-15)

**Documentation Reorganization** - Just completed organizing all project documentation into the `docs/` directory structure.

## Recent Changes

- **Documentation Organization**: Consolidated 21+ scattered markdown files into organized `docs/` directory
- **API Documentation**: Merged 3 API docs files into single consolidated overview with "Current vs Planned" sections
- **Memory Bank Updates**: Refreshing all memory-bank files to reflect current project state
- **File Structure**: Moved provider integration, architecture, and reference docs to subdirectories

## Next Steps

- Complete memory-bank updates
- Delete redundant documentation files
- Verify all internal links work correctly

## Active Decisions and Considerations

**Documentation Strategy:**
- Use `docs/` directory for comprehensive documentation
- Keep `CLAUDE.md` in root for AI assistant instructions
- Keep `readme.md` in root for project overview
- Organize by purpose: getting-started, development, api, provider-integration, architecture, reference

**API Implementation Status:**
- Current API is **public** (no authentication)
- Planned: JWT auth, API versioning, rate limiting
- API documentation clearly separates "Current Implementation" from "Planned Features"

## Important Patterns and Preferences

**Code Organization:**
- Follow Django app-based modular structure
- Provider adapter pattern for integrations
- Separate concerns: views, services, models
- Use Django REST Framework for APIs

**Development Workflow:**
- All development via Docker Compose
- PostgreSQL database (no SQLite)
- Redis for Celery broker
- Live code reloading via volume mounts

**Documentation Preferences:**
- Use Markdown for all documentation
- Cross-reference related documents
- Keep examples practical and copy-pasteable
- Separate "current implementation" from "planned features"

## Learnings and Project Insights

**Provider Integration:**
- Every wholesale operator has different API structure
- Provider adapter pattern is essential for maintainability
- Two-stage sync (fetch → process) helps with debugging
- Some providers have no API (manual entry required)

**Data Normalization Challenges:**
- Field naming varies (camelCase, snake_case)
- Data types inconsistent between providers
- Some data only exists in PDF/Word docs (not API)
- Country/location data often needs manual validation

**Development Best Practices:**
- Docker Compose essential for consistent development
- Bulk database operations much faster than individual saves
- Celery Beat for scheduled data sync tasks
- Django admin powerful for manual data management

## Current Provider Status

| Provider | Type | Status | Sync Method |
|----------|------|--------|-------------|
| Zego | API | ✅ Integrated | `sync_zego` command |
| Unique Inter | API | ✅ Integrated | `sync_unique_inter` command |
| Go365 | Manual | ✅ Integrated | Django admin / CSV import |

## Known Issues

- **API Security**: Currently no authentication on API endpoints (planned for future)
- **Country Validation**: Some tours have invalid country names (audit command available)
- **Documentation**: Some docs may reference old file paths (recently reorganized)
