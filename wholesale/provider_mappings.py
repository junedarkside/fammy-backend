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
            # Note: Field names are placeholders based on common conventions
            # Adjust based on actual API response structure
            'external_id': 'tour_id',
            'code': 'tour_code',
            'name': 'tour_name',
            'days': 'duration_days',
            'nights': 'duration_nights',
            'country_name': 'country_name',
            'airline_name': 'airline',
            'file_pdf': 'pdf_url',
            'image_url': 'image_url',
            'highlight': 'description',
        },
        'period': {
            'external_id': 'departure_id',
            'code': 'departure_code',
            'start_date': 'departure_date',
            'end_date': 'return_date',
            'seats': 'available_seats',
            'status': 'status',
            'price_adult': 'price_adult',
            'price_child': 'price_child',
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
