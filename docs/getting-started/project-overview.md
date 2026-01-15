# TravelApp B2B Travel Platform

A Django-based B2B travel platform connecting travel agencies with tour operators through standardized data integration.

## Current Status

🚧 **Under Development** - This platform is currently in active development with core infrastructure established but data models being refined.

## What's Working

- ✅ Django project structure with modular apps
- ✅ Provider adapter pattern for API integration
- ✅ Base API service classes
- ✅ Development environment setup with Docker
- ✅ Management command structure

## What's Being Developed

- ⚠️ Database models (currently commented out during refinement)
- ⚠️ Data synchronization services
- ⚠️ REST API endpoints
- ⚠️ Authentication system

## Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Git

### Development Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd TravelApp/BackEnd
```

2. **Environment Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration
```

3. **Database Setup**
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

4. **Start Development Server**
```bash
python manage.py runserver
```

### Docker Development

```bash
# Start all services
docker-compose -f docker-compose.yml up

# Create superuser in Docker
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py createsuperuser"

# View logs
docker-compose -f docker-compose.yml logs -f
```

## Project Structure

```
TravelApp/BackEnd/
├── Core/                 # Django project configuration
├── Accounts/            # Custom user authentication
├── tours/               # Internal tour management
├── wholesale/           # Provider integration
├── management/          # Django management commands
└── tests/               # Test suite
```

## Travel Industry Focus

This platform serves the B2B travel industry by:

- **Connecting Agencies** with **Tour Operators**
- **Standardizing Data** from multiple providers
- **Automating Synchronization** of tour inventory
- **Simplifying Integration** through adapter patterns

### Key Concepts

- **Tour Operators**: Create and manage tour packages
- **Travel Agencies**: Access and sell tour packages
- **Provider Adapters**: Normalize different API formats
- **Data Synchronization**: Keep inventory up-to-date

## Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Main project documentation
- **[TRAVEL_INDUSTRY_GUIDE.md](./TRAVEL_INDUSTRY_GUIDE.md)** - Industry concepts
- **[PROVIDER_INTEGRATION.md](./PROVIDER_INTEGRATION.md)** - Integration guide
- **[NEW_DEVELOPER_GUIDE.md](./NEW_DEVELOPER_GUIDE.md)** - Developer onboarding

## Provider Integration

To integrate a new tour operator:

1. **Register Provider** in Django admin
2. **Create API Service** extending `BaseAPIService`
3. **Register Service** in `APIServiceFactory`
4. **Test Integration** with API endpoints

```python
# Example provider service
class YourOperatorAPIService(BaseAPIService):
    def _setup_authentication(self):
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}'
        })

    def get_tours(self):
        return self._make_request('tours')
```

## Development Guidelines

### Code Quality
- Follow Django conventions
- Write clear, simple code
- Test your implementations
- Update documentation

### Git Workflow
- Create feature branches
- Pull requests for review
- Clear commit messages
- Documentation updates with code changes

## Getting Help

1. **Read Documentation**: Check existing guides first
2. **Review Examples**: Look at existing provider implementations
3. **Test APIs**: Use curl/Postman to verify endpoints
4. **Ask Questions**: Contact the development team

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## License

[Add your license information here]

---

**Note**: This platform is under active development. Features and documentation are evolving as the system matures.