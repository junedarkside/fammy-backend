"""
Centralized provider field mapping configurations.

This module provides a centralized configuration for mapping provider-specific
API field names to our standard model field names. This makes it easier to
see the complete mapping for each provider in one place.
"""

from typing import Dict, List, Optional


# =============================================================================
# PROVIDER FIELD MAPPINGS
# =============================================================================

PROVIDER_MAPPINGS = {
    'zego': {
        'tour': {
            # Direct 1:1 mappings
            'external_id': 'ProductID',
            'code': 'ProductCode',
            'name': 'ProductName',
            'days': 'Days',
            'nights': 'Nights',
            'country_code': 'CountryCode',
            'country_name': 'CountryName',
            'airline_code': 'AirlineCode',
            'airline_name': 'AirlineName',
            'file_pdf': 'FilePDF',
            'file_word': 'FileWord',
            'image_url': 'URLImage',
            'highlight': 'Highlight',
            'max_hotel_stars': 'MaxHotelStars',
            'min_hotel_stars': 'MinHotelStars',
            'plane_meals': 'PlaneMeals',
            'total_meals': 'TotalMeals',
            'locations': 'Locations',
        },
        'period': {
            'external_id': 'PeriodID',
            'code': 'PeriodCode',
            'start_date': 'PeriodStartDate',
            'end_date': 'PeriodEndDate',
            'bus': 'Bus',
            'country_name': 'CountryName',
            'airline_code': 'AirlineCode',
            'airline_name': 'AirlineName',
            'airport': 'Airport',
            'group_size': 'Groupsize',
            'booked': 'Book',
            'seats': 'Seat',
            'status': 'PeriodStatus',
            'deposit': 'Deposit',
            'deposit_end': 'Deposit_End',
            'com_agent': 'ComAgent',
            'com_agent_end': 'ComAgent_End',
            'com_sale': 'ComSale',
            'com_sale_end': 'ComSale_End',
            'update_date': 'UpdateDate',
            # Pricing fields (mapped to JSONField)
            'price_adult': 'Price',
            'price_child': 'Price_Child',
            'price_child_nb': 'Price_ChildNB',
            'price_infant': 'Price_Infant',
            'price_join_land': 'Price_JoinLand',
            'price_single_bed': 'Price_Single_Bed',
            'price_twin_bed': 'Price_Twin_Bed',
            'price_double_bed': 'Price_Double_Bed',
            'price_triple_bed': 'Price_Triple_Bed',
            'price_single_visa': 'Price_Single_Visa',
            'price_group_visa': 'Price_Group_Visa',
            'price_express_visa': 'Price_Express_Visa',
            'price_end_adult': 'Price_End',
            'price_end_child': 'Price_Child_End',
        },
        'flight': {
            'airline_code': 'AirlineCode',
            'airline_name': 'AirlineName',
            'flight_no': 'FlightNo',
            'route': 'Route',
            'departure_time': 'DepartureTime',
            'arrival_time': 'ArrivalTime',
        },
        'itinerary': {
            'external_id': 'ItinID',
            'day': 'ItinDay',
            'description': 'ItinDes',
            'hotel': 'ItinHotel',
            'hotel_star': 'ItinHotelStar',
            'breakfast': 'ItinBfast',
            'breakfast_desc': 'ItinBfastDes',
            'lunch': 'ItinLunch',
            'lunch_desc': 'ItinLunchDes',
            'dinner': 'ItinDnr',
            'dinner_desc': 'ItinDnrDes',
        },
    },

    'unique_inter': {
        'tour': {
            # Direct mappings
            'external_id': 'mainid',
            'code': 'mainid',  # Same field used for both
            'name': 'title',
            'country_name': 'Country',  # Actually category, not country
            'airline_name': 'Airline',
            'file_pdf': 'pdf',
            'file_word': 'word',
            'image_url': 'jpg',
            'highlight': 'story',
            # Extracted from title (not direct API fields)
            'days': None,  # Extracted from title
            'nights': None,  # Extracted from title
            'country': None,  # Extracted from title
        },
        'period': {
            'external_id': 'ProductCode',
            'code': 'pid',
            'start_date': 'Date',
            'end_date': 'ENDDate',
            'country_name': 'Country',
            'airline_name': 'Airline',
            'group_size': 'Size',
            'booked': 'Booking',
            'seats': 'AVBL',
            'deposit': 'Deposit',
            'com_agent': 'com',
            'com_sale': 'complus',
            'promotion': 'Pro',
            # Pricing fields (limited compared to Zego)
            'price_adult': 'Adult',
            'price_child': 'Chd+B',
            'price_single_bed': 'Single',
        },
        'flight': {
            # Not available - Unique Inter doesn't provide flight schedules
            # Only airline names are available in tour data
        },
        'itinerary': {
            # Not available - Unique Inter itineraries are in PDF/Word documents
        },
    },

    'go365': {
        'tour': {
            # Updated based on actual Go365 API response structure
            # API endpoint: https://api.kaikongservice.com
            #
            # NESTED FIELD MAPPINGS - IMPORTANT:
            # The dot notation below indicates nested extraction in Go365Mapper.map_tour_data()
            # These fields are correctly extracted and saved to the database.
            #
            # NOTE: The evaluation page may show these as "TODO - Need Mapping" because
            # it doesn't recognize dot notation as valid mappings. This is a UI limitation
            # of the evaluation tool, NOT an actual mapping issue.
            #
            # VERIFIED WORKING (2026-01-16):
            # ✓ file_pdf (100% populated)       - Extracted from tour_file object
            # ✓ file_word (100% populated)      - Extracted from tour_file.file_doc
            # ✓ airline_code (100% populated)   - Extracted from tour_airline object
            # ✓ airline_name (100% populated)   - Extracted from tour_airline object
            # ✓ country_name (100% populated)   - Extracted from tour_country[0] array
            # ⚠ country (FK) - Requires countries to be synced first via --countries-only
            #
            'external_id': 'tour_id',
            'code': 'tour_code',
            'name': 'tour_name',
            'days': 'tour_num_day',
            'nights': 'tour_num_night',
            'country_code': 'tour_country.country_code_2',  # Array[0] extraction
            'country_name': 'tour_country.country_name',    # Array[0] extraction
            'airline_code': 'tour_airline.airline_iata',    # Object extraction
            'airline_name': 'tour_airline.airline_name',    # Object extraction
            'file_pdf': 'tour_file.file_pdf',               # Object extraction
            'file_word': 'tour_file.file_doc',              # Object extraction (note: API uses 'file_doc')
            'image_url': 'tour_cover_image',
            'highlight': 'tour_description',
            'locations': 'tour_city',  # Array of cities
            'min_price': 'tour_price_start',
        },
        'period': {
            'external_id': 'period_id',
            'code': 'period_code',
            'start_date': 'period_date',
            'end_date': 'period_back',
            'seats': 'period_available',
            'booked': 'period_total - period_available',
            'status': 'period_visible_text',
            'price_adult': 'period_price_start',
            'airline_code': 'period_airline.airline_iata',
            'airline_name': 'period_airline.airline_name',
            'airport': 'period_airline.airport_iata',
            'commission': 'period_commission',
            'commission_special': 'period_commission_special',
        },
        'flight': {
            'airline_name': 'airline',
            'flight_no': 'flight_number',
            'route': 'route',
        },
        'itinerary': {
            'day': 'day_number',
            'description': 'description',
            'hotel': 'hotel_name',
        },
    },

    'checkingroup': {
        'tour': {
            # Based on CheckInGroupMapper implementation
            'external_id': 'id',
            'code': 'code',
            'name': 'name',
            'days': 'day',
            'nights': 'night',
            'file_pdf': 'pdf',
            'file_word': 'word',
            'image_url': 'banner',
            'highlight': 'highlight',
            'airline_name': 'vehicle',  # Format: "THAI AIRWAYS (TG)"
            'tour_type': 'type',
            'provider_created_at': 'createdAt',
            'provider_updated_at': 'updatedAt',
        },
        'period': {
            # Based on CheckIn Group API structure
            'external_id': 'id',
            'start_date': 'startPeriod',
            'end_date': 'endPeriod',
            'price_adult': 'price',
            'price_air_ticket': 'airTicketPrice',
            'full_price': 'fullprice',
            'service_fee': 'serviceFee',
        },
        'flight': {
            # Flight info available in remark field (text format)
        },
        'itinerary': {
            # Not available via API
        },
    },
}


# =============================================================================
# PRICING FIELD MAPPINGS
# =============================================================================

"""
Pricing structure for each provider.

All providers map to our standard pricing JSONField structure:
{
    'adult': Decimal,
    'child': Decimal,
    'child_nb': Decimal,
    'infant': Decimal,
    'join_land': Decimal,
    'single_bed': Decimal,
    'twin_bed': Decimal,
    'double_bed': Decimal,
    'triple_bed': Decimal,
    'single_visa': Decimal,
    'group_visa': Decimal,
    'express_visa': Decimal,
}
"""

PRICING_FIELD_MAPPINGS = {
    'zego': {
        'base_prices': {
            'adult': 'Price',
            'child': 'Price_Child',
            'child_nb': 'Price_ChildNB',
            'infant': 'Price_Infant',
            'join_land': 'Price_JoinLand',
            'single_bed': 'Price_Single_Bed',
            'twin_bed': 'Price_Twin_Bed',
            'double_bed': 'Price_Double_Bed',
            'triple_bed': 'Price_Triple_Bed',
            'single_visa': 'Price_Single_Visa',
            'group_visa': 'Price_Group_Visa',
            'express_visa': 'Price_Express_Visa',
        },
        'end_prices': {
            'adult': 'Price_End',
            'child': 'Price_Child_End',
        },
    },
    'unique_inter': {
        'base_prices': {
            'adult': 'Adult',
            'child': 'Chd+B',
            'single_bed': 'Single',
        },
        'end_prices': {},  # Not available
    },
    'go365': {
        'base_prices': {
            'adult': 'price_adult',
            'child': 'price_child',
        },
        'end_prices': {},  # Unknown
    },
}


# =============================================================================
# DATA COMPLETENESS EXPECTATIONS
# =============================================================================

"""
Define what data completeness each provider is expected to have.

This helps set the has_flights, has_itineraries, has_full_pricing flags
and calculate data_quality_score.
"""

PROVIDER_DATA_COMPLETENESS = {
    'zego': {
        'has_flights': True,
        'has_itineraries': True,
        'has_full_pricing': True,
        'expected_pricing_types': 12,  # Number of pricing types
        'data_quality_score': 100,  # Maximum score
    },
    'unique_inter': {
        'has_flights': False,  # No flight schedules
        'has_itineraries': False,  # Itineraries in PDF only
        'has_full_pricing': False,  # Only 3 pricing types
        'expected_pricing_types': 3,
        'data_quality_score': 60,  # Lower due to missing data
    },
    'go365': {
        'has_flights': True,  # May have partial flight data
        'has_itineraries': True,  # May have partial itineraries
        'has_full_pricing': False,  # Likely limited pricing
        'expected_pricing_types': 2,
        'data_quality_score': 80,  # Middle ground
    },
    'checkingroup': {
        'has_flights': True,  # Text format in remark field
        'has_itineraries': False,  # Not available via API
        'has_full_pricing': True,  # Complete pricing structure
        'expected_pricing_types': 4,  # price, airTicketPrice, fullprice, serviceFee
        'data_quality_score': 85,  # High quality data
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_provider_mapping(provider_code: str, entity_type: str) -> Dict:
    """
    Get field mappings for a specific provider and entity type.

    Args:
        provider_code: Provider code (e.g., 'zego', 'unique_inter')
        entity_type: Entity type ('tour', 'period', 'flight', 'itinerary')

    Returns:
        Dictionary of field mappings (model_field -> api_field)
    """
    provider_config = PROVIDER_MAPPINGS.get(provider_code.lower(), {})
    return provider_config.get(entity_type, {})


def get_pricing_mapping(provider_code: str, pricing_type: str = 'base_prices') -> Dict:
    """
    Get pricing field mappings for a provider.

    Args:
        provider_code: Provider code
        pricing_type: 'base_prices' or 'end_prices'

    Returns:
        Dictionary of pricing field mappings
    """
    provider_config = PRICING_FIELD_MAPPINGS.get(provider_code.lower(), {})
    return provider_config.get(pricing_type, {})


def get_data_completeness(provider_code: str) -> Dict:
    """
    Get expected data completeness for a provider.

    Args:
        provider_code: Provider code

    Returns:
        Dictionary with completeness flags and quality score
    """
    return PROVIDER_DATA_COMPLETENESS.get(
        provider_code.lower(),
        {
            'has_flights': True,
            'has_itineraries': True,
            'has_full_pricing': True,
            'expected_pricing_types': 0,
            'data_quality_score': 50,  # Default low score for unknown
        }
    )


def reverse_mapping(provider_code: str, entity_type: str) -> Dict:
    """
    Get reverse mapping (API field -> model field).

    Useful for parsing API responses when you know the API field names
    and want to find the corresponding model field names.

    Args:
        provider_code: Provider code
        entity_type: Entity type

    Returns:
        Dictionary of reverse field mappings (api_field -> model_field)
    """
    forward_mapping = get_provider_mapping(provider_code, entity_type)
    return {v: k for k, v in forward_mapping.items() if v is not None}


# =============================================================================
# DYNAMIC PROVIDER DISCOVERY
# =============================================================================

def get_available_providers(include_incomplete: bool = False) -> Dict[str, Dict[str, str]]:
    """
    Get all available providers from PROVIDER_MAPPINGS dynamically.

    This function uses PROVIDER_MAPPINGS keys as the single source of truth
    for available providers. Providers can exist in mappings before being in
    the database (during development).

    Args:
        include_incomplete: If True, include providers that are in mappings
                           but don't have completeness data yet.

    Returns:
        Dictionary of provider_code -> {name, code, status}
        where status is 'configured' or 'incomplete'
    """
    providers = {}

    for provider_code in PROVIDER_MAPPINGS.keys():
        # Check if provider has completeness data (is fully configured)
        is_configured = provider_code in PROVIDER_DATA_COMPLETENESS

        if not is_configured and not include_incomplete:
            continue

        # Generate display name from provider code
        display_name = provider_code.replace('_', ' ').title()

        providers[provider_code] = {
            'name': display_name,
            'code': provider_code,
            'status': 'configured' if is_configured else 'incomplete'
        }

    return providers


def is_provider_configured(provider_code: str) -> bool:
    """
    Check if a provider has complete configuration (mappings + completeness data).

    A provider is considered configured if:
    1. It exists in PROVIDER_MAPPINGS
    2. It has an entry in PROVIDER_DATA_COMPLETENESS

    Args:
        provider_code: Provider code to check

    Returns:
        True if provider is fully configured, False otherwise
    """
    return (
        provider_code.lower() in PROVIDER_MAPPINGS and
        provider_code.lower() in PROVIDER_DATA_COMPLETENESS
    )


# =============================================================================
# MAPPING VALIDATION
# =============================================================================

def validate_provider_mapping(provider_code: str) -> List[str]:
    """
    Validate that a provider has all required field mappings.

    Args:
        provider_code: Provider code to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check if provider exists in mappings
    if provider_code.lower() not in PROVIDER_MAPPINGS:
        errors.append(f"Provider '{provider_code}' not found in mappings")
        return errors

    provider_config = PROVIDER_MAPPINGS[provider_code.lower()]

    # Check required entities
    required_entities = ['tour', 'period']
    for entity in required_entities:
        if entity not in provider_config:
            errors.append(f"Missing '{entity}' entity mapping")

    # Check required tour fields
    required_tour_fields = ['external_id', 'code', 'name']
    tour_mapping = provider_config.get('tour', {})
    for field in required_tour_fields:
        if field not in tour_mapping:
            errors.append(f"Missing required tour field: '{field}'")

    # Check required period fields
    required_period_fields = ['external_id', 'start_date']
    period_mapping = provider_config.get('period', {})
    for field in required_period_fields:
        if field not in period_mapping:
            errors.append(f"Missing required period field: '{field}'")

    return errors
