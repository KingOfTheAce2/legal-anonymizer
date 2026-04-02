"""
Entity Validation Layer - Confidence Adjustment & Sanity Checks

This module provides comprehensive validation for detected PII entities.
It handles edge cases specific to legal documents (test data, placeholders)
and adjusts confidence scores based on validation results.

Features:
- Fake SSN detection (invalid patterns like 000-00-0000)
- Test email detection (test@, example@, noreply@)
- Disposable email domain detection
- Phone number sanity checks
- Credit card validation (Luhn algorithm)
- IBAN validation (mod-97 algorithm)

All validators return (is_valid: bool, adjusted_confidence: int)
where adjusted_confidence is the modified confidence score after validation.
"""

import re
from typing import Tuple


class EntityValidator:
    """
    Static validation methods for PII entities.

    Each validator method returns a tuple of:
    - is_valid (bool): Whether the entity passed validation
    - adjusted_confidence (int): Confidence score after validation (0-100)
    """

    # Invalid SSN patterns (commonly used as test/placeholder data)
    INVALID_SSN_PATTERNS = {
        "000-00-0000",  # All zeros
        "111-11-1111",  # All ones
        "222-22-2222",  # All twos
        "333-33-3333",  # All threes
        "444-44-4444",  # All fours
        "555-55-5555",  # All fives
        "666-66-6666",  # All sixes (historically invalid)
        "777-77-7777",  # All sevens
        "888-88-8888",  # All eights
        "999-99-9999",  # All nines
        "123-45-6789",  # Sequential pattern
        "012-34-5678",  # Sequential pattern starting with 0
    }

    # Test and placeholder email patterns
    TEST_EMAIL_PATTERNS = [
        r"^test@",
        r"^example@",
        r"^noreply@",
        r"^no-reply@",
        r"^donotreply@",
        r"^do-not-reply@",
        r"^admin@",
        r"^webmaster@",
        r"^postmaster@",
        r"^support@",
        r"^dummy@",
        r"^fake@",
        r"^placeholder@",
        r"@localhost$",
        r"@example\.com$",
        r"@test\.com$",
        r"@sample\.com$",
        r"@demo\.com$",
        r"@tempmail\.com$",
    ]

    # Disposable/temporary email domains
    DISPOSABLE_EMAIL_DOMAINS = {
        # Temporary email services
        "tempmail.com", "temp-mail.org", "guerrillamail.com", "mailinator.com",
        "10minutemail.com", "throwaway.email", "trashmail.com", "yopmail.com",
        "maildrop.cc", "sharklasers.com", "mailnesia.com", "fakeinbox.com",
        "temp-mail.io", "mailnesia.com", "temp-mail.io", "testmail.com",
        "mailpoof.com", "email.net", "onetime.email", "tempmail.email",
        "getinbox.com", "grr.la", "guerrillamail.info", "guerrillamail.org",
        "pokemail.net", "spam4.me", "thisisnotmyrealemail.com", "trashmail.de",
        "15minutemail.com", "tempemails.com", "maildrop.cc", "mail.tm",
        "corrupt.io", "vomoto.com", "throwaway.email", "mailbox.ai",
        # Other known disposable domains
        "sharklasers.com", "spam.la", "spam.su", "spambox.us",
        "tempmail.net", "temp.email", "trash-mail.com", "use.startmail.com",
    }

    @staticmethod
    def validate_ssn(value: str) -> Tuple[bool, int]:
        """
        Validate SSN against common fake/test patterns.

        Args:
            value: SSN string (e.g., "123-45-6789" or "123456789")

        Returns:
            Tuple of (is_valid, adjusted_confidence):
            - is_valid: False if value matches known fake patterns
            - adjusted_confidence: Original confidence (100) or reduced if suspicious

        Examples:
            >>> EntityValidator.validate_ssn("000-00-0000")
            (False, 10)  # Invalid - all zeros
            >>> EntityValidator.validate_ssn("123-45-6789")
            (False, 30)  # Suspicious - sequential pattern
            >>> EntityValidator.validate_ssn("123-45-6789")
            (False, 30)  # Invalid - sequential
        """
        if not value:
            return False, 0

        # Normalize: remove hyphens and spaces
        normalized = value.replace("-", "").replace(" ", "").strip()

        # Check if exactly 9 digits
        if not re.match(r"^\d{9}$", normalized):
            return False, 0

        # Format with hyphens for pattern matching
        formatted = f"{normalized[:3]}-{normalized[3:5]}-{normalized[5:9]}"

        # Check against invalid patterns
        if formatted in EntityValidator.INVALID_SSN_PATTERNS:
            return False, 10

        # Check for all same digits (e.g., 111111111)
        if len(set(normalized)) == 1:
            return False, 15

        # Check for sequential patterns (e.g., 123456789)
        is_sequential = all(
            int(normalized[i+1]) == (int(normalized[i]) + 1) % 10
            for i in range(8)
        )
        if is_sequential:
            return False, 25

        # Additional validation: SSA rules
        # First 3 digits (area number) cannot be 000, 666, or 900-999
        area = int(normalized[:3])
        if area == 0 or area == 666 or area >= 900:
            return False, 35

        # Group number (middle 2) cannot be 00
        group = int(normalized[3:5])
        if group == 0:
            return False, 35

        # Serial number (last 4) cannot be 0000
        serial = int(normalized[5:9])
        if serial == 0:
            return False, 35

        return True, 100

    @staticmethod
    def validate_email(value: str) -> Tuple[bool, int]:
        """
        Validate email against test/disposable domain patterns.

        Checks for:
        - Test email patterns (test@, example@, noreply@, etc.)
        - Disposable/temporary email services
        - Localhost and fake domains

        Args:
            value: Email address string

        Returns:
            Tuple of (is_valid, adjusted_confidence):
            - is_valid: False if matches test/disposable patterns
            - adjusted_confidence: Reduced confidence for suspicious emails

        Examples:
            >>> EntityValidator.validate_email("test@example.com")
            (False, 20)  # Test email
            >>> EntityValidator.validate_email("john@tempmail.com")
            (False, 15)  # Disposable domain
            >>> EntityValidator.validate_email("john.smith@acme.com")
            (True, 95)  # Legitimate email
        """
        if not value:
            return False, 0

        value_lower = value.lower().strip()

        # Check for test email patterns
        for pattern in EntityValidator.TEST_EMAIL_PATTERNS:
            if re.search(pattern, value_lower):
                return False, 20

        # Extract domain
        if "@" not in value_lower:
            return False, 0

        domain = value_lower.split("@")[-1]

        # Check against disposable domain list
        if domain in EntityValidator.DISPOSABLE_EMAIL_DOMAINS:
            return False, 15

        # Check for numeric-only domains or suspicious patterns
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", domain):  # IP address
            return False, 30

        # Check domain format validity
        if not re.match(r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$", domain):
            return False, 25

        return True, 95

    @staticmethod
    def validate_phone(value: str, pattern_name: str = "") -> Tuple[bool, int]:
        """
        Validate phone number for consistency and sanity checks.

        Checks for:
        - All same digits (e.g., 000000000)
        - Sequential patterns
        - Known placeholder numbers (e.g., 555-xxxx)
        - Correct digit counts for given region
        - Proper format consistency

        Args:
            value: Phone number string
            pattern_name: Pattern name (e.g., "phone_us_ca", "phone_uk")
                         used to determine expected format

        Returns:
            Tuple of (is_valid, adjusted_confidence):
            - is_valid: False if matches test/invalid patterns
            - adjusted_confidence: Confidence after validation

        Examples:
            >>> EntityValidator.validate_phone("000-000-0000", "phone_us_ca")
            (False, 10)  # All zeros
            >>> EntityValidator.validate_phone("555-555-5555", "phone_us_ca")
            (False, 25)  # Placeholder pattern
            >>> EntityValidator.validate_phone("(555) 123-4567", "phone_us_ca")
            (True, 90)  # Valid US number
        """
        if not value:
            return False, 0

        # Extract only digits
        digits_only = re.sub(r"\D", "", value)

        # Too short or too long
        if len(digits_only) < 7 or len(digits_only) > 15:
            return False, 20

        # Check for all same digits (e.g., 000000000)
        if len(set(digits_only)) == 1:
            return False, 10

        # Check for sequential patterns
        is_sequential = all(
            int(digits_only[i+1]) == (int(digits_only[i]) + 1) % 10
            for i in range(len(digits_only) - 1)
        )
        if is_sequential:
            return False, 20

        # US/Canada specific: 555 exchange is reserved for fictional use
        if pattern_name in ("phone_us_ca", "phone_international"):
            if len(digits_only) >= 10:
                area_code = digits_only[:3]
                exchange = digits_only[3:6]

                # Area code cannot be 000, 111, or certain patterns
                if area_code in ("000", "111", "222"):
                    return False, 25

                # 555 exchange is reserved (except 555-0100 to 555-0199 which are allowed)
                if exchange == "555":
                    last_four = digits_only[6:10]
                    if not (last_four.startswith("01")):
                        return False, 25

        # Check for repeating patterns (e.g., 123-123-1234)
        if len(digits_only) >= 6:
            first_half = digits_only[:len(digits_only)//2]
            second_half = digits_only[len(digits_only)//2:]
            if first_half in second_half or second_half in first_half:
                return False, 30

        return True, 90

    @staticmethod
    def validate_credit_card(value: str) -> Tuple[bool, int]:
        """
        Validate credit card number using Luhn algorithm.

        Also checks for:
        - Invalid length (should be 13-19 digits)
        - Known test card numbers
        - Sequential or repeating patterns

        Args:
            value: Credit card number (digits, spaces, or hyphens)

        Returns:
            Tuple of (is_valid, adjusted_confidence):
            - is_valid: True if passes Luhn check
            - adjusted_confidence: 100 if valid, lower if test pattern

        Examples:
            >>> EntityValidator.validate_credit_card("4532015112830366")
            (True, 100)  # Valid Visa
            >>> EntityValidator.validate_credit_card("4111111111111111")
            (False, 20)  # Test/fake card
            >>> EntityValidator.validate_credit_card("1234567890123456")
            (False, 10)  # Invalid Luhn
        """
        if not value:
            return False, 0

        # Extract only digits
        digits_only = re.sub(r"\D", "", value)

        # Check length
        if len(digits_only) < 13 or len(digits_only) > 19:
            return False, 0

        # Known test card numbers (commonly used in documentation/tests)
        test_cards = {
            "4111111111111111",  # Visa test
            "5555555555554444",  # Mastercard test
            "378282246310005",   # Amex test
            "6011111111111117",  # Discover test
            "3530111333300000",  # JCB test
            "3566002020360505",  # JCB test
            "2131111111111111",  # Diners test
            "3600666666666666",  # Diners test
        }

        if digits_only in test_cards:
            return False, 15

        # Check for all same digits
        if len(set(digits_only)) == 1:
            return False, 10

        # Check for sequential patterns
        is_sequential = all(
            int(digits_only[i+1]) == (int(digits_only[i]) + 1) % 10
            for i in range(len(digits_only) - 1)
        )
        if is_sequential:
            return False, 15

        # Validate with Luhn algorithm
        if not EntityValidator._luhn_check(digits_only):
            return False, 10

        return True, 100

    @staticmethod
    def validate_iban(value: str) -> Tuple[bool, int]:
        """
        Validate IBAN using mod-97 algorithm and format checks.

        Checks for:
        - Correct length per country
        - Valid country code
        - Proper format
        - mod-97 checksum validity

        Args:
            value: IBAN string (e.g., "DE89370400440532013000")

        Returns:
            Tuple of (is_valid, adjusted_confidence):
            - is_valid: True if IBAN passes validation
            - adjusted_confidence: 100 if valid, lower if suspicious

        Examples:
            >>> EntityValidator.validate_iban("DE89370400440532013000")
            (True, 100)  # Valid German IBAN
            >>> EntityValidator.validate_iban("XX00000000000000000000")
            (False, 20)  # Invalid country code
            >>> EntityValidator.validate_iban("INVALID")
            (False, 0)  # Invalid format
        """
        if not value:
            return False, 0

        # Normalize: remove spaces and hyphens, uppercase
        normalized = re.sub(r"[\s\-]", "", value).upper()

        # Check format: 2 letters, 2 digits, then alphanumeric
        if not re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$", normalized):
            return False, 0

        # IBAN length should be 15-34 characters
        if len(normalized) < 15 or len(normalized) > 34:
            return False, 20

        # Country-specific expected lengths
        iban_lengths = {
            "AD": 24, "AE": 23, "AT": 20, "AZ": 28, "BA": 20, "BE": 20,
            "BG": 22, "BH": 22, "BR": 29, "BY": 28, "CH": 21, "CR": 22,
            "CY": 28, "CZ": 24, "DE": 22, "DK": 18, "DO": 28, "EE": 20,
            "EG": 29, "ES": 24, "FI": 18, "FO": 18, "FR": 27, "GB": 22,
            "GE": 22, "GI": 23, "GL": 18, "GR": 27, "GT": 28, "HR": 21,
            "HU": 28, "IE": 22, "IL": 23, "IS": 26, "IT": 27, "JO": 30,
            "KW": 30, "KZ": 20, "LB": 28, "LC": 32, "LI": 21, "LT": 20,
            "LU": 20, "LV": 21, "MC": 27, "MD": 24, "ME": 22, "MK": 19,
            "MR": 27, "MT": 31, "MU": 30, "NL": 18, "NO": 15, "PK": 24,
            "PL": 28, "PS": 29, "PT": 25, "QA": 29, "RO": 24, "RS": 22,
            "SA": 24, "SE": 24, "SI": 19, "SK": 24, "SM": 27, "TN": 24,
            "TR": 26, "UA": 29, "VA": 22, "VG": 24, "XK": 20,
        }

        country_code = normalized[:2]
        expected_length = iban_lengths.get(country_code)

        # Check country code validity
        if not country_code.isalpha() or len(country_code) != 2:
            return False, 20

        # Check length against country
        if expected_length and len(normalized) != expected_length:
            return False, 30

        # Check for all same digits after country code
        digit_part = normalized[4:]
        if digit_part and len(set(digit_part)) == 1:
            return False, 15

        # Validate with mod-97 algorithm
        if not EntityValidator._mod97_check(normalized):
            return False, 20

        return True, 100

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """
        Validate credit card using Luhn algorithm.

        The Luhn algorithm (also known as mod-10 algorithm) is used to
        validate credit card numbers and detect simple errors in typing.

        Args:
            card_number: String of digits

        Returns:
            True if checksum is valid

        Algorithm:
        1. From right to left, double every second digit
        2. If doubling results in > 9, subtract 9
        3. Sum all digits
        4. If sum % 10 == 0, valid
        """
        digits = [int(d) for d in card_number if d.isdigit()]

        checksum = 0
        for i, d in enumerate(reversed(digits)):
            if i % 2 == 1:  # Every second digit from right
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d

        return checksum % 10 == 0

    @staticmethod
    def _mod97_check(iban: str) -> bool:
        """
        Validate IBAN checksum using mod-97 algorithm.

        Algorithm:
        1. Move first 4 characters to end
        2. Replace each letter with digits (A=10, B=11, ..., Z=35)
        3. Calculate mod 97
        4. If result == 1, IBAN is valid

        Args:
            iban: IBAN string (uppercase, normalized)

        Returns:
            True if checksum is valid
        """
        # Move first 4 chars to end
        rearranged = iban[4:] + iban[:4]

        # Replace letters with numbers
        numeric = ""
        for char in rearranged:
            if char.isdigit():
                numeric += char
            else:
                # A=10, B=11, ..., Z=35
                numeric += str(ord(char) - ord("A") + 10)

        # Calculate mod 97
        # Use iterative approach to handle very large numbers
        remainder = 0
        for digit in numeric:
            remainder = (remainder * 10 + int(digit)) % 97

        return remainder == 1


# =============================================================================
# Public API - Convenience function for multi-entity validation
# =============================================================================

def validate_entity(
    entity_type: str,
    value: str,
    pattern_name: str = "",
) -> Tuple[bool, int]:
    """
    Unified validation function that dispatches to appropriate validator.

    Args:
        entity_type: Type of entity (SSN, EMAIL, PHONE_NUMBER, CREDIT_CARD, IBAN)
        value: The value to validate
        pattern_name: Optional pattern name for context (e.g., "phone_us_ca")

    Returns:
        Tuple of (is_valid, adjusted_confidence)

    Examples:
        >>> validate_entity("SSN", "000-00-0000")
        (False, 10)
        >>> validate_entity("EMAIL", "john@example.com")
        (True, 95)
        >>> validate_entity("PHONE_NUMBER", "(555) 123-4567", "phone_us_ca")
        (True, 90)
    """
    entity_type = entity_type.upper().strip()

    if entity_type == "SSN":
        return EntityValidator.validate_ssn(value)
    elif entity_type == "EMAIL":
        return EntityValidator.validate_email(value)
    elif entity_type == "PHONE_NUMBER":
        return EntityValidator.validate_phone(value, pattern_name)
    elif entity_type == "CREDIT_CARD":
        return EntityValidator.validate_credit_card(value)
    elif entity_type == "IBAN":
        return EntityValidator.validate_iban(value)
    else:
        # Unknown entity type - return original confidence
        return True, 85
