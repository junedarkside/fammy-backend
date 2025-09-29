import logging
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from .models import Provider, Country, ProgramTour, Period, Flight, Itinerary, ProviderMeta
from django.db.utils import IntegrityError, DataError # Import specific DB errors
from django.conf import settings # For USE_TZ
from .api_service import APIServiceFactory,ZegoAPIService
from datetime import datetime


logger = logging.getLogger(__name__)


# Comprehensive Country name to ISO code mapping for normalization
COUNTRY_NAME_TO_ISO = {
    # Current Zego countries (maintaining compatibility)
    'jordan': 'JOR',
    'spain': 'ESP',
    'russia': 'RUS',
    'china': 'CHN',
    'hong kong': 'HKG',
    'taiwan': 'TWN',
    'myanmar': 'MMR',
    'egypt': 'EGY',
    'japan': 'JPN',
    'nepal': 'NPL',
    'mongolia': 'MNG',
    'england': 'GBR',
    'india': 'IND',
    'scandinavia': 'SCA',  # Custom region code
    'netherlands': 'NLD',
    'america': 'USA',
    'united states': 'USA',
    'europe': 'EUR',  # Custom region code
    'italy': 'ITA',
    'vietnam': 'VNM',
    'australia': 'AUS',
    'germany': 'DEU',
    'georgia': 'GEO',
    'switzerland': 'CHE',
    'korea': 'KOR',
    'south korea': 'KOR',
    'singapore': 'SGP',
    'turkiye': 'TUR',
    'turkey': 'TUR',
    'france': 'FRA',

    # Additional Asian countries
    'thailand': 'THA',
    'malaysia': 'MYS',
    'indonesia': 'IDN',
    'philippines': 'PHL',
    'cambodia': 'KHM',
    'laos': 'LAO',
    'brunei': 'BRN',
    'timor-leste': 'TLS',
    'east timor': 'TLS',
    'north korea': 'PRK',
    'macao': 'MAC',
    'macau': 'MAC',
    'afghanistan': 'AFG',
    'bangladesh': 'BGD',
    'bhutan': 'BTN',
    'maldives': 'MDV',
    'sri lanka': 'LKA',
    'pakistan': 'PAK',
    'uzbekistan': 'UZB',
    'kazakhstan': 'KAZ',
    'kyrgyzstan': 'KGZ',
    'tajikistan': 'TJK',
    'turkmenistan': 'TKM',
    'armenia': 'ARM',
    'azerbaijan': 'AZE',

    # European countries
    'united kingdom': 'GBR',
    'great britain': 'GBR',
    'uk': 'GBR',
    'scotland': 'GBR',
    'wales': 'GBR',
    'northern ireland': 'GBR',
    'ireland': 'IRL',
    'norway': 'NOR',
    'sweden': 'SWE',
    'denmark': 'DNK',
    'finland': 'FIN',
    'iceland': 'ISL',
    'poland': 'POL',
    'czech republic': 'CZE',
    'slovakia': 'SVK',
    'hungary': 'HUN',
    'romania': 'ROU',
    'bulgaria': 'BGR',
    'greece': 'GRC',
    'croatia': 'HRV',
    'slovenia': 'SVN',
    'bosnia and herzegovina': 'BIH',
    'serbia': 'SRB',
    'montenegro': 'MNE',
    'albania': 'ALB',
    'north macedonia': 'MKD',
    'macedonia': 'MKD',
    'kosovo': 'XKX',
    'moldova': 'MDA',
    'ukraine': 'UKR',
    'belarus': 'BLR',
    'lithuania': 'LTU',
    'latvia': 'LVA',
    'estonia': 'EST',
    'austria': 'AUT',
    'belgium': 'BEL',
    'luxembourg': 'LUX',
    'portugal': 'PRT',
    'andorra': 'AND',
    'monaco': 'MCO',
    'liechtenstein': 'LIE',
    'san marino': 'SMR',
    'vatican': 'VAT',
    'malta': 'MLT',
    'cyprus': 'CYP',

    # Middle Eastern countries
    'israel': 'ISR',
    'palestine': 'PSE',
    'lebanon': 'LBN',
    'syria': 'SYR',
    'iraq': 'IRQ',
    'iran': 'IRN',
    'saudi arabia': 'SAU',
    'united arab emirates': 'ARE',
    'uae': 'ARE',
    'kuwait': 'KWT',
    'qatar': 'QAT',
    'bahrain': 'BHR',
    'oman': 'OMN',
    'yemen': 'YEM',

    # African countries
    'south africa': 'ZAF',
    'nigeria': 'NGA',
    'kenya': 'KEN',
    'ethiopia': 'ETH',
    'tanzania': 'TZA',
    'uganda': 'UGA',
    'rwanda': 'RWA',
    'burundi': 'BDI',
    'democratic republic of congo': 'COD',
    'congo': 'COG',
    'cameroon': 'CMR',
    'ghana': 'GHA',
    'ivory coast': 'CIV',
    'senegal': 'SEN',
    'mali': 'MLI',
    'burkina faso': 'BFA',
    'niger': 'NER',
    'chad': 'TCD',
    'sudan': 'SDN',
    'south sudan': 'SSD',
    'libya': 'LBY',
    'tunisia': 'TUN',
    'algeria': 'DZA',
    'morocco': 'MAR',
    'madagascar': 'MDG',
    'mauritius': 'MUS',
    'seychelles': 'SYC',
    'zimbabwe': 'ZWE',
    'botswana': 'BWA',
    'namibia': 'NAM',
    'zambia': 'ZMB',
    'malawi': 'MWI',
    'mozambique': 'MOZ',
    'angola': 'AGO',

    # American countries
    'usa': 'USA',
    'united states of america': 'USA',
    'canada': 'CAN',
    'mexico': 'MEX',
    'guatemala': 'GTM',
    'belize': 'BLZ',
    'honduras': 'HND',
    'el salvador': 'SLV',
    'nicaragua': 'NIC',
    'costa rica': 'CRI',
    'panama': 'PAN',
    'cuba': 'CUB',
    'jamaica': 'JAM',
    'haiti': 'HTI',
    'dominican republic': 'DOM',
    'puerto rico': 'PRI',
    'bahamas': 'BHS',
    'barbados': 'BRB',
    'trinidad and tobago': 'TTO',
    'brazil': 'BRA',
    'argentina': 'ARG',
    'chile': 'CHL',
    'peru': 'PER',
    'colombia': 'COL',
    'venezuela': 'VEN',
    'ecuador': 'ECU',
    'bolivia': 'BOL',
    'paraguay': 'PRY',
    'uruguay': 'URY',
    'guyana': 'GUY',
    'suriname': 'SUR',
    'french guiana': 'GUF',

    # Oceania
    'new zealand': 'NZL',
    'fiji': 'FJI',
    'papua new guinea': 'PNG',
    'solomon islands': 'SLB',
    'vanuatu': 'VUT',
    'samoa': 'WSM',
    'tonga': 'TON',
    'palau': 'PLW',
    'micronesia': 'FSM',
    'marshall islands': 'MHL',
    'kiribati': 'KIR',
    'nauru': 'NRU',
    'tuvalu': 'TUV',

    # Popular travel destination variations
    'bali': 'IDN',  # Part of Indonesia
    'lombok': 'IDN',  # Part of Indonesia
    'phuket': 'THA',  # Part of Thailand
    'koh samui': 'THA',  # Part of Thailand
    'jeju': 'KOR',  # Part of South Korea
    'okinawa': 'JPN',  # Part of Japan
    'hokkaido': 'JPN',  # Part of Japan
    'honshu': 'JPN',  # Part of Japan
    'kyushu': 'JPN',  # Part of Japan
    'shikoku': 'JPN',  # Part of Japan
    'taiwan island': 'TWN',
    'formosa': 'TWN',  # Historical name for Taiwan
    'ceylon': 'LKA',  # Historical name for Sri Lanka
    'burma': 'MMR',  # Historical name for Myanmar
    'siam': 'THA',  # Historical name for Thailand
    'persia': 'IRN',  # Historical name for Iran
    'czechoslovakia': 'CZE',  # Historical, now Czech Republic
    'yugoslavia': 'SRB',  # Historical, mapping to Serbia
    'soviet union': 'RUS',  # Historical, mapping to Russia
    'ussr': 'RUS',  # Historical, mapping to Russia

    # Common variations and abbreviations
    'us': 'USA',
    'nz': 'NZL',
    'png': 'PNG',
    'drc': 'COD',

    # Regions (custom codes for travel industry)
    'balkans': 'BLK',  # Custom region code
    'baltics': 'BLT',  # Custom region code
    'central asia': 'CAS',  # Custom region code
    'southeast asia': 'SEA',  # Custom region code
    'middle east': 'MEA',  # Custom region code
    'east africa': 'EAF',  # Custom region code
    'west africa': 'WAF',  # Custom region code
    'southern africa': 'SAF',  # Custom region code
    'caribbean': 'CAR',  # Custom region code
    'central america': 'CAM',  # Custom region code
    'south america': 'SAM',  # Custom region code
    'north america': 'NAM',  # Custom region code
    'oceania': 'OCE',  # Custom region code
    'pacific islands': 'PAC',  # Custom region code
}


def normalize_country_name(name: str) -> str:
    """Normalize country name for deduplication"""
    if not name:
        return ''
    return name.lower().strip()


def get_iso_code(country_name: str) -> str:
    """Get ISO code for country name"""
    normalized = normalize_country_name(country_name)
    return COUNTRY_NAME_TO_ISO.get(normalized, '')


def safe_int(value: Any) -> int:
    """Safely convert value to integer"""
    if value is None or value == '':
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def convert_yn_to_bool(value: str) -> bool:
    """Convert Y/N string to boolean"""
    return str(value).upper() == 'Y'


def convert_meal_code_to_bool(value: str) -> bool:
    """Convert meal codes (Y/N/P) to boolean. Y=Yes, P=Provided, others=False"""
    return str(value).upper() in ['Y', 'P']


def parse_api_date(date_str: str) -> Optional[Any]:
    """Parse API date string to date object"""
    if not date_str:
        return None
    try:
        from datetime import datetime
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def parse_api_datetime(datetime_str: str) -> Optional[Any]:
    """Parse API datetime string to datetime object"""
    if not datetime_str:
        return None
    try:
        from datetime import datetime
        return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None


def parse_api_time(time_str: str) -> Optional[Any]:
    """Parse API time string to time object"""
    if not time_str:
        return None
    try:
        from datetime import datetime
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except (ValueError, TypeError):
        return None


def transform_pricing_data(period_data: Dict) -> tuple:
    """Transform individual price fields to JSONField structure"""
    base_prices = {
        'adult': safe_int(period_data.get('Price')),
        'child': safe_int(period_data.get('Price_Child')),
        'child_nb': safe_int(period_data.get('Price_ChildNB')),
        'infant': safe_int(period_data.get('Price_Infant')),
        'join_land': safe_int(period_data.get('Price_JoinLand')),
        'single_bed': safe_int(period_data.get('Price_Single_Bed')),
        'twin_bed': safe_int(period_data.get('Price_Twin_Bed')),
        'double_bed': safe_int(period_data.get('Price_Double_Bed')),
        'triple_bed': safe_int(period_data.get('Price_Triple_Bed')),
        'single_visa': safe_int(period_data.get('Price_Single_Visa')),
        'group_visa': safe_int(period_data.get('Price_Group_Visa')),
        'express_visa': safe_int(period_data.get('Price_Express_Visa'))
    }

    end_prices = {
        'adult': safe_int(period_data.get('Price_End')),
        'child': safe_int(period_data.get('Price_Child_End')),
        'child_nb': safe_int(period_data.get('Price_ChildNB_End')),
        'infant': safe_int(period_data.get('Price_Infant_End')),
        'join_land': safe_int(period_data.get('Price_JoinLand_End')),
        'single_bed': safe_int(period_data.get('Price_Single_Bed_End')),
        'twin_bed': safe_int(period_data.get('Price_Twin_Bed_End')),
        'double_bed': safe_int(period_data.get('Price_Double_Bed_End')),
        'triple_bed': safe_int(period_data.get('Price_Triple_Bed_End')),
        'single_visa': safe_int(period_data.get('Price_Single_Visa_End')),
        'group_visa': safe_int(period_data.get('Price_Group_Visa_End')),
        'express_visa': safe_int(period_data.get('Price_Express_Visa_End'))
    }

    return base_prices, end_prices


class DataSyncService:
    """Service to sync data from a Provider's API to local database"""

    def __init__(self, provider: Provider):
        self.provider = provider
        # Use APIServiceFactory to get the correct API service for the provider
        self.api_service = APIServiceFactory.create_service(provider)

    @transaction.atomic
    def sync_countries(self) -> Dict[str, int]:
        """
        Sync countries and their associated locations data from the API.
        """
        countries_data = self.api_service.get_countries() # type: Optional[List[Dict]]
        logger.debug(f"Raw countries_data from API for {self.provider.name}: {countries_data}") # Optional: for debugging
        if countries_data is None: # API call failed or returned None
            logger.error(f"Failed to fetch countries data for provider {self.provider.name} due to API error or no data.")
            return {'created': 0, 'updated': 0, 'errors': 1, 'message': 'API request to fetch countries failed or returned no data.'}
        if not countries_data: # Empty list returned by API
            logger.info(f"No countries found for provider {self.provider.name} from API.")
            return {'created': 0, 'updated': 0, 'errors': 0, 'message': 'No countries data returned by API.'}

        created_count = 0
        updated_count = 0

        # Counters for locations (optional, can be added to return dict if needed)
        # locations_created_count = 0
        # locations_updated_count = 0
        for country_data in countries_data:
            try:
                api_country_code = country_data.get('CountryCode')
                api_country_name = country_data.get('CountryName')
                api_country_content = country_data.get('CountryContent', '') # Default to empty string if missing

                if not api_country_code:
                    logger.warning(f"Skipping country data item due to missing 'CountryCode' for provider {self.provider.name}: {country_data}")
                    continue # Skip this record

                if not api_country_name:
                    # Country.name is not nullable and unique.
                    logger.warning(f"Skipping country data item for code '{api_country_code}' due to missing 'CountryName' for provider {self.provider.name}: {country_data}")
                    continue # Skip this record

                country, created = Country.objects.update_or_create(
                    provider=self.provider,
                    provider_code=api_country_code,
                    defaults={
                        'name': api_country_name,
                        'content': api_country_content,
                        'normalized_name': normalize_country_name(api_country_name),
                        'iso_code': get_iso_code(api_country_name),
                    }
                )

                if created:
                    created_count += 1
                    logger.info(f"Created country: {country.name} ({country.provider_code}) for provider {self.provider.name}")
                else:
                    updated_count += 1
                    logger.info(f"Updated country: {country.name} ({country.provider_code}) for provider {self.provider.name}")

                # Store locations as JSON in the country
                api_locations = country_data.get('Locations')
                if isinstance(api_locations, list):
                    country.locations = api_locations
                    country.save(update_fields=['locations'])
                elif api_locations is not None: # If 'Locations' key exists but is not a list
                    logger.warning(
                        f"Expected 'Locations' to be a list for country {api_country_code} "
                        f"from provider {self.provider.name}, but got {type(api_locations)}. Data: {api_locations}"
                    )

            except Exception as e:
                logger.error(f"Error syncing country {country_data.get('CountryCode', 'UNKNOWN_CODE')} for provider {self.provider.name}: {str(e)}. Data: {country_data}")

        return {'created': created_count, 'updated': updated_count, 'errors': 0}


    @transaction.atomic
    def sync_program_tours(self) -> Dict[str, int]:
        """Sync program tours data from API"""
        tours_data = self.api_service.get_program_tours() # type: Optional[List[Dict]]
        # logger.debug(f"Raw program_tours_data from API for {self.provider.name}: {tours_data}")
        if tours_data is None: # API call failed or returned None
            logger.error(f"Failed to fetch program tours data for provider {self.provider.name} due to API error or no data.")
            return {'created': 0, 'updated': 0, 'errors': 1, 'message': f'API request to fetch program tours for {self.provider.name} failed or returned no data.'}
        if not tours_data: # Empty list
            logger.info(f"No program tours found for provider {self.provider.name} from API.")
            return {'created': 0, 'updated': 0, 'errors': 0, 'message': 'No program tours data returned by API.'}

        created_count = 0
        updated_count = 0
        error_count = 0
        # logger.debug(f"Processing tours_data for {self.provider.name}: {tours_data}") # Optional: for verbose debugging
        for tour_data in tours_data:
            api_product_id = tour_data.get('ProductID') # Changed to PascalCase
            if not api_product_id:
                logger.warning(
                    f"Skipping tour data item due to missing 'ProductID' for provider {self.provider.name}. "
                    f"Data: {tour_data.get('ProductCode', 'N/A')}"
                )
                error_count += 1
                continue
            # logger.debug(f"Processing tour with ProductID: {api_product_id}")
            try:
                # 1. Determine Country for the tour
                api_country_code = tour_data.get('CountryCode') # Changed to PascalCase
                country_obj = None
                if api_country_code:
                    try:
                        country_obj = Country.objects.get(provider_code=api_country_code, provider=self.provider)
                    except Country.DoesNotExist:
                        logger.error(
                            f"Country with code '{api_country_code}' not found for provider {self.provider.name} "
                            f"when syncing tour with product_id '{api_product_id}'. This tour will not be linked to a country."
                        )
                elif tour_data.get('CountryName'): # Fallback logging, changed to PascalCase
                    logger.warning(
                        f"Tour with product_id '{api_product_id}' for provider {self.provider.name} is missing 'country_code', "
                        f"but has 'country_name': {tour_data.get('CountryName')}. Country linkage might be unreliable or skipped."
                    )
                # logger.debug(f"Country object for tour {api_product_id}: {country_obj}") # Optional: for debugging
                # 2. Prepare defaults for ProgramTour using helper functions
                defaults = {
                    'provider': self.provider,
                    'code': tour_data.get('ProductCode', ''),
                    'name': tour_data.get('ProductName', ''),
                    'days': safe_int(tour_data.get('Days')),
                    'nights': safe_int(tour_data.get('Nights')),
                    'country': country_obj,  # Link to Country object
                    'country_name': tour_data.get('CountryName', ''),
                    'airline_code': tour_data.get('AirlineCode', ''),
                    'airline_name': tour_data.get('AirlineName', ''),
                    'file_word': tour_data.get('FileWord'),
                    'file_pdf': tour_data.get('FilePDF'),
                    'image_url': tour_data.get('URLImage'),
                    'highlight': tour_data.get('Highlight'),
                    'max_hotel_stars': safe_int(tour_data.get('MaxHotelStars')),
                    'min_hotel_stars': safe_int(tour_data.get('MinHotelStars')),
                    'plane_meals': convert_yn_to_bool(tour_data.get('PlaneMeals', '')),
                    'total_meals': safe_int(tour_data.get('TotalMeals')),
                    'locations': tour_data.get('Locations', []),
                }

                tour, created = ProgramTour.objects.update_or_create(
                    provider=self.provider,
                    external_id=str(api_product_id),
                    defaults=defaults
                )

                # # Safety check for provider (if external_id is globally unique but we still want to ensure context)
                if tour.provider != self.provider:
                    logger.error(
                        f"Provider mismatch for tour with external_id {api_product_id}. "
                        f"Expected {self.provider.name}, found {tour.provider.name}. Skipping further processing for this tour."
                    )
                    error_count += 1
                    # Potentially delete the incorrectly attributed tour or mark it for review
                    # For now, we'll skip its related data sync
                    continue

                # Locations are already stored as JSON in the tour object (set in defaults above)
                # No additional location processing needed

                # # Sync other related data
                # # Pass tour-level Flights to _sync_periods, as periods in sample don't have their own flights
                self._sync_periods(tour, tour_data.get('Periods', []), tour_data.get('Flights', []))

                # Sync itineraries with fallback key checking
                itinerary_data = None
                possible_keys = ['Itinerary', 'Itineraries', 'ItineraryData', 'Itin', 'DayByDay']

                for key in possible_keys:
                    if key in tour_data and tour_data[key]:
                        itinerary_data = tour_data[key]
                        break

                if itinerary_data is None:
                    itinerary_data = []

                self._sync_itineraries(tour, itinerary_data)
                # Images are handled as single image_url field in the tour model

                if created:
                    created_count += 1
                    logger.info(f"Created tour: {tour.name} (ID: {api_product_id}) for provider {self.provider.name}")
                else:
                    updated_count += 1
                    logger.info(f"Updated tour: {tour.name} (ID: {api_product_id}) for provider {self.provider.name}")

            except Exception as e:
                error_count += 1
                # logger.error(
                #     f"Error syncing tour with product_id '{api_product_id}' for wholesaler {self.wholesaler.name}: {str(e)}. Data: {tour_data}"
                # )
        
        message = f"Program tour sync for {self.provider.name} completed."
        if error_count > 0:
            message += f" Encountered {error_count} errors during individual tour processing."
        return {'created': created_count, 'updated': updated_count, 'errors': error_count, 'message': message}

    @transaction.atomic
    def sync_single_program_tour_by_id(self, product_code_to_sync: str) -> Dict[str, Any]:
        """
        Syncs a single program tour by its ProductID from the API.
        """
        logger.info(f"Attempting to sync single program tour with ProductID: {product_code_to_sync} for wholesaler {self.wholesaler.name}")

        raw_tour_data_from_api = self.api_service.get_program_tour_details(product_code_to_sync) # type: Optional[Union[Dict, List]]
        if raw_tour_data_from_api is None:
            msg = f"API request for program tour ProductID {product_code_to_sync} failed or returned no data for wholesaler {self.wholesaler.name}."
            logger.error(msg)
            return {'created': 0, 'updated': 0, 'errors': 1, 'message': msg, 'product_id': product_code_to_sync}
        
        # Intermediate variable to hold the potential single tour data item
        tour_data_intermediate: Any = None 
        if isinstance(raw_tour_data_from_api, list):
            if raw_tour_data_from_api: # If the list is not empty
                tour_data_intermediate = raw_tour_data_from_api[0] # Get the first item
                if len(raw_tour_data_from_api) > 1:
                    logger.warning(f"API for single tour ProductID {product_code_to_sync} returned a list with multiple items ({len(raw_tour_data_from_api)}). Using the first item.")
            # If raw_tour_data_from_api is an empty list, tour_data_intermediate remains None
        elif isinstance(raw_tour_data_from_api, dict):
            tour_data_intermediate = raw_tour_data_from_api
        # If raw_tour_data_from_api was None or some other type, tour_data_intermediate remains None
        tour_data: Optional[Dict] = None
        if isinstance(tour_data_intermediate, dict): # Now, explicitly check if the extracted item is a dict
            tour_data = tour_data_intermediate
        elif tour_data_intermediate is not None: # If it was something, but not a dict (e.g. a list, string from API)
            logger.warning(
                f"API for single tour ProductID {product_code_to_sync} returned an item of unexpected type: {type(tour_data_intermediate)}. "
                f"Expected a dictionary. Data: {str(tour_data_intermediate)[:200]}" # Log a snippet
            )
        
        if not tour_data: # This covers: API returned None, empty list, list of non-dicts, non-dict/non-list, or empty dict from API
            msg = f"No valid tour data dictionary found by API for program tour ProductID {product_code_to_sync} for wholesaler {self.wholesaler.name}."
            if isinstance(raw_tour_data_from_api, list) and not raw_tour_data_from_api: # Specifically if API returned empty list
                logger.info(f"API for single tour ProductID {product_code_to_sync} returned an empty list for wholesaler {self.wholesaler.name}.")
            logger.warning(msg)
            return {'created': 0, 'updated': 0, 'errors': 1, 'message': msg, 'product_id': product_code_to_sync}
        api_product_code_from_data = tour_data.get('ProductCode')
        if api_product_code_from_data and str(api_product_code_from_data) != str(product_code_to_sync):
            msg = (f"API returned data for ProductID '{api_product_code_from_data}' when '{product_code_to_sync}' was requested "
                   f"for wholesaler {self.wholesaler.name}. Skipping.")
            logger.error(msg)
            return {'created': 0, 'updated': 0, 'errors': 1, 'message': msg, 'product_id': product_code_to_sync}
        try:
            # 1. Determine Country for the tour
            api_country_code = tour_data.get('CountryCode')
            country_obj = None
            if api_country_code:
                try:
                    country_obj = Country.objects.get(country_code=api_country_code, wholesaler=self.wholesaler)
                except Country.DoesNotExist:
                    logger.error(
                        f"Country with code '{api_country_code}' not found for wholesaler {self.wholesaler.name} "
                        f"when syncing tour with product_id '{product_code_to_sync}'. This tour will not be linked to a country."
                    )
            elif tour_data.get('CountryName'):
                logger.warning(
                    f"Tour with product_id '{product_code_to_sync}' for wholesaler {self.wholesaler.name} is missing 'country_code', "
                    f"but has 'country_name': {tour_data.get('CountryName')}. Country linkage might be unreliable or skipped."
                )

            def safe_int(value, default=0):
                if value is None: return default
                try: return int(value)
                except (ValueError, TypeError): return default

            # 2. Prepare defaults for ProgramTour
            defaults = {
                'wholesaler': self.wholesaler,
                'product_code': tour_data.get('ProductCode', ''),
                'product_name': tour_data.get('ProductName', ''),
                'days': safe_int(tour_data.get('Days')),
                'nights': safe_int(tour_data.get('Nights')),
                'country': country_obj,
                'airline_code': tour_data.get('AirlineCode', ''),
                'airline_name': tour_data.get('AirlineName', ''),
                'file_word': tour_data.get('FileWord'),
                'file_pdf': tour_data.get('FilePDF'),
                'url_image': tour_data.get('URLImage'),
                'highlight': tour_data.get('Highlight'),
                'max_hotel_stars': safe_int(tour_data.get('MaxHotelStars')),
                'min_hotel_stars': safe_int(tour_data.get('MinHotelStars')),
                'plane_meals': tour_data.get('PlaneMeals'),
                'total_meals': safe_int(tour_data.get('TotalMeals')),
                'update_date': timezone.now(),
            }

            tour, created = ProgramTour.objects.update_or_create(
                product_code=str(product_code_to_sync), # Use the requested product_id as the key
                defaults=defaults
            )

            if tour.wholesaler != self.wholesaler: # Should not happen if product_id is unique per wholesaler
                msg = (f"Wholesaler mismatch for tour with product_id {product_code_to_sync}. "
                       f"Expected {self.wholesaler.name}, found {tour.wholesaler.name}. Correcting wholesaler or aborting.")
                logger.error(msg)
                # Decide on correction strategy or abort
                tour.wholesaler = self.wholesaler # Force correct wholesaler
                tour.save(update_fields=['wholesaler'])
                # return {'created': 0, 'updated': 0, 'errors': 1, 'message': msg, 'product_id': product_code_to_sync}

            # 3. Sync visited_locations (M2M) - Reusing logic from the main sync method
            api_locations_list = tour_data.get('Locations', [])
            if tour.country and isinstance(api_locations_list, list):
                current_locations_to_set = []
                for loc_name_str in api_locations_list:
                    # ... (same location processing logic as in sync_program_tours)
                    loc_name_stripped = loc_name_str.strip()
                    if not loc_name_stripped: continue
                    field_max_length = Location._meta.get_field('location_name').max_length
                    if len(loc_name_stripped) > field_max_length: continue # Skip if too long
                    location_obj, _ = Location.objects.update_or_create(
                        wholesaler=self.wholesaler,
                        country_code=tour.country.country_code,
                        location_name=loc_name_stripped,
                        defaults={'country': tour.country, 'is_active': True}
                    )
                    current_locations_to_set.append(location_obj)
                tour.visited_locations.set(current_locations_to_set)

            # Sync other related data
            self._sync_periods(tour, tour_data.get('Periods', []), tour_data.get('Flights', []))
            self._sync_itineraries(tour, tour_data.get('Itinerary', []))
            self._sync_images(tour, tour_data.get('Images', []))

            action_taken = "created" if created else "updated"
            msg = f"Successfully {action_taken} program tour ProductID {product_code_to_sync} for wholesaler {self.wholesaler.name}."
            logger.info(msg)
            return {'created': 1 if created else 0, 'updated': 1 if not created else 0, 'errors': 0, 'message': msg, 'product_id': product_code_to_sync}

        except Exception as e:
            msg = f"Error syncing single program tour ProductID {product_code_to_sync} for wholesaler {self.wholesaler.name}: {str(e)}"
            logger.exception(msg) # Use logger.exception to include traceback
            return {'created': 0, 'updated': 0, 'errors': 1, 'message': msg, 'product_id': product_code_to_sync, 'details': str(e)}

    def _parse_api_datetime(self, datetime_str: Optional[str]) -> datetime:
        """Helper to parse datetime string from API, defaults to now() on failure."""
        if datetime_str:
            try:
                # Example format: "2025-01-24 07:12:34"
                dt_naive = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                if settings.USE_TZ:
                    return timezone.make_aware(dt_naive, timezone.get_default_timezone())
                return dt_naive
            except ValueError:
                logger.warning(f"Invalid datetime format '{datetime_str}'. Using current time.")
        return timezone.now()

    def _sync_periods(self, tour: ProgramTour, periods_data: List[Dict], tour_level_flights_data: List[Dict]):
        """Sync periods for a tour"""
        # Clear existing periods
        tour.periods.all().delete()

        for period_data in periods_data:
            api_period_id = period_data.get('PeriodID')
            api_period_code = period_data.get('PeriodCode', 'UNKNOWN_PERIOD_CODE')

            if not api_period_id:
                logger.warning(f"Skipping period with missing PeriodID for tour {tour.external_id}")
                continue

            try:
                # Transform pricing data to JSON structure
                base_prices, end_prices = transform_pricing_data(period_data)

                period = Period.objects.create(
                    provider=self.provider,
                    external_id=str(api_period_id),
                    program=tour,
                    code=period_data.get('PeriodCode', ''),
                    start_date=parse_api_date(period_data.get('PeriodStartDate')),
                    end_date=parse_api_date(period_data.get('PeriodEndDate')),
                    bus=period_data.get('Bus', ''),
                    country_name=period_data.get('CountryName', ''),
                    airline_code=period_data.get('AirlineCode', ''),
                    airline_name=period_data.get('AirlineName', ''),
                    airport=period_data.get('Airport', ''),
                    group_size=safe_int(period_data.get('GroupSize')),
                    booked=safe_int(period_data.get('Book')),
                    seats=safe_int(period_data.get('Seat')),
                    status=period_data.get('PeriodStatus', ''),
                    promotion=period_data.get('Promotion', ''),
                    base_prices=base_prices,
                    end_prices=end_prices,
                    deposit=safe_int(period_data.get('Deposit')),
                    deposit_end=safe_int(period_data.get('Deposit_End')),
                    com_agent=safe_int(period_data.get('ComAgent')),
                    com_agent_end=safe_int(period_data.get('ComAgent_End')),
                    com_sale=safe_int(period_data.get('ComSale')),
                    com_sale_end=safe_int(period_data.get('ComSale_End')),
                    update_date=parse_api_datetime(period_data.get('UpdateDate')),
                )

                # Sync flights for this period using tour_level_flights_data
                if tour_level_flights_data:
                    self._sync_flights(tour, period, tour_level_flights_data)

            except (IntegrityError, DataError) as db_err_period:
                logger.error(
                    f"Database error processing period for tour '{tour.code}' (ID: {tour.external_id}), "
                    f"PeriodCode: '{api_period_code}'. Error: {type(db_err_period).__name__} - {str(db_err_period)}. Period Data: {period_data}"
                )
                raise
            except Exception as ex_period:
                logger.error(
                    f"Unexpected error processing period for tour '{tour.code}' (ID: {tour.external_id}), "
                    f"PeriodCode: '{api_period_code}'. Error: {type(ex_period).__name__} - {str(ex_period)}. Period Data: {period_data}"
                )
                raise

    def _sync_flights(self, tour: ProgramTour, period: Period, flights_data: List[Dict]):
        """Sync flights for a tour and period"""
        for flight_data in flights_data:
            Flight.objects.create(
                provider=self.provider,
                program=tour,
                period=period,
                airline_code=flight_data.get('AirlineCode', ''),
                airline_name=flight_data.get('AirlineName', ''),
                flight_no=flight_data.get('FlightNo', ''),
                route=flight_data.get('Route', ''),
                departure_time=parse_api_time(flight_data.get('DepartureTime')),
                arrival_time=parse_api_time(flight_data.get('ArrivalTime')),
            )

    def _sync_itineraries(self, tour: ProgramTour, itineraries_data: List[Dict]):
        """Sync itineraries for a tour"""
        logger.debug(f"Syncing itineraries for tour {tour.external_id} ({tour.name}). Received {len(itineraries_data)} itinerary records.")

        # Validate input data
        if not itineraries_data:
            logger.info(f"No itinerary data received for tour {tour.external_id}. Clearing existing itineraries.")
            tour.itineraries.all().delete()
            return

        if not isinstance(itineraries_data, list):
            logger.warning(f"Invalid itinerary data format for tour {tour.external_id}. Expected list, got {type(itineraries_data)}. Skipping itinerary sync.")
            return

        # Clear existing itineraries
        existing_count = tour.itineraries.count()
        tour.itineraries.all().delete()
        logger.debug(f"Cleared {existing_count} existing itineraries for tour {tour.external_id}")

        created_count = 0
        skipped_count = 0

        for itin_data in itineraries_data:
            api_itin_id = itin_data.get('ItinID')
            itin_day = itin_data.get('ItinDay', 'Unknown')

            if not api_itin_id:
                logger.warning(f"Skipping itinerary with missing ItinID for tour {tour.external_id}, Day: {itin_day}")
                skipped_count += 1
                continue

            try:
                itinerary = Itinerary.objects.create(
                    provider=self.provider,
                    external_id=str(api_itin_id),
                    program=tour,
                    day=safe_int(itin_data.get('ItinDay')) or 1,
                    description=itin_data.get('ItinDes', ''),
                    hotel=itin_data.get('ItinHotel', ''),
                    hotel_star=itin_data.get('ItinHotelStar', ''),
                    breakfast=convert_meal_code_to_bool(itin_data.get('ItinBfast', '')),
                    breakfast_desc=itin_data.get('ItinBfastDes', ''),
                    lunch=convert_meal_code_to_bool(itin_data.get('ItinLunch', '')),
                    lunch_desc=itin_data.get('ItinLunchDes', ''),
                    dinner=convert_meal_code_to_bool(itin_data.get('ItinDnr', '')),
                    dinner_desc=itin_data.get('ItinDnrDes', ''),
                )
                created_count += 1
                logger.debug(f"Created itinerary Day {itinerary.day} for tour {tour.external_id} (ItinID: {api_itin_id})")

            except (IntegrityError, DataError) as db_err_itin:
                logger.error(
                    f"Database error processing itinerary for tour '{tour.code}' (ID: {tour.external_id}), "
                    f"Day: {itin_day}, ItinID: {api_itin_id}. Error: {type(db_err_itin).__name__} - {str(db_err_itin)}. Itinerary Data: {itin_data}"
                )
                skipped_count += 1
            except Exception as ex_itin:
                logger.error(
                    f"Unexpected error processing itinerary for tour '{tour.code}' (ID: {tour.external_id}), "
                    f"Day: {itin_day}, ItinID: {api_itin_id}. Error: {type(ex_itin).__name__} - {str(ex_itin)}. Itinerary Data: {itin_data}"
                )
                skipped_count += 1

        logger.info(f"Itinerary sync completed for tour {tour.external_id}: {created_count} created, {skipped_count} skipped")

    def _sync_images(self, tour: ProgramTour, images_data: List[Dict]):
        """Sync images for a tour"""
        # Clear existing images
        tour.images.all().delete()

        for image_data in images_data:
            ImageGallery.objects.create(
                program_tour=tour,
                image_url=image_data.get('ImageURL', ''), # Assuming PascalCase 'ImageURL'
                caption=image_data.get('Caption', ''),   # Assuming PascalCase 'Caption'
            )

    def check_for_updates(self) -> bool:
        """Check if there are updates available from API"""
        latest_data = self.api_service.get_latest_update_time()

        if not latest_data:
            return False

        api_latest_time = latest_data.get('latest_update_time')
        if not api_latest_time:
            return False

        # Compare with local latest update time
        local_latest = ProgramTour.objects.filter(
            wholesaler=self.wholesaler
        ).order_by('-update_date').first()

        if not local_latest:
            return True  # No local data, sync needed

        # Convert API time to datetime and compare
        try:
            api_time = datetime.fromisoformat(
                api_latest_time.replace('Z', '+00:00'))
            return api_time > local_latest.update_date
        except ValueError:
            logger.error(
                f"Invalid datetime format from API: {api_latest_time}")
            return False
