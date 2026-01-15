"""
Provider mapper classes for transforming API data to standard model format.

This module provides mapper classes that transform raw provider API data
into the standard format expected by our Django models.
"""

from typing import Dict, Optional, List
from decimal import Decimal
from .models import Provider, Country
from .field_normalizers import (
    FieldNormalizer,
    ZegoNormalizer,
    UniqueInterNormalizer,
    Go365Normalizer
)


def normalize_country_name(country_name: str) -> str:
    """
    Normalize country name for consistency.

    This is a simplified version - the full implementation with
    300+ mappings is in data_sync_service.py
    """
    if not country_name:
        return ''

    return country_name.strip().lower()


class ProviderMapper:
    """
    Base class for mapping provider data to standard model format.

    Each provider should have its own mapper class that inherits from
    this base class and implements the mapping methods.
    """

    def __init__(self, provider: Provider):
        """
        Initialize mapper with provider instance.

        Args:
            provider: Provider model instance
        """
        self.provider = provider
        self.normalizer = FieldNormalizer()

    def map_tour_data(self, raw_data: Dict) -> Dict:
        """
        Map raw tour data from API to standard format.

        Args:
            raw_data: Raw tour data from provider API

        Returns:
            Dictionary of field names and values for ProgramTour model
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement map_tour_data()"
        )

    def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        Map raw period data from API to standard format.

        Args:
            raw_data: Raw period data from provider API
            program_tour: ProgramTour instance (for foreign key)

        Returns:
            Dictionary of field names and values for Period model
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement map_period_data()"
        )

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        """
        Map raw flight data from API to standard format.

        Args:
            raw_data: Raw flight data from provider API
            period: Period instance (for foreign key)

        Returns:
            Dictionary of field names and values for Flight model
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement map_flight_data()"
        )

    def map_itinerary_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        Map raw itinerary data from API to standard format.

        Args:
            raw_data: Raw itinerary data from provider API
            program_tour: ProgramTour instance (for foreign key)

        Returns:
            Dictionary of field names and values for Itinerary model
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement map_itinerary_data()"
        )

    def _get_or_create_country(self, country_name: str, country_code: str = None) -> Optional[Country]:
        """
        Get or create country based on name and code.

        Args:
            country_name: Country name from API
            country_code: Country code from API (optional)

        Returns:
            Country instance or None
        """
        if not country_name:
            return None

        # Try to find existing country by normalized name
        normalized = normalize_country_name(country_name)
        if not normalized:
            return None

        try:
            country = Country.objects.get(
                provider=self.provider,
                normalized_name=normalized
            )
            return country
        except Country.DoesNotExist:
            # Don't auto-create - requires proper ISO code and validation
            # Leave country field empty, keep country_name as snapshot
            return None


class ZegoMapper(ProviderMapper):
    """
    Zego data mapper - simplest implementation with 1:1 field mapping.

    Zego API provides the most complete data structure, so this mapper
    primarily handles direct field mapping with minimal transformation.
    """

    def __init__(self, provider: Provider):
        super().__init__(provider)
        self.normalizer = ZegoNormalizer()

    def map_tour_data(self, raw_data: Dict) -> Dict:
        """
        Map Zego tour data to standard format.

        Zego API Fields → Model Fields:
        - ProductID → external_id
        - ProductCode → code
        - ProductName → name
        - Days/Nights → days/nights
        - CountryCode → country (via lookup)
        - AirlineCode/AirlineName → airline_code/airline_name
        - FileWord/FilePDF/URLImage → file_word/file_pdf/image_url
        - Highlight → highlight
        - MaxHotelStars/MinHotelStars → max_hotel_stars/min_hotel_stars
        - PlaneMeals/TotalMeals → plane_meals/total_meals
        - Locations[] → locations
        """
        country_name = raw_data.get('CountryName', '')
        country_code = raw_data.get('CountryCode', '')
        country = self._get_or_create_country(country_name, country_code)

        return {
            'provider': self.provider.id,
            'external_id': raw_data.get('ProductID', ''),
            'code': raw_data.get('ProductCode', ''),
            'name': raw_data.get('ProductName', ''),
            'days': self.normalizer.normalize_integer(raw_data.get('Days')),
            'nights': self.normalizer.normalize_integer(raw_data.get('Nights')),
            'country': country,
            'country_name': country_name,
            'airline_code': raw_data.get('AirlineCode', ''),
            'airline_name': raw_data.get('AirlineName', ''),
            'file_pdf': raw_data.get('FilePDF', ''),
            'file_word': raw_data.get('FileWord', ''),
            'image_url': raw_data.get('URLImage', ''),
            'highlight': raw_data.get('Highlight', ''),
            'max_hotel_stars': self.normalizer.normalize_integer(raw_data.get('MaxHotelStars')),
            'min_hotel_stars': self.normalizer.normalize_integer(raw_data.get('MinHotelStars')),
            'plane_meals': self.normalizer.normalize_boolean(raw_data.get('PlaneMeals')),
            'total_meals': self.normalizer.normalize_integer(raw_data.get('TotalMeals')),
            'locations': raw_data.get('Locations', []),
            # Data completeness - Zego has everything
            'has_flights': True,
            'has_itineraries': True,
            'has_full_pricing': True,
            'data_quality_score': 100,
        }

    def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        Map Zego period data to standard format.

        Zego provides comprehensive pricing with 15+ price types.
        All stored in JSONField for flexibility.
        """
        # Build base_prices JSONField
        base_prices = {
            'adult': self.normalizer.normalize_price(raw_data.get('Price')),
            'child': self.normalizer.normalize_price(raw_data.get('Price_Child')),
            'child_nb': self.normalizer.normalize_price(raw_data.get('Price_ChildNB')),
            'infant': self.normalizer.normalize_price(raw_data.get('Price_Infant')),
            'join_land': self.normalizer.normalize_price(raw_data.get('Price_JoinLand')),
            'single_bed': self.normalizer.normalize_price(raw_data.get('Price_Single_Bed')),
            'twin_bed': self.normalizer.normalize_price(raw_data.get('Price_Twin_Bed')),
            'double_bed': self.normalizer.normalize_price(raw_data.get('Price_Double_Bed')),
            'triple_bed': self.normalizer.normalize_price(raw_data.get('Price_Triple_Bed')),
            'single_visa': self.normalizer.normalize_price(raw_data.get('Price_Single_Visa')),
            'group_visa': self.normalizer.normalize_price(raw_data.get('Price_Group_Visa')),
            'express_visa': self.normalizer.normalize_price(raw_data.get('Price_Express_Visa')),
        }

        # Build end_prices JSONField
        end_prices = {
            'adult': self.normalizer.normalize_price(raw_data.get('Price_End')),
            'child': self.normalizer.normalize_price(raw_data.get('Price_Child_End')),
            # Add other end prices as needed
        }

        return {
            'provider': self.provider.id,
            'external_id': raw_data.get('PeriodID', ''),
            'code': raw_data.get('PeriodCode', ''),
            'program_id': program_tour.id if program_tour else None,
            'start_date': self.normalizer.normalize_date(raw_data.get('PeriodStartDate')),
            'end_date': self.normalizer.normalize_date(raw_data.get('PeriodEndDate')),
            'bus': raw_data.get('Bus', ''),
            'country_name': raw_data.get('CountryName', ''),
            'airline_code': raw_data.get('AirlineCode', ''),
            'airline_name': raw_data.get('AirlineName', ''),
            'airport': raw_data.get('Airport', ''),
            'group_size': self.normalizer.normalize_integer(raw_data.get('Groupsize')),
            'booked': self.normalizer.normalize_integer(raw_data.get('Book')),
            'seats': self.normalizer.normalize_integer(raw_data.get('Seat')),
            'status': raw_data.get('PeriodStatus', 'Book'),
            'base_prices': base_prices,
            'end_prices': end_prices,
            'deposit': self.normalizer.normalize_price(raw_data.get('Deposit')),
            'deposit_end': self.normalizer.normalize_price(raw_data.get('Deposit_End')),
            'com_agent': self.normalizer.normalize_price(raw_data.get('ComAgent')),
            'com_agent_end': self.normalizer.normalize_price(raw_data.get('ComAgent_End')),
            'com_sale': self.normalizer.normalize_price(raw_data.get('ComSale')),
            'com_sale_end': self.normalizer.normalize_price(raw_data.get('ComSale_End')),
            'update_date': raw_data.get('UpdateDate'),
        }

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        """Map Zego flight data to standard format."""
        return {
            'provider': self.provider.id,
            'period_id': period.id if period else None,
            'airline_code': raw_data.get('AirlineCode', ''),
            'airline_name': raw_data.get('AirlineName', ''),
            'flight_no': raw_data.get('FlightNo', ''),
            'route': raw_data.get('Route', ''),
            'departure_time': self.normalizer.clean_flight_time(raw_data.get('DepartureTime')),
            'arrival_time': self.normalizer.clean_flight_time(raw_data.get('ArrivalTime')),
        }

    def map_itinerary_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """Map Zego itinerary data to standard format."""
        return {
            'provider': self.provider.id,
            'external_id': raw_data.get('ItinID', ''),
            'program_id': program_tour.id if program_tour else None,
            'day': self.normalizer.normalize_integer(raw_data.get('ItinDay')),
            'description': raw_data.get('ItinDes', ''),
            'hotel': raw_data.get('ItinHotel', ''),
            'hotel_star': raw_data.get('ItinHotelStar', ''),
            'breakfast': self.normalizer.normalize_boolean(raw_data.get('ItinBfast')),
            'breakfast_desc': raw_data.get('ItinBfastDes', ''),
            'lunch': self.normalizer.normalize_boolean(raw_data.get('ItinLunch')),
            'lunch_desc': raw_data.get('ItinLunchDes', ''),
            'dinner': self.normalizer.normalize_boolean(raw_data.get('ItinDnr')),
            'dinner_desc': raw_data.get('ItinDnrDes', ''),
        }


class UniqueInterMapper(ProviderMapper):
    """
    Unique Inter data mapper - complex transformations required.

    Unique Inter API is departure-centric with limited data.
    Many fields need to be extracted from title or set to defaults.
    """

    def __init__(self, provider: Provider):
        super().__init__(provider)
        self.normalizer = UniqueInterNormalizer()

    def map_tour_data(self, raw_data: Dict) -> Dict:
        """
        Map Unique Inter tour data to standard format.

        Unique Inter provides minimal tour data:
        - No direct country (extracted from title)
        - No flight schedules (only airline name)
        - No itineraries (in PDF/Word docs)
        - Limited pricing types
        """
        title = self.normalizer.normalize_text(raw_data.get('title', ''))
        days, nights = self.normalizer.extract_duration(title)
        country_name = self.normalizer.extract_country(title) or raw_data.get('Country', '')

        # Build URLs for documents
        base_url = "https://uniqueinterwholesale.com"
        word_path = raw_data.get('word', '')
        pdf_path = raw_data.get('pdf', '')

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('mainid', '')),
            'code': str(raw_data.get('mainid', '')),
            'name': title,
            'days': days,
            'nights': nights,
            'country': self._get_or_create_country(country_name),
            'country_name': country_name,
            'airline_name': raw_data.get('Airline', ''),
            'file_pdf': f"{base_url}/{pdf_path}" if pdf_path else '',
            'file_word': f"{base_url}/{word_path}" if word_path else '',
            'image_url': raw_data.get('jpg', ''),
            'highlight': raw_data.get('story', ''),
            # Data completeness - Unique Inter has limited data
            'has_flights': False,  # No flight schedules
            'has_itineraries': False,  # Itineraries in PDF only
            'has_full_pricing': False,  # Limited pricing types
            'data_quality_score': 60,  # Lower score due to missing data
        }

    def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        Map Unique Inter period data to standard format.

        Unique Inter provides basic pricing (adult, child, single).
        Missing pricing types are set to null.
        """
        # Build base_prices JSONField - only available prices
        base_prices = {
            'adult': self.normalizer.clean_price(raw_data.get('Adult')),
            'child': self.normalizer.clean_price(raw_data.get('Chd+B')),
            'single_bed': self.normalizer.clean_price(raw_data.get('Single')),
            # Other types not available - will be null
        }

        # Determine status from availability
        available = self.normalizer.normalize_integer(raw_data.get('AVBL'))
        if available <= 0:
            status = 'Soldout'
        elif available <= 5:
            status = 'Waitlist'
        else:
            status = 'Book'

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('ProductCode', '')),
            'code': raw_data.get('pid', ''),
            'program_id': program_tour.id if program_tour else None,
            'start_date': self.normalizer.normalize_date(raw_data.get('Date')),
            'end_date': self.normalizer.normalize_date(raw_data.get('ENDDate')),
            'country_name': raw_data.get('Country', ''),
            'airline_name': raw_data.get('Airline', ''),
            'group_size': self.normalizer.normalize_integer(raw_data.get('Size')),
            'booked': self.normalizer.normalize_integer(raw_data.get('Booking')),
            'seats': available,
            'status': status,
            'base_prices': base_prices,
            'deposit': self.normalizer.clean_price(raw_data.get('Deposit')),
            'com_agent': self.normalizer.clean_price(raw_data.get('com')),
        }

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        """
        Unique Inter doesn't provide flight data.

        This method is not implemented as Unique Inter only provides
        airline names, not flight schedules.
        """
        raise NotImplementedError(
            "Unique Inter does not provide flight schedule data. "
            "Only airline names are available in tour data."
        )

    def map_itinerary_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        Unique Inter doesn't provide itinerary data.

        Itineraries are only available in PDF/Word documents,
        not in the API response.
        """
        raise NotImplementedError(
            "Unique Inter does not provide itinerary data in API. "
            "Itineraries are only available in PDF/Word documents."
        )


class Go365Mapper(ProviderMapper):
    """
    Go365 data mapper - middle ground between Zego and Unique Inter.

    Go365 provides structured REST API but with less detail than Zego.
    """

    def __init__(self, provider: Provider):
        super().__init__(provider)
        self.normalizer = Go365Normalizer()

    def map_tour_data(self, raw_data: Dict) -> Dict:
        """
        Map Go365 tour data to standard format.

        Note: This is a placeholder implementation as Go365 API
        endpoints were returning 404 during testing.
        Adjust field mappings based on actual API response structure.
        """
        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('tour_id', '')),
            'code': raw_data.get('tour_code', ''),
            'name': raw_data.get('tour_name', ''),
            'days': self.normalizer.normalize_integer(raw_data.get('duration_days')),
            'nights': self.normalizer.normalize_integer(raw_data.get('duration_nights')),
            'country': self._get_or_create_country(raw_data.get('country_name')),
            'country_name': raw_data.get('country_name', ''),
            'airline_name': raw_data.get('airline', ''),
            'file_pdf': raw_data.get('pdf_url', ''),
            'image_url': raw_data.get('image_url', ''),
            'highlight': raw_data.get('description', ''),
            # Data completeness - Go365 likely has partial data
            'has_flights': True,  # May have partial flight data
            'has_itineraries': True,  # May have partial itineraries
            'has_full_pricing': False,  # Likely limited pricing
            'data_quality_score': 80,  # Middle ground
        }

    def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """Map Go365 period data to standard format."""
        # Placeholder - adjust based on actual API structure
        base_prices = {
            'adult': self.normalizer.normalize_price(raw_data.get('price_adult')),
            'child': self.normalizer.normalize_price(raw_data.get('price_child')),
        }

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('departure_id', '')),
            'code': raw_data.get('departure_code', ''),
            'program_id': program_tour.id if program_tour else None,
            'start_date': self.normalizer.normalize_date(raw_data.get('departure_date')),
            'end_date': self.normalizer.normalize_date(raw_data.get('return_date')),
            'base_prices': base_prices,
            'seats': self.normalizer.normalize_integer(raw_data.get('available_seats')),
            'status': raw_data.get('status', 'Book'),
        }

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        """Map Go365 flight data to standard format."""
        # Placeholder - adjust based on actual API structure
        return {
            'provider': self.provider.id,
            'period_id': period.id if period else None,
            'airline_name': raw_data.get('airline', ''),
            'flight_no': raw_data.get('flight_number', ''),
            'route': raw_data.get('route', ''),
        }

    def map_itinerary_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """Map Go365 itinerary data to standard format."""
        # Placeholder - adjust based on actual API structure
        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('itinerary_id', '')),
            'program_id': program_tour.id if program_tour else None,
            'day': self.normalizer.normalize_integer(raw_data.get('day_number')),
            'description': raw_data.get('description', ''),
            'hotel': raw_data.get('hotel_name', ''),
        }


class GenericMapper(ProviderMapper):
    """
    Generic mapper for providers without specific implementations.

    Provides basic field mapping with fallbacks for unknown providers.
    """

    def map_tour_data(self, raw_data: Dict) -> Dict:
        """
        Generic tour data mapping.

        Attempts to map common field names that might appear in
        various provider APIs.
        """
        # Try common field name variations
        external_id = (
            raw_data.get('id') or
            raw_data.get('tour_id') or
            raw_data.get('product_id') or
            raw_data.get('code') or
            ''
        )

        code = (
            raw_data.get('code') or
            raw_data.get('tour_code') or
            raw_data.get('product_code') or
            external_id
        )

        name = (
            raw_data.get('name') or
            raw_data.get('title') or
            raw_data.get('tour_name') or
            raw_data.get('product_name') or
            ''
        )

        return {
            'provider': self.provider.id,
            'external_id': str(external_id),
            'code': str(code),
            'name': name,
            'country': self._get_or_create_country(raw_data.get('country')),
            'country_name': raw_data.get('country', ''),
            'image_url': raw_data.get('image_url', '') or raw_data.get('image', ''),
            'highlight': raw_data.get('description', ''),
            # Unknown completeness
            'has_flights': True,
            'has_itineraries': True,
            'has_full_pricing': True,
            'data_quality_score': 50,  # Low score for unknown provider
        }

    def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """Generic period data mapping."""
        base_prices = {
            'adult': self.normalizer.normalize_price(
                raw_data.get('price') or
                raw_data.get('price_adult') or
                raw_data.get('adult_price')
            ),
        }

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('id') or raw_data.get('period_id', '')),
            'program_id': program_tour.id if program_tour else None,
            'start_date': self.normalizer.normalize_date(
                raw_data.get('start_date') or
                raw_data.get('departure_date') or
                raw_data.get('date')
            ),
            'end_date': self.normalizer.normalize_date(
                raw_data.get('end_date') or
                raw_data.get('return_date')
            ),
            'base_prices': base_prices,
        }

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        """Generic flight data mapping."""
        return {
            'provider': self.provider.id,
            'period_id': period.id if period else None,
            'airline_name': raw_data.get('airline', ''),
            'flight_no': raw_data.get('flight_number', ''),
            'route': raw_data.get('route', ''),
        }

    def map_itinerary_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """Generic itinerary data mapping."""
        return {
            'provider': self.provider.id,
            'program_id': program_tour.id if program_tour else None,
            'day': self.normalizer.normalize_integer(raw_data.get('day')),
            'description': raw_data.get('description', ''),
        }
