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
    Go365Normalizer,
    CheckInGroupNormalizer
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


class CheckInGroupMapper(ProviderMapper):
    """
    CheckIn Group data mapper.

    Handles transformation from CheckIn Group API format to standard model format.
    """

    def __init__(self, provider: Provider):
        super().__init__(provider)
        self.normalizer = CheckInGroupNormalizer()

    def map_tour_data(self, raw_data: Dict) -> Dict:
        """
        Map CheckIn Group tour data to standard format.

        API Fields → Model Fields:
        - id → external_id
        - code → code
        - name → name
        - day → days
        - night → nights
        - highlight → highlight
        - banner → image_url
        - pdf → file_pdf
        - word → file_word
        - vehicle → airline_name, airline_code
        - countries → country, country_name
        - type → tour_type
        - createdAt → provider_created_at
        - updatedAt → provider_updated_at
        """
        # Extract airline info from vehicle field
        # Format: "CHINA EASTERN AIRLINES (MU)" or "THAI AIRWAYS (TG)"
        vehicle = raw_data.get('vehicle', '')
        airline_name = ''
        airline_code = ''

        if vehicle:
            # Extract airline name (before the parenthesis)
            airline_name = vehicle.split('(')[0].strip() if '(' in vehicle else vehicle.strip()
            # Extract airline code (inside parenthesis)
            airline_code = vehicle.split('(')[1].rstrip(')') if '(' in vehicle else ''

        # Extract country info from countries array
        countries_list = raw_data.get('countries', [])
        country_name = ''
        country_code = ''
        country_icon_url = ''

        if countries_list and len(countries_list) > 0:
            country_data = countries_list[0]  # Use first country
            country_name = country_data.get('name', '')
            country_code = country_data.get('code', '')
            country_icon_url = country_data.get('icon', '')

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('id', '')),
            'code': raw_data.get('code', ''),
            'name': raw_data.get('name', ''),
            'days': self.normalizer.normalize_integer(raw_data.get('day')),
            'nights': self.normalizer.normalize_integer(raw_data.get('night')),
            'file_pdf': raw_data.get('pdf', ''),
            'file_word': raw_data.get('word', ''),
            'image_url': raw_data.get('banner', ''),
            'highlight': raw_data.get('highlight', ''),
            # Airline information
            'airline_name': airline_name,
            'airline_code': airline_code,
            # Country information - use CheckIn Group specific method
            'country': self._get_or_create_country_for_checkingroup(country_name, country_code, country_icon_url) if country_name else None,
            'country_name': country_name,  # Snapshot
            # Tour type and pricing
            'tour_type': raw_data.get('type', ''),
            # Note: starting_price and starting_price_air_ticket are calculated
            # after all periods are synced, not during tour mapping
            # Provider timestamps
            'provider_created_at': self.normalizer.normalize_datetime(raw_data.get('createdAt')),
            'provider_updated_at': self.normalizer.normalize_datetime(raw_data.get('updatedAt')),
            # Data completeness
            'has_flights': True,  # Text format in remark field
            'has_itineraries': False,  # Not available via API
            'has_full_pricing': True,  # Complete pricing structure
            'data_quality_score': 85,
        }

    def _get_or_create_country_for_checkingroup(
        self, country_name: str, country_code: str = None, icon_url: str = None
    ) -> Optional[Country]:
        """
        CheckIn Group specific: Get or create country.

        CheckIn Group provides ISO 2-letter codes (CN, JP, KR, etc.)
        This method creates Country records when they don't exist.

        Args:
            country_name: Country name from API (e.g., "จีน", "ญี่ปุ่น")
            country_code: ISO 2-letter code from API (e.g., "CN", "JP")
            icon_url: URL to country icon/flag image

        Returns:
            Country instance or None
        """
        if not country_name or not country_code:
            return None

        # Try to find existing country
        normalized = normalize_country_name(country_name)
        if not normalized:
            return None

        try:
            country = Country.objects.get(
                provider=self.provider,
                normalized_name=normalized
            )
            # Update icon_url if provided and different
            if icon_url and country.icon_url != icon_url:
                country.icon_url = icon_url
                country.save(update_fields=['icon_url'])
            return country
        except Country.DoesNotExist:
            # Create new country record
            iso_code_3 = self._convert_iso2_to_iso3(country_code)

            country = Country.objects.create(
                provider=self.provider,
                provider_code=country_code,
                name=country_name,
                normalized_name=normalized,
                iso_code=iso_code_3,
                icon_url=icon_url
            )
            return country

    def _convert_iso2_to_iso3(self, iso2_code: str) -> str:
        """
        Convert ISO 2-letter code to 3-letter code.

        Args:
            iso2_code: 2-letter ISO 3166-1 alpha-2 code (e.g., 'CN', 'JP', 'TH')

        Returns:
            3-letter ISO 3166-1 alpha-3 code (e.g., 'CHN', 'JPN', 'THA')

        Note:
            Common mappings for CheckIn Group destinations.
            Returns ISO2 code if not found in mapping.
        """
        iso2_to_iso3 = {
            'CN': 'CHN',  # China
            'JP': 'JPN',  # Japan
            'KR': 'KOR',  # South Korea
            'TH': 'THA',  # Thailand
            'TW': 'TWN',  # Taiwan
            'HK': 'HKG',  # Hong Kong
            'SG': 'SGP',  # Singapore
            'MY': 'MYS',  # Malaysia
            'VN': 'VNM',  # Vietnam
            'KH': 'KHM',  # Cambodia
            'LA': 'LAO',  # Laos
            'MM': 'MMR',  # Myanmar
            'ID': 'IDN',  # Indonesia
            'PH': 'PHL',  # Philippines
            'IN': 'IND',  # India
            'NP': 'NPL',  # Nepal
            'LK': 'LKA',  # Sri Lanka
            'BD': 'BGD',  # Bangladesh
            'MV': 'MDV',  # Maldives
            'BT': 'BTN',  # Bhutan
            'MO': 'MAC',  # Macau
            'AU': 'AUS',  # Australia
            'NZ': 'NZL',  # New Zealand
            'GB': 'GBR',  # United Kingdom
            'FR': 'FRA',  # France
            'DE': 'DEU',  # Germany
            'IT': 'ITA',  # Italy
            'ES': 'ESP',  # Spain
            'CH': 'CHE',  # Switzerland
            'AT': 'AUT',  # Austria
            'CZ': 'CZE',  # Czech Republic
            'GR': 'GRC',  # Greece
            'TR': 'TUR',  # Turkey
            'EG': 'EGY',  # Egypt
            'ZA': 'ZAF',  # South Africa
            'US': 'USA',  # United States
            'CA': 'CAN',  # Canada
            'BR': 'BRA',  # Brazil
            'AR': 'ARG',  # Argentina
            'MX': 'MEX',  # Mexico
            'RU': 'RUS',  # Russia
            'UA': 'UKR',  # Ukraine
            'SE': 'SWE',  # Sweden
            'NO': 'NOR',  # Norway
            'DK': 'DNK',  # Denmark
            'FI': 'FIN',  # Finland
            'PL': 'POL',  # Poland
            'NL': 'NLD',  # Netherlands
            'BE': 'BEL',  # Belgium
            'LU': 'LUX',  # Luxembourg
            'IE': 'IRL',  # Ireland
            'PT': 'PRT',  # Portugal
            'IS': 'ISL',  # Iceland
        }

        return iso2_to_iso3.get(iso2_code.upper(), iso2_code.upper())

    def map_period_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        Map CheckIn Group period data to standard format.

        Builds base_prices JSONField with all price types:
        - priceAdultDouble → adult_double
        - priceAdultTriple → adult_triple
        - priceChild → child
        - priceChildNoBed → child_no_bed
        - priceInfant → infant
        - priceSingleRoomAdd → single_supplement
        - priceAirTicket → air_ticket
        - serviceFeeVat → service_fee
        - price → price (general price)
        - priceForOne → price_for_one
        - beforePrice → before_price
        """
        # Convert Decimal to float for JSON serialization
        def to_float(value):
            """Convert Decimal to float, return None if value is None."""
            if value is None:
                return None
            return float(value)

        base_prices = {
            'adult_double': to_float(self.normalizer.normalize_price(raw_data.get('priceAdultDouble'))),
            'adult_triple': to_float(self.normalizer.normalize_price(raw_data.get('priceAdultTriple'))),
            'child': to_float(self.normalizer.normalize_price(raw_data.get('priceChild'))),
            'child_no_bed': to_float(self.normalizer.normalize_price(raw_data.get('priceChildNoBed'))),
            'infant': to_float(self.normalizer.normalize_price(raw_data.get('priceInfant'))),
            'single_supplement': to_float(self.normalizer.normalize_price(raw_data.get('priceSingleRoomAdd'))),
            'air_ticket': to_float(self.normalizer.normalize_price(raw_data.get('priceAirTicket'))),
            'service_fee': to_float(self.normalizer.normalize_price(raw_data.get('serviceFeeVat'))),
            # Add missing price fields
            'price': to_float(self.normalizer.normalize_price(raw_data.get('price'))),
            'price_for_one': to_float(self.normalizer.normalize_price(raw_data.get('priceForOne'))),
            'before_price': to_float(self.normalizer.normalize_price(raw_data.get('beforePrice'))),
            # Store CheckIn Group specific fields in base_prices._meta
            '_meta': {
                'group': raw_data.get('group'),
                'seat': raw_data.get('seat'),
                'available': raw_data.get('available'),
                'join': raw_data.get('join'),
                'flight_info': raw_data.get('flight', ''),
                # Booking deadlines (CheckIn Group specific)
                'expire1': raw_data.get('expire1'),
                'expire2': raw_data.get('expire2'),
                'expire3': raw_data.get('expire3'),
                # Additional period information
                'note': raw_data.get('note'),
                'remark': raw_data.get('remark'),
                'ticket_pnr': raw_data.get('ticketPnr'),
            }
        }

        # Map bus field (integer to string)
        # API uses 1 for Yes, 0 for No
        bus_value = raw_data.get('bus')
        if bus_value == 1:
            bus_mapped = 'Yes'
        elif bus_value == 0:
            bus_mapped = 'No'
        else:
            bus_mapped = ''

        return {
            'provider': self.provider.id,
            'external_id': str(raw_data.get('id', '')),
            'code': f"{program_tour.code}_{raw_data.get('id')}" if program_tour else '',
            'start_date': self.normalizer.normalize_date(raw_data.get('start')),
            'end_date': self.normalizer.normalize_date(raw_data.get('end')),
            'status': self.normalizer.normalize_status(raw_data.get('status')),
            'base_prices': base_prices,
            'deposit': self.normalizer.normalize_price(raw_data.get('deposit')),
            'com_agent': self.normalizer.normalize_price(raw_data.get('comAgent')),
            'com_sale': self.normalizer.normalize_price(raw_data.get('comSales')),
            'group_size': self.normalizer.normalize_integer(raw_data.get('group')),
            'seats': self.normalizer.normalize_integer(raw_data.get('seat')),
            'booked': self.normalizer.normalize_integer(raw_data.get('join')),
            'bus': bus_mapped,
        }

    def map_flight_data(self, raw_data: Dict, period=None) -> Dict:
        """
        CheckIn Group doesn't provide structured flight data.
        Flight info is text format in remark/flight fields.

        Raises NotImplementedError.
        """
        raise NotImplementedError(
            "CheckIn Group provides flight data as text only, not structured format. "
            "Flight information is available in period.extra['flight_info']"
        )

    def map_itinerary_data(self, raw_data: Dict, program_tour=None) -> Dict:
        """
        CheckIn Group doesn't provide itinerary data via API.
        Itineraries are only available in PDF/Word documents.

        Raises NotImplementedError.
        """
        raise NotImplementedError(
            "CheckIn Group does not provide itinerary data in API. "
            "Itineraries are only available in PDF/Word documents."
        )


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
