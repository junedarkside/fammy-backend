"""
Field normalization utilities for transforming provider data to standard format.

This module provides reusable classes and functions for normalizing data
from different travel providers into a consistent format for the database models.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple
from datetime import datetime, date
import re


class FieldNormalizer:
    """
    Base class for normalizing provider data to standard format.

    Provides common normalization methods that can be used across
    different provider implementations.
    """

    @staticmethod
    def normalize_price(raw_value, price_type: str = 'adult') -> Optional[Decimal]:
        """
        Normalize various price formats to Decimal.

        Handles:
        - String prices: "25000", "25,000", "25.00"
        - Integer/float prices
        - Special formats like "25+1" (25 + 1 free)
        - Empty/null values

        Args:
            raw_value: Raw price value from API
            price_type: Type of price (for logging/debugging)

        Returns:
            Decimal price or None if invalid
        """
        if raw_value is None or raw_value == '':
            return None

        try:
            # Handle string prices
            if isinstance(raw_value, str):
                # Remove commas and whitespace
                cleaned = raw_value.replace(',', '').strip()

                # Handle special format "25+1" (25 + 1 free)
                if '+' in cleaned and not cleaned.startswith('+'):
                    # Sum the parts
                    parts = cleaned.split('+')
                    total = sum(Decimal(p) for p in parts if p.strip())
                    return total

                # Handle normal price strings
                return Decimal(cleaned)

            # Handle numeric prices
            if isinstance(raw_value, (int, float)):
                return Decimal(str(raw_value))

            # Handle Decimal
            if isinstance(raw_value, Decimal):
                return raw_value

        except (InvalidOperation, ValueError) as e:
            # Log error but don't raise - allow partial data
            pass

        return None

    @staticmethod
    def normalize_date(raw_value) -> Optional[date]:
        """
        Normalize various date formats to Python date.

        Handles:
        - ISO format: "2025-01-15"
        - String formats: "15/01/2025", "01-15-2025"
        - datetime objects
        - Empty/null values

        Args:
            raw_value: Raw date value from API

        Returns:
            date object or None if invalid
        """
        if raw_value is None or raw_value == '':
            return None

        try:
            # Already a date object
            if isinstance(raw_value, date):
                return raw_value

            # Parse string dates
            if isinstance(raw_value, str):
                raw_value = raw_value.strip()

                # Try ISO format first (most common)
                try:
                    return datetime.fromisoformat(raw_value).date()
                except ValueError:
                    pass

                # Try common formats
                formats = [
                    '%Y-%m-%d',      # ISO: 2025-01-15
                    '%d/%m/%Y',      # European: 15/01/2025
                    '%m-%d-%Y',      # US: 01-15-2025
                    '%d-%m-%Y',      # European: 15-01-2025
                    '%Y/%m/%d',      # ISO with slashes: 2025/01/15
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(raw_value, fmt).date()
                    except ValueError:
                        continue

        except (ValueError, TypeError):
            pass

        return None

    @staticmethod
    def normalize_boolean(raw_value) -> Optional[bool]:
        """
        Normalize various boolean formats to Python bool.

        Handles:
        - Y/N strings (common in travel APIs)
        - true/false strings
        - 1/0 integers
        - Boolean values
        - Empty/null values

        Args:
            raw_value: Raw boolean value from API

        Returns:
            bool or None if invalid
        """
        if raw_value is None or raw_value == '':
            return None

        # Handle boolean
        if isinstance(raw_value, bool):
            return raw_value

        # Handle Y/N (common in travel industry)
        if isinstance(raw_value, str):
            raw_value = raw_value.strip().upper()
            if raw_value in ['Y', 'YES', 'TRUE']:
                return True
            elif raw_value in ['N', 'NO', 'FALSE']:
                return False

        # Handle integers
        if isinstance(raw_value, int):
            return bool(raw_value)

        return None

    @staticmethod
    def normalize_integer(raw_value, default: int = 0) -> int:
        """
        Normalize various integer formats to Python int.

        Args:
            raw_value: Raw integer value from API
            default: Default value if conversion fails

        Returns:
            int value or default
        """
        if raw_value is None or raw_value == '':
            return default

        try:
            if isinstance(raw_value, str):
                # Remove commas and whitespace
                cleaned = raw_value.replace(',', '').strip()
                return int(float(cleaned))  # Handle "25.0" as 25
            return int(raw_value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def normalize_text(raw_value) -> str:
        """
        Normalize text by removing artifacts.

        Handles:
        - Removing \r\n and extra whitespace
        - Stripping leading/trailing whitespace
        - Empty/null values

        Args:
            raw_value: Raw text value from API

        Returns:
            Cleaned string or empty string
        """
        if raw_value is None:
            return ''

        if not isinstance(raw_value, str):
            return str(raw_value)

        # Remove common artifacts
        cleaned = raw_value.replace('\r\n', ' ')
        cleaned = cleaned.replace('\n', ' ')
        cleaned = cleaned.replace('\r', ' ')

        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())

        return cleaned.strip()


class UniqueInterNormalizer(FieldNormalizer):
    """
    Unique Inter specific normalizations.

    Handles the specific data format quirks of Unique Inter Wholesale API.
    """

    @staticmethod
    def extract_duration(title: str) -> Tuple[int, int]:
        """
        Extract days and nights from tour title.

        Unique Inter titles often contain duration information like:
        - "Tour Name 8 Days 7 Nights"
        - "Tour Name 8D7N"
        - "Tour Name (8 Days)"

        Args:
            title: Tour title string

        Returns:
            Tuple of (days, nights) - (0, 0) if not found
        """
        if not title:
            return 0, 0

        title = title.upper()
        days, nights = 0, 0

        # Try to extract "X Days Y Nights" pattern
        pattern = r'(\d+)\s*DAYS?\s*(\d+)\s*NIGHTS?'
        match = re.search(pattern, title)
        if match:
            days = int(match.group(1))
            nights = int(match.group(2))
            return days, nights

        # Try to extract "XD YN" pattern
        pattern = r'(\d+)\s*D\s*(\d+)\s*N'
        match = re.search(pattern, title)
        if match:
            days = int(match.group(1))
            nights = int(match.group(2))
            return days, nights

        # Try to extract just days
        pattern = r'(\d+)\s*DAYS?'
        match = re.search(pattern, title)
        if match:
            days = int(match.group(1))
            nights = days - 1  # Assume nights = days - 1
            return days, nights

        return days, nights

    @staticmethod
    def extract_country(title: str) -> str:
        """
        Extract country name from Unique Inter title.

        Unique Inter uses structured title formats like:
        - "UI_TOURCODE_CountryName Tour Description"
        - "TourCode-CountryName-Tour Name"

        Args:
            title: Tour title string

        Returns:
            Extracted country name or empty string
        """
        if not title:
            return ''

        # Try underscore format: UI_CODE_CountryName
        if '_' in title:
            parts = title.split('_')
            if len(parts) >= 3:
                potential_country = parts[2].strip()
                # Remove tour description if present
                if ' ' in potential_country:
                    potential_country = potential_country.split()[0]
                if potential_country:
                    return potential_country

        # Try dash format: Code-CountryName-Description
        if '-' in title:
            parts = title.split('-')
            if len(parts) >= 2:
                potential_country = parts[1].strip()
                if potential_country:
                    return potential_country

        return ''

    @staticmethod
    def clean_price(raw_price: str) -> Optional[Decimal]:
        """
        Handle Unique Inter special price formats.

        Unique Inter sometimes uses formats like:
        - "25+1" (25 people + 1 free)
        - "25,000"
        - "25000"

        Args:
            raw_price: Raw price string from API

        Returns:
            Decimal price or None if invalid
        """
        return FieldNormalizer.normalize_price(raw_price)


class ZegoNormalizer(FieldNormalizer):
    """
    Zego specific normalizations.

    Zego API has relatively clean data, but this class provides
    Zego-specific normalization if needed.
    """

    @staticmethod
    def clean_flight_time(raw_time: str) -> Optional[str]:
        """
        Normalize flight time format.

        Zego returns times in various formats:
        - "14:30"
        - "2:30 PM"
        - "1430"

        Args:
            raw_time: Raw time string from API

        Returns:
            Normalized time string (HH:MM) or None
        """
        if not raw_time:
            return None

        try:
            # Already in correct format
            if ':' in raw_time:
                return raw_time.strip()

            # Try military time (1430 -> 14:30)
            if len(raw_time) == 4 and raw_time.isdigit():
                return f"{raw_time[:2]}:{raw_time[2:]}"

        except (ValueError, AttributeError):
            pass

        return None


class Go365Normalizer(FieldNormalizer):
    """
    Go365 specific normalizations.

    Handles Go365 API response formats and multi-language content.
    """

    @staticmethod
    def extract_language(content: str) -> Tuple[str, str]:
        """
        Detect language and extract text content.

        Go365 returns multi-language content, this helps separate
        language from actual content.

        Args:
            content: Raw content string

        Returns:
            Tuple of (language_code, cleaned_content)
        """
        if not content:
            return 'en', ''

        # Default to English
        language = 'en'
        cleaned = FieldNormalizer.normalize_text(content)

        return language, cleaned

    @staticmethod
    def clean_flight_time(raw_time: str) -> Optional[str]:
        """
        Normalize flight time format.

        Go365 returns times in various formats:
        - "14:30"
        - "2:30 PM"
        - "1430"

        Args:
            raw_time: Raw time string from API

        Returns:
            Normalized time string (HH:MM) or None
        """
        if not raw_time:
            return None

        try:
            # Already in correct format
            if ':' in raw_time:
                return raw_time.strip()

            # Try military time (1430 -> 14:30)
            if len(raw_time) == 4 and raw_time.isdigit():
                return f"{raw_time[:2]}:{raw_time[2:]}"

        except (ValueError, AttributeError):
            pass

        return None


class CheckInGroupNormalizer(FieldNormalizer):
    """
    CheckIn Group specific normalizations.

    Handles CheckIn Group API response formats including:
    - ISO date format (YYYY-MM-DD)
    - ISO datetime format (YYYY-MM-DDTHH:MM:SSZ)
    - Multiple price types
    - Status normalization (Open/Closed/Waiting/Cancel)
    """

    @staticmethod
    def normalize_datetime(raw_datetime: str) -> Optional[datetime]:
        """
        Normalize CheckIn Group datetime values.

        CheckIn Group returns ISO 8601 format: 2025-11-28T03:17:40.000000Z

        Args:
            raw_datetime: Raw datetime string from API

        Returns:
            datetime object or None if invalid
        """
        if not raw_datetime:
            return None

        try:
            # Parse ISO 8601 datetime
            return datetime.fromisoformat(raw_datetime.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def normalize_status(raw_status: str) -> str:
        """
        Normalize CheckIn Group status values.

        Maps API statuses to standard values:
        - 'Open' -> 'Book'
        - 'Closed' -> 'Soldout'
        - 'Waiting' -> 'Waitlist'
        - 'Cancel' -> 'Cancelled'

        Args:
            raw_status: Raw status string from API

        Returns:
            Normalized status string
        """
        if not raw_status:
            return 'Book'

        status_map = {
            'open': 'Book',
            'closed': 'Soldout',
            'waiting': 'Waitlist',
            'cancel': 'Cancelled',
        }

        normalized = raw_status.strip().lower()
        return status_map.get(normalized, raw_status)

    @staticmethod
    def extract_location(tour_name: str) -> str:
        """
        Extract location from Thai tour name.

        CheckIn Group tour names contain location info like:
        - "จางเจียเจี้ย-เมืองโบราณเฟิ่งหวง..."

        Args:
            tour_name: Thai tour name

        Returns:
            Extracted location or empty string
        """
        if not tour_name:
            return ''

        # Common Thai location keywords
        locations = ['จางเจียเจี้ย', 'ปักกิ่ง', 'ฮ่องกง', 'เกาหลี', 'ญี่ปุ่น',
                    'ไทเป', 'เวียดนาม', 'สิงคโปร์', 'มาเลเซีย']

        for location in locations:
            if location in tour_name:
                return location

        return ''


class FieldNormalizerFactory:
    """
    Factory class for creating appropriate normalizers based on provider.

    This factory is used when implementing Path 2 (REUSE_WITH_NORMALIZER)
    of the post-evaluation implementation plan.
    """

    @staticmethod
    def create_normalizer(provider_code: str, target_adapter: str) -> FieldNormalizer:
        """
        Create a normalizer for transforming provider data to target adapter format.

        Args:
            provider_code: The new provider's code
            target_adapter: The adapter to normalize to (e.g., 'checkingroup', 'zego')

        Returns:
            Appropriate normalizer instance

        Raises:
            ValueError: If target_adapter is not supported
        """
        # Return existing normalizers for known providers
        normalizer_map = {
            'zego': ZegoNormalizer(),
            'unique_inter': UniqueInterNormalizer(),
            'go365': Go365Normalizer(),
            'checkingroup': CheckInGroupNormalizer(),
        }

        if target_adapter in normalizer_map:
            return normalizer_map[target_adapter]

        # Return base normalizer for unknown adapters
        return FieldNormalizer()
