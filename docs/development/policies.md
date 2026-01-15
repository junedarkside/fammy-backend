# Development Policies

Core development principles and policies for the B2B Travel Platform.

## Core Development Principles

### 1. No Over-Engineering

Build only what is needed for the current requirement:
- Avoid adding features "for future use" or "just in case"
- Don't create abstraction layers without concrete use cases
- Prefer simple, direct solutions over complex architectures
- Follow YAGNI (You Aren't Gonna Need It) principle

**Example:**
```python
# ❌ Bad - Over-engineered
class AbstractDataProviderFactory(ABC):
    """Abstract factory for potential future data sources"""

    @abstractmethod
    def create_provider(self, provider_type: str) -> DataProvider:
        pass

# ✅ Good - Simple
def get_provider(code: str):
    """Get provider adapter by code"""
    if code == 'zego':
        return ZegoAdapter()
    elif code == 'unique_inter':
        return UniqueInterAdapter()
    raise ValueError(f"Unknown provider: {code}")
```

### 2. Keep It Simple

- Simple code is better than clever code
- Choose the most straightforward solution that meets requirements
- Avoid unnecessary complexity in design patterns
- Write code that is easy to understand and maintain
- Favor explicit over implicit

### 3. Reuse Existing Codebase

- Always search for existing implementations before writing new code
- Use established patterns from the current codebase
- Don't reinvent the wheel - leverage existing utilities, helpers, and services
- Study the existing architecture before making changes
- Maintain consistency with existing code style and patterns

**Before writing new code:**
```bash
# Search for existing patterns
grep -r "pattern_name" --include="*.py"
# Or use IDE search
```

### 4. No Monolithic Coding Style

- Break down large functions into smaller, focused units
- Follow Django's app-based modular structure
- Keep views, models, and business logic properly separated
- Avoid god classes or god functions that do everything
- Each module should have a single, clear responsibility

**Example:**
```python
# ❌ Bad - Monolithic view
def tour_list(request):
    # 500 lines of logic doing everything
    ...

# ✅ Good - Separated concerns
def tour_list(request):
    tours = get_published_tours()
    paginated = paginate_tours(tours, request)
    serialized = TourSerializer(paginated, many=True)
    return Response(serialized.data)
```

### 5. No Spaghetti Code

- Avoid deeply nested conditionals and complex control flow
- Don't use excessive global state or side effects
- Keep data flow clear and predictable
- Avoid circular dependencies between modules
- Write functions with clear inputs and outputs

### 6. Recheck Syntax

- Always verify code syntax before committing
- Use Django's built-in validation: `python manage.py check`
- Run linting tools if available
- Check for common Python/Django anti-patterns
- Ensure proper error handling and edge cases

**Pre-commit checklist:**
```bash
# Syntax check
python manage.py check

# Run tests (if available)
pytest

# Check for migrations
python manage.py makemigrations --dry-run
```

### 7. Updates Won't Break Current Functionalities

- Maintain backward compatibility when possible
- Write tests for existing behavior before making changes
- Use Django migrations properly for database changes
- Consider impact on other parts of the system
- Test integrations with existing services and APIs

### 8. Updates Won't Break Production

- Never deploy untested code to production
- Use environment-specific settings properly
- Test in development/staging before production deployment
- Handle database migrations carefully in production
- Have a rollback plan for significant changes
- Monitor production logs after deployments

## Before Making Changes

Use this checklist before modifying code:

1. **Read existing code** - Understand how it works before modifying
2. **Search for patterns** - Look for similar implementations in the codebase
3. **Think simple** - Choose the simplest approach that solves the problem
4. **Consider impact** - How will this affect other parts of the system?
5. **Test thoroughly** - Verify changes work and don't break existing functionality

## Code Style Guidelines

### Python/Django Conventions

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all public methods and classes
- Use type hints for function signatures
- Keep lines under 100 characters

### Model Guidelines

```python
from django.db import models
from typing import Optional


class Tour(models.Model):
    """
    Tour model representing travel packages.

    Attributes:
        name: Tour name
        slug: URL-friendly unique identifier
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def get_absolute_url(self) -> str:
        """Get the canonical URL for this tour."""
        return f"/tours/{self.slug}/"
```

### View Guidelines

- Use Django REST Framework ViewSets for API endpoints
- Keep business logic out of views - use services instead
- Return consistent response formats
- Handle errors gracefully

### Service Layer

For complex business logic, create service modules:

```python
# wholesale/services/tour_sync.py
class TourSyncService:
    """Service for synchronizing tour data from providers."""

    def sync_provider_tours(self, provider: Provider) -> dict:
        """
        Sync tours from a provider.

        Returns:
            Dict with sync statistics (created, updated, errors)
        """
        ...
```

## Testing Guidelines

### When to Write Tests

- Write tests for all new functionality
- Add tests when fixing bugs (to prevent regression)
- Test integration points (API endpoints, external services)
- Test data validation and edge cases

### Test Structure

```python
from django.test import TestCase
from wholesale.models import Provider


class ProviderSyncTestCase(TestCase):
    """Test provider synchronization functionality."""

    def setUp(self):
        """Set up test data."""
        self.provider = Provider.objects.create(
            name="Test Provider",
            code="test"
        )

    def test_sync_countries_success(self):
        """Test successful country synchronization."""
        # Arrange
        service = TourSyncService(self.provider)

        # Act
        result = service.sync_countries()

        # Assert
        self.assertEqual(result['created'], 10)
        self.assertEqual(result['errors'], 0)
```

## Git Workflow

### Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add Zego provider adapter for tour synchronization"

# Bad
git commit -m "update stuff"
```

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation changes

## Security Guidelines

### Input Validation

- Always validate user input
- Use Django forms or DRF serializers
- Sanitize data from external APIs
- Never trust client-side validation

### API Keys and Secrets

- Store API keys in environment variables
- Never commit secrets to git
- Use different keys for dev/staging/production
- Rotate keys regularly

### Database Queries

- Use parameterized queries (Django ORM does this by default)
- Avoid raw SQL when possible
- Be careful with `extra()` and `raw()` methods

## Performance Guidelines

### Database Optimization

```python
# ❌ Bad - N+1 query problem
tours = Tour.objects.all()
for tour in tours:
    print(tour.operator.name)  # Separate query for each tour

# ✅ Good - Use select_related
tours = Tour.objects.all().select_related('operator')
for tour in tours:
    print(tour.operator.name)  # No additional queries
```

### Caching

- Cache expensive operations (API calls, complex queries)
- Use Redis for caching in production
- Set appropriate cache expiration times
- Invalidate cache when data changes

### Bulk Operations

```python
# ❌ Bad - Individual saves
for tour_data in tour_list:
    tour = Tour.objects.create(**tour_data)

# ✅ Good - Bulk create
Tour.objects.bulk_create([
    Tour(**tour_data) for tour_data in tour_list
])
```

## Documentation Standards

### Code Documentation

- Document complex business logic
- Explain non-obvious implementation decisions
- Keep comments up to date with code changes
- Don't document the obvious

### README Files

Each major app/module should have a README explaining:
- Purpose and functionality
- Key models and their relationships
- Important services and utilities
- Usage examples

## Code Review Checklist

Before submitting code for review:

- [ ] Code follows style guidelines
- [ ] No unnecessary complexity
- [ ] Reuses existing patterns
- [ ] Tests are included
- [ ] Documentation is updated
- [ ] No syntax errors (`python manage.py check`)
- [ ] Backward compatibility maintained
- [ ] Security considerations addressed
- [ ] Performance impact considered

## Getting Help

When stuck or unsure:

1. Search the codebase for similar patterns
2. Read relevant documentation in `docs/`
3. Ask team members for guidance
4. Document decisions for future reference

---

For more detailed information, see:
- [New Developer Guide](../getting-started/new-developer-guide.md)
- [Commands Reference](commands-reference.md)
- [Provider Integration Guide](../provider-integration/adapter-guide.md)
