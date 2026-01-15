import requests
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# Custom API exceptions for better error handling
class APIError(Exception):
    """Base class for API errors"""
    pass


class APITimeoutError(APIError):
    """Raised when API request times out"""
    pass


class APIConnectionError(APIError):
    """Raised when API connection fails"""
    pass


class APIHTTPError(APIError):
    """Raised when API returns HTTP error status"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class APIResponseError(APIError):
    """Raised when API response is invalid"""
    pass


class APIRequestError(APIError):
    """Raised when API request fails"""
    pass


class BaseAPIService(ABC):
    """Abstract base class for API services"""

    def __init__(self, provider):
        self.provider = provider
        self.base_url = provider.base_url.rstrip('/') if provider.base_url else ''
        self.token = provider.token
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            "Accept": "application/json",
        })
        # Set up authentication
        self._setup_authentication()

    @abstractmethod
    def _setup_authentication(self):
        """Setup authentication headers - to be implemented by subclasses"""
        pass

    @abstractmethod
    def get_countries(self) -> Optional[List[Dict]]:
        """Fetch all countries - to be implemented by subclasses"""
        pass

    @abstractmethod
    def get_program_tours(self) -> Optional[List[Dict]]:
        """Fetch all program tours - to be implemented by subclasses"""
        pass

    @abstractmethod
    def get_program_tour_details(self, product_code: str) -> Optional[Dict]:
        """Fetch details for a single program tour by its ProductID - to be implemented by subclasses"""
        pass

    def _make_request(self, endpoint: str, method: str = 'GET', params: Optional[Dict] = None,
                      data: Optional[Dict] = None, timeout: int = 30) -> Optional[Union[Dict, List]]:
        """Make HTTP request to API with improved error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            logger.info(f"Making {method} request to: {url}")

            if method.upper() == 'GET':
                response = self.session.get(
                    url, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(
                    url, json=data, params=params, timeout=timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(
                    url, json=data, params=params, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(
                    url, params=params, timeout=timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            # Handle empty responses
            if response.status_code == 204 or not response.content:
                logger.debug(f"Empty response from {url} (status: {response.status_code})")
                return {}

            try:
                return response.json()
            except ValueError as json_error:
                logger.error(f"JSON decode error for {url}: {str(json_error)}. Response content: {response.text[:200]}")
                raise APIResponseError(f"Invalid JSON response from {url}: {str(json_error)}")

        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout for {url} (timeout: {timeout}s)"
            logger.error(error_msg)
            raise APITimeoutError(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error for {url}: {str(e)}"
            logger.error(error_msg)
            raise APIConnectionError(error_msg) from e
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error for {url}: {e.response.status_code} - {e.response.text[:200]}"
            logger.error(error_msg)
            raise APIHTTPError(error_msg, status_code=e.response.status_code) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {url}: {str(e)}"
            logger.error(error_msg)
            raise APIRequestError(error_msg) from e

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            return response.status_code < 500
        except:
            return False


class ZegoAPIService(BaseAPIService):
    """Service class to interact with Zego API endpoints"""

    def _setup_authentication(self):
        """Setup Zego API authentication"""
        if self.token:
            self.session.headers.update({
                "auth-token": self.token
            })

    def get_countries(self) -> Optional[List[Dict]]:
        """Fetch all countries from Zego API"""
        return self._make_request("countries")

    def get_country_by_code(self, country_code: str) -> Optional[Dict]:
        """Fetch specific country by code"""
        return self._make_request(f"countries/{country_code}")

    def get_program_tours(self, page: Optional[int] = None, limit: Optional[int] = None) -> Optional[List[Dict]]:
        """Fetch all program tours with optional pagination"""
        params = {}
        if page is not None:
            params['page'] = page
        if limit is not None:
            params['limit'] = limit

        return self._make_request("programtours", params=params)

    def get_program_tour_by_code(self, tour_code: str) -> Optional[Dict]:
        """Fetch specific program tour by code"""
        return self._make_request(f"programtours/{tour_code}")

    def get_program_tour_details(self, product_id: str) -> Optional[Dict]:
        """Fetch specific program tour by its ProductID from Zego API."""
        return self._make_request(f"programtours/{product_id}")  # Assuming endpoint uses ProductID

    def get_latest_update_time(self) -> Optional[Dict]:
        """Get latest update time from API"""
        return self._make_request("programtours/updatelastesttime")

    def get_program_tours_by_country(self, country_code: str, page: Optional[int] = None) -> Optional[List[Dict]]:
        """Fetch program tours by country code with optional pagination"""
        params = {}
        if page is not None:
            params['page'] = page

        return self._make_request(f"programtours/country/{country_code}", params=params)


class GenericAPIService(BaseAPIService):
    """Generic API service for other wholesalers with configurable endpoints"""

    def __init__(self, provider, endpoint_config: Optional[Dict] = None):
        super().__init__(provider)

        # Default endpoint configuration
        self.endpoints = {
            'countries': 'countries',
            'country_detail': 'countries/{code}',
            'tours': 'tours',
            'tour_detail': 'tours/{code}',
            'latest_update': 'tours/latest',
            'tours_by_country': 'tours/country/{code}',
        }

        # Override with custom configuration if provided
        if endpoint_config:
            self.endpoints.update(endpoint_config)

    def _setup_authentication(self):
        """Setup authentication based on provider configuration"""
        if self.token:
            # Try different common authentication methods
            auth_method = getattr(self.provider, 'auth_method', 'bearer')

            if auth_method.lower() == 'bearer':
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
            elif auth_method.lower() == 'basic':
                from requests.auth import HTTPBasicAuth
                # Assume token contains username:password
                if ':' in self.token:
                    username, password = self.token.split(':', 1)
                    self.session.auth = HTTPBasicAuth(username, password)
            elif auth_method.lower() == 'apikey':
                self.session.headers.update({
                    'X-API-Key': self.token
                })
            elif auth_method.lower() == 'custom':
                # Custom header name
                header_name = getattr(
                    self.provider, 'auth_header', 'Authorization')
                self.session.headers.update({
                    header_name: self.token
                })

    def get_countries(self) -> Optional[List[Dict]]:
        """Fetch all countries using configured endpoint"""
        return self._make_request(self.endpoints['countries'])

    def get_country_by_code(self, country_code: str) -> Optional[Dict]:
        """Fetch specific country by code"""
        endpoint = self.endpoints['country_detail'].format(code=country_code)
        return self._make_request(endpoint)

    def get_program_tours(self, page: Optional[int] = None, limit: Optional[int] = None) -> Optional[List[Dict]]:
        """Fetch all program tours"""
        params = {}
        if page is not None:
            params['page'] = page
        if limit is not None:
            params['limit'] = limit

        return self._make_request(self.endpoints['tours'], params=params)

    def get_program_tour_by_code(self, tour_code: str) -> Optional[Dict]:
        """Fetch specific program tour by code"""
        endpoint = self.endpoints['tour_detail'].format(code=tour_code)
        return self._make_request(endpoint)

    def get_program_tour_details(self, product_id: str) -> Optional[Dict]:
        """Fetch specific program tour by its ProductID using configured endpoint."""
        endpoint = self.endpoints['tour_detail'].format(
            code=product_id)  # Assuming 'code' can be product_id
        return self._make_request(endpoint)

    def get_latest_update_time(self) -> Optional[Dict]:
        """Get latest update time from API"""
        return self._make_request(self.endpoints['latest_update'])

    def get_program_tours_by_country(self, country_code: str, page: Optional[int] = None) -> Optional[List[Dict]]:
        """Fetch program tours by country code"""
        params = {}
        if page is not None:
            params['page'] = page

        endpoint = self.endpoints['tours_by_country'].format(code=country_code)
        return self._make_request(endpoint, params=params)


class Go365APIService(BaseAPIService):
    """
    Go365 Travel API integration service.
    Supports multi-language (Thai, English, Chinese) and standard REST endpoints.
    """

    def __init__(self, provider):
        # Get default language from provider extra config before calling parent __init__
        self.default_language = 'en'
        if hasattr(provider, 'extra') and provider.extra:
            self.default_language = provider.extra.get('default_language', 'en')

        # Validate language support
        supported_languages = ['th', 'en', 'ch']
        if self.default_language not in supported_languages:
            logger.warning(f"Unsupported language '{self.default_language}', using 'en'")
            self.default_language = 'en'

        super().__init__(provider)

    def _setup_authentication(self):
        """Setup Go365 API authentication with token and optional secret key"""
        if not self.token:
            logger.warning(f"No token configured for {self.provider.name}")
            return

        # Get secret key from provider extra config
        secret_key = None
        if hasattr(self.provider, 'extra') and self.provider.extra:
            secret_key = self.provider.extra.get('secret_key')

        # Setup language header
        self.session.headers.update({
            'x-accept-language': self.default_language
        })

        # Determine authentication method based on available credentials
        if secret_key:
            # Dual authentication: token + secret key (HMAC signature)
            logger.info(f"Setting up dual authentication for {self.provider.name}")
            self._setup_hmac_authentication(self.token, secret_key)
        else:
            # Simple API key authentication (current method)
            logger.info(f"Setting up API key authentication for {self.provider.name}")
            self.session.headers.update({
                'x-api-key': self.token
            })

    def _setup_hmac_authentication(self, api_key: str, secret_key: str):
        """
        Setup HMAC signature authentication using API key and secret key

        Common patterns for travel APIs:
        1. x-api-key + x-signature headers
        2. Authorization header with HMAC signature
        3. Custom signature in query parameters
        """
        import hashlib
        import hmac
        import time

        # Store credentials for signature generation
        self.api_key = api_key
        self.secret_key = secret_key

        # Add API key header
        self.session.headers.update({
            'x-api-key': api_key
        })

        # Override _make_request to add signature to each request
        original_make_request = self._make_request

        def make_request_with_signature(endpoint: str, method: str = 'GET', params: Optional[Dict] = None,
                                      data: Optional[Dict] = None, timeout: int = 30) -> Optional[Union[Dict, List]]:
            """Make request with HMAC signature"""

            # Generate timestamp and nonce for signature
            timestamp = str(int(time.time()))
            nonce = hashlib.md5(f"{timestamp}{endpoint}".encode()).hexdigest()[:16]

            # Prepare string to sign (method + endpoint + timestamp + nonce + body)
            string_to_sign = f"{method.upper()}\n{endpoint}\n{timestamp}\n{nonce}"

            # Add request body to signature if present
            if data:
                import json
                body_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
                string_to_sign += f"\n{body_json}"

            # Generate HMAC signature
            signature = hmac.new(
                secret_key.encode(),
                string_to_sign.encode(),
                hashlib.sha256
            ).hexdigest()

            # Add signature headers
            self.session.headers.update({
                'x-timestamp': timestamp,
                'x-nonce': nonce,
                'x-signature': signature,
                'x-signature-method': 'HMAC-SHA256'
            })

            # Make the original request
            return original_make_request(endpoint, method, params, data, timeout)

        # Replace the _make_request method
        self._make_request = make_request_with_signature

    def get_countries(self) -> Optional[List[Dict]]:
        """Fetch available countries/destinations from Go365 API"""
        return self._make_request('api/v1/tours/country')

    def get_program_tours(self, page: int = 1, limit: int = 10, tour_ids: Optional[List[str]] = None) -> Optional[List[Dict]]:
        """Fetch tour list with pagination support"""
        params = {
            'start_page': page,
            'limit_page': limit
        }

        if tour_ids:
            params['tour_id'] = tour_ids

        return self._make_request('api/v1/tours/list', params=params)

    def get_program_tour_details(self, tour_id: str) -> Optional[Dict]:
        """Fetch detailed information for a specific tour"""
        return self._make_request(f'api/v1/tours/detail/{tour_id}')

    def get_tour_periods(self, tour_id: str) -> Optional[List[Dict]]:
        """Get available departure dates/periods for a tour"""
        response = self._make_request(f'api/v1/tours/period/{tour_id}')
        return response.get('periods', []) if response else None

    def search_tours(self, search_query: str = None, rate_start: float = None, rate_end: float = None,
                    sort_by: str = None, page: int = 1, limit: int = 10) -> Optional[List[Dict]]:
        """
        Search tours with multiple filters

        Args:
            search_query: Text search term
            rate_start: Minimum price/rate filter
            rate_end: Maximum price/rate filter
            sort_by: Sort option ('price_min', 'price_max', 'name_min', 'name_max', 'date_min', 'date_max')
            page: Page number for pagination
            limit: Results per page
        """
        data = {}
        params = {
            'start_page': page,
            'limit_page': limit
        }

        if search_query:
            data['search'] = search_query
        if rate_start is not None:
            data['rate_start'] = rate_start
        if rate_end is not None:
            data['rate_end'] = rate_end
        if sort_by:
            data['sort'] = sort_by

        return self._make_request('api/v1/tours/search', method='POST', data=data, params=params)

    def set_language(self, language: str):
        """Change API response language"""
        supported_languages = ['th', 'en', 'ch']
        if language in supported_languages:
            self.session.headers.update({'x-accept-language': language})
            logger.info(f"Language changed to: {language}")
        else:
            logger.warning(f"Unsupported language: {language}")


class APIServiceFactory:
    """Factory class to create appropriate API service and mapper based on provider type"""

    @staticmethod
    def create_service(provider) -> BaseAPIService:
        """Create API service based on provider configuration"""

        # Check provider code for exact match first
        provider_code = provider.code.lower()

        if provider_code == 'zego':
            return ZegoAPIService(provider)
        elif provider_code == 'unique_inter':
            return UniqueInterAPIService(provider)
        elif provider_code == 'go365':
            return Go365APIService(provider)
        elif provider_code == 'checkingroup':
            return CheckInGroupAPIService(provider)
        # Note: Remove non-existent provider services to prevent AttributeError
        else:
            # Check if provider has a specific service type
            service_type = getattr(provider, 'api_service_type', 'auto')
            if service_type == 'generic':
                # Check if provider has custom endpoint configuration
                endpoint_config = getattr(provider, 'endpoint_config', None)
                return GenericAPIService(provider, endpoint_config)
            else:
                # Auto-detect based on API base URL
                if provider.base_url and 'zegoapi.com' in provider.base_url:
                    return ZegoAPIService(provider)
                elif provider.base_url and 'uniqueinterwholesale.com' in provider.base_url:
                    return UniqueInterAPIService(provider)
                elif provider.base_url and 'go365travel.com' in provider.base_url:
                    return Go365APIService(provider)
                else:
                    logger.warning(f"No specific API service for '{provider.code}', using GenericAPIService")
                    return GenericAPIService(provider)

    @staticmethod
    def create_mapper(provider):
        """Create appropriate mapper for provider"""
        from .provider_mappers import (
            ZegoMapper,
            UniqueInterMapper,
            Go365Mapper,
            GenericMapper
        )

        provider_code = provider.code.lower()

        if provider_code == 'zego':
            return ZegoMapper(provider)
        elif provider_code == 'unique_inter':
            return UniqueInterMapper(provider)
        elif provider_code == 'go365':
            return Go365Mapper(provider)
        else:
            logger.warning(f"No specific mapper for '{provider.code}', using GenericMapper")
            return GenericMapper(provider)


# Example usage for different wholesaler types:
class TourismThailandAPIService(BaseAPIService):
    """Example service for Tourism Thailand API"""

    def _setup_authentication(self):
        if self.token:
            self.session.headers.update({
                'X-API-Key': self.token
            })

    def get_countries(self) -> Optional[List[Dict]]:
        return self._make_request("api/v2/destinations")

    def get_program_tours(self) -> Optional[List[Dict]]:
        return self._make_request("api/v2/packages")

    def get_program_tour_details(self, product_id: str) -> Optional[Dict]:
        # Example: This API might use /api/v2/packages/{product_id}
        return self._make_request(f"api/v2/packages/{product_id}")


class EuropePackagesAPIService(BaseAPIService):
    """Example service for European packages API"""

    def _setup_authentication(self):
        if self.token:
            # Basic authentication
            from requests.auth import HTTPBasicAuth
            username, password = self.token.split(':', 1)
            self.session.auth = HTTPBasicAuth(username, password)

    def get_countries(self) -> Optional[List[Dict]]:
        return self._make_request("v3/countries")

    def get_program_tours(self) -> Optional[List[Dict]]:
        return self._make_request("v3/tours")

    def get_program_tour_details(self, product_id: str) -> Optional[Dict]:
        # Example: This API might use /v3/tours/{product_id}
        return self._make_request(f"v3/tours/{product_id}")


class UniqueInterAPIService(BaseAPIService):
    """
    API Service for Unique Inter Wholesale.
    Uses category-based endpoints where each category represents a destination region.
    """

    CATEGORY_MAPPING = {
        '59': 'Europe',
        '60': 'Russia',
        '61': 'UK',
        '62': 'Hong Kong',
        '63': 'Special Promotion Europe',
        '64': 'Vietnam',
    }

    def __init__(self, provider):
        # Override base_url since Unique Inter uses a specific domain
        if not provider.base_url or 'uniqueinterwholesale.com' not in provider.base_url:
            provider.base_url = "https://uniqueinterwholesale.com"
        super().__init__(provider)

        # Get user email from provider.extra
        self.user_email = provider.extra.get('user_email', '') if provider.extra else ''
        if not self.user_email:
            logger.warning(f"No user_email configured for {provider.name} in provider.extra")

    def _setup_authentication(self):
        """Unique Inter uses query parameter authentication, not headers"""
        # No header-based authentication needed
        pass

    def get_tour_packages_by_category(self, category_id: str) -> Optional[List[Dict]]:
        """
        Fetch tour packages for a specific category.

        Args:
            category_id: The category ID (e.g., '59' for Europe, '64' for Vietnam)

        Returns:
            List of tour packages or None if request fails
        """
        if not self.user_email:
            logger.error(f"Cannot fetch tours: user_email not configured in {self.provider.name}.extra")
            return None

        params = {
            'id': category_id,
            'user': self.user_email
        }

        logger.info(f"Fetching category {category_id} ({self.CATEGORY_MAPPING.get(category_id, 'Unknown')}) for {self.provider.name}")
        return self._make_request('apiweb.php', params=params)

    def get_countries(self) -> Optional[List[Dict]]:
        """
        Return category-based 'countries' for Unique Inter.
        Note: Unique Inter doesn't have a dedicated countries endpoint.
        Categories represent destination regions instead.
        """
        return [
            {'code': cat_id, 'name': cat_name}
            for cat_id, cat_name in self.CATEGORY_MAPPING.items()
        ]

    def get_program_tours(self) -> Optional[List[Dict]]:
        """
        Fetch tours from all active categories configured for this provider.
        Queries the ProviderCategory model to get active categories dynamically.
        """
        from wholesale.models import ProviderCategory

        all_tours = []

        # Get active categories from database
        active_categories = ProviderCategory.objects.filter(
            provider=self.provider,
            is_active=True
        ).order_by('-priority', 'name')

        if not active_categories.exists():
            logger.warning(f"No active categories configured for {self.provider.name}")
            return None

        for category in active_categories:
            logger.info(f"Fetching tours for category: {category.name} ({category.category_id})")
            tours = self.get_tour_packages_by_category(category.category_id)

            if tours:
                # Add category metadata to each tour for tracking
                for tour in tours:
                    tour['_category_id'] = category.category_id
                    tour['_category_name'] = category.name
                all_tours.extend(tours)
            else:
                logger.warning(f"No tours returned for category {category.category_id}")

        return all_tours if all_tours else None

    def get_program_tour_details(self, product_code: str) -> Optional[Dict]:
        """
        Unique Inter doesn't have a separate detail endpoint.
        All tour information is included in the list response.
        """
        logger.info("Unique Inter API doesn't support separate detail endpoint")
        return None

    def discover_categories(self) -> List[Dict]:
        """
        Auto-discover available categories by testing known category IDs.
        Returns categories that have active tour data.

        Returns:
            List of dicts with category_id, name, name_local, and tour_count
        """
        if not self.user_email:
            logger.error("Cannot discover categories: user_email not configured")
            return []

        available_categories = []

        # Known category mappings with Thai translations
        known_categories = {
            '59': {'name': 'Europe Tours', 'name_th': 'ทัวร์เส้นทางยุโรป'},
            '60': {'name': 'Russia Tours', 'name_th': 'ทัวร์เส้นทางรัสเซีย'},
            '61': {'name': 'UK Tours', 'name_th': 'ทัวร์อังกฤษ สหราชอาณาจักร (UK)'},
            '62': {'name': 'Hong Kong Tours', 'name_th': 'ทัวร์เส้นทางฮ่องกง'},
            '63': {'name': 'Special Promotion Europe', 'name_th': 'Special Promotion ยุโรป'},
            '64': {'name': 'Vietnam Tours', 'name_th': 'ทัวร์เส้นทางเวียดนาม'},
        }

        logger.info(f"Discovering active categories for {self.provider.name}...")

        for cat_id, cat_info in known_categories.items():
            tours = self.get_tour_packages_by_category(cat_id)

            if tours and isinstance(tours, list) and len(tours) > 0:
                available_categories.append({
                    'category_id': cat_id,
                    'name': cat_info['name'],
                    'name_local': cat_info['name_th'],
                    'tour_count': len(tours)
                })
                logger.info(f"✓ Category {cat_id} ({cat_info['name']}): {len(tours)} tours")
            else:
                logger.info(f"✗ Category {cat_id} ({cat_info['name']}): No active tours")

        return available_categories


class CheckInGroupAPIService(BaseAPIService):
    """
    API Service for CheckIn Group Wholesale.

    CheckIn Group is a Thai B2B travel wholesaler with a public API.
    No authentication required. Provides tours with embedded periods.

    Base URL: https://api.checkingroup.co.th
    API Version: v1
    """

    def _setup_authentication(self):
        """No authentication required for CheckIn Group API."""
        pass

    def get_countries(self) -> Optional[List[Dict]]:
        """
        CheckIn Group doesn't have a countries endpoint.

        Returns empty list - countries must be extracted from tour names.
        """
        return []

    def get_program_tours(self, page: Optional[int] = None, limit: Optional[int] = None) -> Optional[List[Dict]]:
        """
        Fetch all program tours with embedded periods.

        GET /v1/programtours

        Returns:
            List of tour dictionaries with embedded periods

        Note:
            CheckIn Group returns all tours in a single response (no pagination).
            The page and limit parameters are accepted but ignored by the API.
        """
        response = self._make_request('GET', 'v1/programtours')
        return response if isinstance(response, list) else []

    def get_program_tour_details(self, tour_id: str) -> Optional[Dict]:
        """
        Fetch single program tour details.

        GET /v1/programtours/{tour_id}

        Args:
            tour_id: The tour ID (integer as string)

        Returns:
            Tour dictionary with embedded periods

        Note:
            The single tour endpoint wraps response in "data" key,
            unlike the list endpoint which returns array directly.
        """
        response = self._make_request('GET', f'v1/programtours/{tour_id}')
        return response.get('data', response) if isinstance(response, dict) else response

    def get_about(self) -> Optional[Dict]:
        """
        Fetch company information.

        GET /v1/about

        Returns:
            Company information dictionary including:
            - company_id
            - company_name
            - company_license
            - company_address
            - company_phone
            - company_lineid
            - company_email
            - company_taxid
            - company_vat
        """
        return self._make_request('GET', 'v1/about')
