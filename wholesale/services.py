"""
Multi-Provider Integration Services

Simple, reusable components for managing multiple tour operator providers.
No over-engineering - just practical solutions.
"""

import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from .models import Provider
from .api_service import APIServiceFactory, BaseAPIService

logger = logging.getLogger(__name__)


class MultiProviderSyncService:
    """Simple service to sync multiple providers without over-engineering"""

    def __init__(self):
        self.factory = APIServiceFactory()

    def sync_all_providers(self) -> Dict[str, Dict]:
        """
        Sync all active providers

        Returns:
            Dict mapping provider codes to sync results
        """
        results = {}
        active_providers = Provider.objects.filter(is_active=True)

        logger.info(f"Starting sync for {active_providers.count()} providers")

        for provider in active_providers:
            try:
                result = self.sync_provider(provider)
                results[provider.code] = result
                logger.info(f"✓ {provider.code}: {result['status']}")
            except Exception as e:
                error_msg = f"Failed to sync {provider.code}: {str(e)}"
                logger.error(error_msg)
                results[provider.code] = {
                    'status': 'error',
                    'error': str(e),
                    'countries': 0,
                    'tours': 0
                }

        return results

    def sync_provider(self, provider: Provider) -> Dict:
        """
        Sync a single provider

        Args:
            provider: Provider instance to sync

        Returns:
            Dict with sync results
        """
        logger.info(f"Syncing provider: {provider.name} ({provider.code})")

        # Create API service
        service = self.factory.create_service(provider)

        # Test connection
        if not service.test_connection():
            raise ConnectionError(f"Cannot connect to {provider.name}")

        # Sync data
        result = {
            'provider': provider.name,
            'code': provider.code,
            'status': 'success',
            'countries': 0,
            'tours': 0,
            'sync_time': timezone.now().isoformat()
        }

        try:
            # Sync countries
            countries = service.get_countries()
            if countries:
                result['countries'] = len(countries) if isinstance(countries, list) else 1
                # TODO: Process countries into database when models are ready

            # Sync tours
            tours = service.get_program_tours()
            if tours:
                result['tours'] = len(tours) if isinstance(tours, list) else 1
                # TODO: Process tours into database when models are ready

            logger.info(f"✓ {provider.code}: {result['countries']} countries, {result['tours']} tours")

        except Exception as e:
            logger.error(f"Error during sync for {provider.code}: {e}")
            result['status'] = 'partial_error'
            result['error'] = str(e)

        return result

    def test_provider_connection(self, provider: Provider) -> bool:
        """
        Test connection to a provider

        Args:
            provider: Provider to test

        Returns:
            True if connection successful
        """
        try:
            service = self.factory.create_service(provider)
            return service.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed for {provider.code}: {e}")
            return False

    def test_all_connections(self) -> Dict[str, bool]:
        """
        Test connections for all active providers

        Returns:
            Dict mapping provider codes to connection status
        """
        results = {}
        active_providers = Provider.objects.filter(is_active=True)

        for provider in active_providers:
            results[provider.code] = self.test_provider_connection(provider)

        return results


class ProviderRegistrationService:
    """Service for managing provider registration and configuration"""

    @staticmethod
    def register_standard_provider(
        name: str,
        code: str,
        base_url: str,
        token: str = None,
        auth_method: str = 'bearer',
        service_type: str = 'generic',
        endpoints: Dict = None
    ) -> Provider:
        """
        Register a standard REST API provider

        Args:
            name: Provider display name
            code: Unique provider code
            base_url: API base URL
            token: Authentication token
            auth_method: Authentication method
            service_type: Service type (generic/specific/auto)
            endpoints: Custom endpoint mapping

        Returns:
            Created Provider instance
        """
        extra = {
            'auth_method': auth_method,
            'service_type': service_type
        }
        if endpoints:
            extra['endpoints'] = endpoints

        provider = Provider.objects.create(
            name=name,
            code=code,
            base_url=base_url,
            token=token,
            extra=extra,
            is_active=True
        )

        logger.info(f"Registered provider: {name} ({code})")
        return provider

    @staticmethod
    def register_bearer_token_provider(
        name: str,
        code: str,
        base_url: str,
        token: str,
        endpoints: Dict = None
    ) -> Provider:
        """Register a provider using Bearer token authentication"""
        return ProviderRegistrationService.register_standard_provider(
            name=name,
            code=code,
            base_url=base_url,
            token=token,
            auth_method='bearer',
            service_type='generic',
            endpoints=endpoints
        )

    @staticmethod
    def register_api_key_provider(
        name: str,
        code: str,
        base_url: str,
        token: str,
        header_name: str = 'X-API-Key',
        endpoints: Dict = None
    ) -> Provider:
        """Register a provider using API key authentication"""
        extra = {'auth_header': header_name}
        if endpoints:
            extra['endpoints'] = endpoints

        return Provider.objects.create(
            name=name,
            code=code,
            base_url=base_url,
            token=token,
            auth_method='apikey',
            service_type='generic',
            extra=extra
        )

    @staticmethod
    def register_basic_auth_provider(
        name: str,
        code: str,
        base_url: str,
        username: str,
        password: str,
        endpoints: Dict = None
    ) -> Provider:
        """Register a provider using Basic authentication"""
        extra = {'auth_username': username}
        if endpoints:
            extra['endpoints'] = endpoints

        return Provider.objects.create(
            name=name,
            code=code,
            base_url=base_url,
            token=password,
            auth_method='basic',
            service_type='generic',
            extra=extra
        )

    @staticmethod
    def register_go365_provider(
        name: str,
        code: str,
        base_url: str = 'https://www.go365travel.com',
        api_key: str = None,
        secret_key: str = None,
        default_language: str = 'en'
    ) -> Provider:
        """
        Register a Go365 Travel provider with dual authentication support

        Args:
            name: Provider display name
            code: Unique provider code
            base_url: API base URL
            api_key: API key for authentication
            secret_key: Secret key for HMAC signature (optional)
            default_language: Default language for API responses

        Returns:
            Created Provider instance
        """
        extra = {
            'default_language': default_language,
            'supported_languages': ['th', 'en', 'ch'],
            'service_type': 'specific',  # Use specific service for Go365
            'auth_method': 'hmac' if secret_key else 'apikey'
        }

        # Store secret key in extra config for secure access
        if secret_key:
            extra['secret_key'] = secret_key
            logger.info(f"Registering {name} with dual authentication (API key + HMAC signature)")
        else:
            logger.info(f"Registering {name} with API key authentication only")

        return Provider.objects.create(
            name=name,
            code=code,
            base_url=base_url,
            token=api_key,
            extra=extra,
            is_active=True
        )

    @staticmethod
    def register_dual_auth_provider(
        name: str,
        code: str,
        base_url: str,
        api_key: str,
        secret_key: str,
        auth_method: str = 'hmac',
        **extra_config
    ) -> Provider:
        """
        Register a provider with dual authentication (API key + secret key)

        Args:
            name: Provider display name
            code: Unique provider code
            base_url: API base URL
            api_key: API key for authentication
            secret_key: Secret key for HMAC signature
            auth_method: Authentication method ('hmac', 'oauth', 'custom')
            **extra_config: Additional provider configuration

        Returns:
            Created Provider instance
        """
        extra = {
            'secret_key': secret_key,
            'auth_method': auth_method,
            'service_type': 'specific',
            **extra_config
        }

        logger.info(f"Registering {name} with dual authentication ({auth_method})")

        return Provider.objects.create(
            name=name,
            code=code,
            base_url=base_url,
            token=api_key,
            extra=extra,
            is_active=True
        )


class ProviderDataProcessor:
    """Simple data processor for normalizing provider data"""

    @staticmethod
    def normalize_countries(raw_countries: List[Dict], provider_code: str) -> List[Dict]:
        """
        Normalize country data from different providers

        Args:
            raw_countries: Raw country data from provider API
            provider_code: Provider code for context

        Returns:
            List of normalized country dictionaries
        """
        normalized = []

        for country in raw_countries:
            # Handle different country field formats from various providers
            if provider_code == 'go365':
                # Go365 specific format
                normalized_country = {
                    'provider_code': provider_code,
                    'name': country.get('name', country.get('country_name', '')),
                    'code': country.get('code', country.get('country_code', country.get('id', ''))),
                    'content': country.get('description', country.get('content', '')),
                    'locations': country.get('cities', country.get('locations', []))
                }
            else:
                # Default/standard format (Zego, Generic services)
                normalized_country = {
                    'provider_code': provider_code,
                    'name': country.get('name', country.get('country_name', '')),
                    'code': country.get('code', country.get('country_code', '')),
                    'content': country.get('description', country.get('content', '')),
                    'locations': country.get('locations', [])
                }
            normalized.append(normalized_country)

        return normalized

    @staticmethod
    def normalize_tours(raw_tours: List[Dict], provider_code: str) -> List[Dict]:
        """
        Normalize tour data from different providers

        Args:
            raw_tours: Raw tour data from provider API
            provider_code: Provider code for context

        Returns:
            List of normalized tour dictionaries
        """
        normalized = []

        for tour in raw_tours:
            # Handle different tour field formats from various providers
            if provider_code == 'go365':
                # Go365 specific format
                normalized_tour = {
                    'provider_code': provider_code,
                    'external_id': str(tour.get('tour_id', tour.get('id', ''))),
                    'code': tour.get('tour_id', tour.get('id', '')),
                    'name': tour.get('name', tour.get('title', '')),
                    'description': tour.get('description', ''),
                    'duration_days': tour.get('days', 0),
                    'duration_nights': tour.get('nights', 0),
                    'country_name': tour.get('country', ''),
                    'airline_name': tour.get('airline', ''),
                    'image_url': tour.get('image_url', tour.get('jpg', '')),
                    'file_pdf': tour.get('pdf', ''),
                    'file_word': tour.get('word', ''),
                    'price': tour.get('price', tour.get('adult', 0)),
                    'currency': tour.get('currency', 'USD')
                }
            else:
                # Default/standard format (Zego, Unique Inter, Generic services)
                normalized_tour = {
                    'provider_code': provider_code,
                    'external_id': str(tour.get('id', tour.get('product_id', tour.get('tour_id', '')))),
                    'code': tour.get('code', tour.get('product_code', '')),
                    'name': tour.get('name', tour.get('title', tour.get('tour_name', ''))),
                    'description': tour.get('description', tour.get('highlight', '')),
                    'duration_days': tour.get('days', 0),
                    'duration_nights': tour.get('nights', 0),
                    'country_name': tour.get('country', tour.get('country_name', '')),
                    'airline_name': tour.get('airline', tour.get('airline_name', '')),
                    'image_url': tour.get('image', tour.get('image_url', '')),
                    'file_pdf': tour.get('pdf', tour.get('file_pdf', '')),
                    'file_word': tour.get('word', tour.get('file_word', '')),
                    'price': tour.get('price', tour.get('adult_price', 0)),
                    'currency': tour.get('currency', 'USD')
                }
            normalized.append(normalized_tour)

        return normalized

    @staticmethod
    def normalize_periods(raw_periods: List[Dict], provider_code: str) -> List[Dict]:
        """
        Normalize period/departure data from different providers

        Args:
            raw_periods: Raw period data from provider API
            provider_code: Provider code for context

        Returns:
            List of normalized period dictionaries
        """
        normalized = []

        for period in raw_periods:
            normalized_period = {
                'provider_code': provider_code,
                'external_id': str(period.get('id', period.get('period_id', period.get('departure_id', '')))),
                'code': period.get('code', period.get('period_code', '')),
                'start_date': period.get('start_date', period.get('date', period.get('departure_date', ''))),
                'end_date': period.get('end_date', period.get('return_date', '')),
                'airline_name': period.get('airline', period.get('airline_name', '')),
                'group_size': period.get('group_size', period.get('size', 0)),
                'booked': period.get('booked', period.get('booking', 0)),
                'available': period.get('available', period.get('seats', period.get('avbl', 0))),
                'status': period.get('status', 'Available'),
                'price': period.get('price', period.get('adult', 0)),
                'deposit': period.get('deposit', 0),
                'commission': period.get('commission', period.get('com', 0))
            }
            normalized.append(normalized_period)

        return normalized


class ProviderHealthChecker:
    """Simple health checking for providers"""

    def __init__(self):
        self.factory = APIServiceFactory()

    def check_provider_health(self, provider: Provider) -> Dict:
        """
        Check health of a single provider

        Args:
            provider: Provider to check

        Returns:
            Dict with health status
        """
        health_info = {
            'provider': provider.name,
            'code': provider.code,
            'status': 'unhealthy',
            'response_time': None,
            'error': None,
            'last_check': timezone.now().isoformat()
        }

        try:
            import time
            start_time = time.time()

            service = self.factory.create_service(provider)
            is_connected = service.test_connection()

            response_time = time.time() - start_time
            health_info['response_time'] = round(response_time, 2)

            if is_connected:
                health_info['status'] = 'healthy' if response_time < 5 else 'degraded'
            else:
                health_info['status'] = 'unhealthy'
                health_info['error'] = 'Connection failed'

        except Exception as e:
            health_info['status'] = 'unhealthy'
            health_info['error'] = str(e)

        return health_info

    def check_all_providers_health(self) -> Dict[str, Dict]:
        """
        Check health of all active providers

        Returns:
            Dict mapping provider codes to health information
        """
        results = {}
        active_providers = Provider.objects.filter(is_active=True)

        for provider in active_providers:
            results[provider.code] = self.check_provider_health(provider)

        return results

    def get_overall_health_status(self) -> Dict:
        """
        Get overall system health status

        Returns:
            Dict with overall health summary
        """
        health_results = self.check_all_providers_health()

        total_providers = len(health_results)
        healthy_providers = sum(1 for h in health_results.values() if h['status'] == 'healthy')
        degraded_providers = sum(1 for h in health_results.values() if h['status'] == 'degraded')
        unhealthy_providers = total_providers - healthy_providers - degraded_providers

        overall_status = 'healthy'
        if unhealthy_providers > 0:
            overall_status = 'unhealthy'
        elif degraded_providers > 0:
            overall_status = 'degraded'

        return {
            'overall_status': overall_status,
            'total_providers': total_providers,
            'healthy_providers': healthy_providers,
            'degraded_providers': degraded_providers,
            'unhealthy_providers': unhealthy_providers,
            'health_percentage': round((healthy_providers / total_providers) * 100, 1) if total_providers > 0 else 0,
            'last_check': timezone.now().isoformat(),
            'details': health_results
        }


# Convenience functions for common operations

def sync_all_providers() -> Dict:
    """Convenience function to sync all providers"""
    service = MultiProviderSyncService()
    return service.sync_all_providers()


def test_all_connections() -> Dict:
    """Convenience function to test all provider connections"""
    service = MultiProviderSyncService()
    return service.test_all_connections()


def get_system_health() -> Dict:
    """Convenience function to get overall system health"""
    checker = ProviderHealthChecker()
    return checker.get_overall_health_status()


def register_standard_provider(**kwargs) -> Provider:
    """Convenience function to register a standard provider"""
    return ProviderRegistrationService.register_standard_provider(**kwargs)