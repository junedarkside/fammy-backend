import requests
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


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
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            logger.info(f"Making {method} request to: {url}")

            if method.upper() == 'GET':
                response = self.session.get(
                    url, params=params, timeout=timeout)
            # elif method.upper() == 'POST':
            #     response = self.session.post(url, json=data, params=params, timeout=timeout)
            # elif method.upper() == 'PUT':
            #     response = self.session.put(url, json=data, params=params, timeout=timeout)
            # elif method.upper() == 'DELETE':
            #     response = self.session.delete(url, params=params, timeout=timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()

            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP error for {url}: {e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"JSON decode error for {url}: {str(e)}")
            return None

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


class APIServiceFactory:
    """Factory class to create appropriate API service based on provider type"""

    @staticmethod
    def create_service(provider) -> BaseAPIService:
        """Create API service based on provider configuration"""

        # Check if provider has a specific service type
        service_type = getattr(provider, 'api_service_type', 'auto')
        if service_type == 'zego' or 'zego' in provider.name.lower():
            return ZegoAPIService(provider)
        elif service_type == 'generic':
            # Check if provider has custom endpoint configuration
            endpoint_config = getattr(provider, 'endpoint_config', None)
            return GenericAPIService(provider, endpoint_config)
        else:
            # Auto-detect based on API base URL
            if provider.base_url and 'zegoapi.com' in provider.base_url:
                return ZegoAPIService(provider)
            else:
                return GenericAPIService(provider)


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
