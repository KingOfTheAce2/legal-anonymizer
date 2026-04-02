"""
PII Pattern Detection Module

Comprehensive global PII detection patterns for:
- Email addresses
- Phone numbers (international formats)
- National IDs (all major countries)
- Passport numbers
- Credit cards (with Luhn validation)
- Bank accounts (IBAN, SWIFT, regional formats)
- IP addresses (IPv4 and IPv6)
- Dates (multiple formats including Asian)
- Addresses (global formats)
- Vehicle IDs / License plates
- Medical IDs
- URLs and usernames
- Tax IDs
- Currency amounts

This module provides backward compatibility with the original patterns.py.
All pattern lists and detection functions are exported for easy use.
"""

# Import base classes and functions
from .base import (
    PatternMatch,
    ALL_PATTERNS,
    detect_patterns,
    detect_with_validation,
    luhn_checksum,
    validate_iban,
    validate_dutch_bsn,
    validate_china_id,
    validate_singapore_nric,
    _compile_patterns,
)

def validate_credit_card(value: str) -> bool:
    """Return True if *value* passes the Luhn check (valid credit-card number)."""
    return luhn_checksum(value)

# Import all pattern lists for direct access
from .email import EMAIL_PATTERNS
from .phone import PHONE_PATTERNS
from .national_ids import NATIONAL_ID_PATTERNS, PASSPORT_PATTERNS
from .financial import CREDIT_CARD_PATTERNS, BANK_ACCOUNT_PATTERNS
from .addresses import (
    IP_ADDRESS_PATTERNS,
    DATE_PATTERNS,
    DATE_OF_BIRTH_PATTERNS,
    ADDRESS_PATTERNS,
    VEHICLE_PATTERNS,
    ONLINE_PATTERNS,
    MONEY_PATTERNS,
    TAX_ID_PATTERNS,
)
from .medical import MEDICAL_ID_PATTERNS

# Export all public names
__all__ = [
    # Classes
    "PatternMatch",
    # Pattern lists
    "EMAIL_PATTERNS",
    "PHONE_PATTERNS",
    "NATIONAL_ID_PATTERNS",
    "PASSPORT_PATTERNS",
    "CREDIT_CARD_PATTERNS",
    "BANK_ACCOUNT_PATTERNS",
    "IP_ADDRESS_PATTERNS",
    "DATE_PATTERNS",
    "DATE_OF_BIRTH_PATTERNS",
    "ADDRESS_PATTERNS",
    "VEHICLE_PATTERNS",
    "MEDICAL_ID_PATTERNS",
    "ONLINE_PATTERNS",
    "MONEY_PATTERNS",
    "TAX_ID_PATTERNS",
    # Collections
    "ALL_PATTERNS",
    # Functions
    "detect_patterns",
    "detect_with_validation",
    "luhn_checksum",
    "validate_iban",
    "validate_dutch_bsn",
    "validate_china_id",
    "validate_singapore_nric",
    "validate_credit_card",
    "_compile_patterns",
]
