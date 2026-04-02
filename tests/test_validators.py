"""
Unit tests for entity validators.

Tests validate_ssn, validate_email, validate_phone, validate_credit_card, validate_iban
"""

import pytest
import sys
from pathlib import Path

# Add engine path to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "engine" / "python"))

from anonymizer_engine.validators import EntityValidator, validate_entity


class TestSSNValidator:
    """Tests for SSN validation."""

    def test_valid_ssn(self):
        """Test valid SSN."""
        is_valid, confidence = EntityValidator.validate_ssn("234-56-7890")
        assert is_valid is True
        assert confidence == 100

    def test_invalid_ssn_all_zeros(self):
        """Test invalid SSN - all zeros."""
        is_valid, confidence = EntityValidator.validate_ssn("000-00-0000")
        assert is_valid is False
        assert confidence == 10

    def test_invalid_ssn_all_ones(self):
        """Test invalid SSN - all ones."""
        is_valid, confidence = EntityValidator.validate_ssn("111-11-1111")
        assert is_valid is False
        assert confidence == 10

    def test_invalid_ssn_sequential(self):
        """Test invalid SSN - sequential pattern."""
        is_valid, confidence = EntityValidator.validate_ssn("123-45-6789")
        assert is_valid is False
        assert confidence == 25

    def test_invalid_ssn_area_zero(self):
        """Test invalid SSN - area code is 000."""
        is_valid, confidence = EntityValidator.validate_ssn("000-12-3456")
        assert is_valid is False
        assert confidence == 35

    def test_invalid_ssn_area_666(self):
        """Test invalid SSN - area code is 666."""
        is_valid, confidence = EntityValidator.validate_ssn("666-12-3456")
        assert is_valid is False
        assert confidence == 35

    def test_invalid_ssn_area_900_plus(self):
        """Test invalid SSN - area code is 900+."""
        is_valid, confidence = EntityValidator.validate_ssn("900-12-3456")
        assert is_valid is False
        assert confidence == 35

    def test_invalid_ssn_group_zero(self):
        """Test invalid SSN - group number is 00."""
        is_valid, confidence = EntityValidator.validate_ssn("123-00-4567")
        assert is_valid is False
        assert confidence == 35

    def test_invalid_ssn_serial_zero(self):
        """Test invalid SSN - serial is 0000."""
        is_valid, confidence = EntityValidator.validate_ssn("123-45-0000")
        assert is_valid is False
        assert confidence == 35

    def test_ssn_without_hyphens(self):
        """Test SSN without hyphens."""
        is_valid, confidence = EntityValidator.validate_ssn("234567890")
        assert is_valid is True
        assert confidence == 100

    def test_ssn_invalid_format(self):
        """Test invalid SSN format."""
        is_valid, confidence = EntityValidator.validate_ssn("invalid")
        assert is_valid is False
        assert confidence == 0

    def test_ssn_too_short(self):
        """Test SSN too short."""
        is_valid, confidence = EntityValidator.validate_ssn("123-45")
        assert is_valid is False
        assert confidence == 0


class TestEmailValidator:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid business email."""
        is_valid, confidence = EntityValidator.validate_email("john.smith@acme.com")
        assert is_valid is True
        assert confidence == 95

    def test_test_email_pattern(self):
        """Test email with test pattern."""
        is_valid, confidence = EntityValidator.validate_email("test@example.com")
        assert is_valid is False
        assert confidence == 20

    def test_noreply_email(self):
        """Test noreply email."""
        is_valid, confidence = EntityValidator.validate_email("noreply@company.com")
        assert is_valid is False
        assert confidence == 20

    def test_disposable_email_domain(self):
        """Test disposable email domain."""
        is_valid, confidence = EntityValidator.validate_email("user@tempmail.com")
        assert is_valid is False
        assert confidence == 15

    def test_example_com_domain(self):
        """Test example.com domain."""
        is_valid, confidence = EntityValidator.validate_email("user@example.com")
        assert is_valid is False
        assert confidence == 20

    def test_localhost_email(self):
        """Test localhost email."""
        is_valid, confidence = EntityValidator.validate_email("user@localhost")
        assert is_valid is False
        assert confidence == 20

    def test_invalid_email_format(self):
        """Test invalid email format."""
        is_valid, confidence = EntityValidator.validate_email("notanemail")
        assert is_valid is False
        assert confidence == 0

    def test_email_no_at_sign(self):
        """Test email without @."""
        is_valid, confidence = EntityValidator.validate_email("invalid.email")
        assert is_valid is False
        assert confidence == 0


class TestPhoneValidator:
    """Tests for phone number validation."""

    def test_valid_us_phone(self):
        """Test valid US phone number."""
        is_valid, confidence = EntityValidator.validate_phone("(555) 123-4567", "phone_us_ca")
        assert is_valid is True
        assert confidence == 90

    def test_invalid_phone_all_zeros(self):
        """Test phone all zeros."""
        is_valid, confidence = EntityValidator.validate_phone("000-000-0000", "phone_us_ca")
        assert is_valid is False
        assert confidence == 10

    def test_invalid_phone_all_ones(self):
        """Test phone all ones."""
        is_valid, confidence = EntityValidator.validate_phone("111-111-1111", "phone_us_ca")
        assert is_valid is False
        assert confidence == 10

    def test_invalid_phone_sequential(self):
        """Test phone sequential pattern."""
        is_valid, confidence = EntityValidator.validate_phone("123-456-7890", "phone_us_ca")
        assert is_valid is False
        assert confidence == 20

    def test_invalid_phone_555_area(self):
        """Test phone with 555 exchange."""
        is_valid, confidence = EntityValidator.validate_phone("(555) 555-1234", "phone_us_ca")
        assert is_valid is False
        assert confidence == 25

    def test_valid_phone_555_ok_range(self):
        """Test phone 555-0100 to 555-0199 (allowed range)."""
        is_valid, confidence = EntityValidator.validate_phone("(555) 123-0150", "phone_us_ca")
        assert is_valid is True
        assert confidence == 90

    def test_invalid_phone_too_short(self):
        """Test phone too short."""
        is_valid, confidence = EntityValidator.validate_phone("123-45", "phone_us_ca")
        assert is_valid is False
        assert confidence == 20

    def test_invalid_phone_too_long(self):
        """Test phone too long."""
        is_valid, confidence = EntityValidator.validate_phone("1234567890123456", "phone_us_ca")
        assert is_valid is False
        assert confidence == 20

    def test_valid_phone_no_pattern_name(self):
        """Test phone validation without pattern name."""
        is_valid, confidence = EntityValidator.validate_phone("(202) 555-0173")
        assert is_valid is True
        assert confidence == 90


class TestCreditCardValidator:
    """Tests for credit card validation."""

    def test_valid_visa_card(self):
        """Test valid Visa card number."""
        # This is a valid test card according to Luhn
        is_valid, confidence = EntityValidator.validate_credit_card("4532015112830366")
        assert is_valid is True
        assert confidence == 100

    def test_invalid_card_all_ones(self):
        """Test card all ones."""
        is_valid, confidence = EntityValidator.validate_credit_card("1111111111111111")
        assert is_valid is False

    def test_invalid_card_sequential(self):
        """Test card with sequential pattern."""
        is_valid, confidence = EntityValidator.validate_credit_card("1234567890123456")
        assert is_valid is False

    def test_test_visa_card(self):
        """Test known test Visa card."""
        is_valid, confidence = EntityValidator.validate_credit_card("4111111111111111")
        assert is_valid is False
        assert confidence == 15

    def test_test_mastercard(self):
        """Test known test Mastercard."""
        is_valid, confidence = EntityValidator.validate_credit_card("5555555555554444")
        assert is_valid is False
        assert confidence == 15

    def test_test_amex(self):
        """Test known test Amex."""
        is_valid, confidence = EntityValidator.validate_credit_card("378282246310005")
        assert is_valid is False
        assert confidence == 15

    def test_card_with_spaces(self):
        """Test card with spaces."""
        is_valid, confidence = EntityValidator.validate_credit_card("4532 0151 1283 0366")
        assert is_valid is True
        assert confidence == 100

    def test_card_with_hyphens(self):
        """Test card with hyphens."""
        is_valid, confidence = EntityValidator.validate_credit_card("4532-0151-1283-0366")
        assert is_valid is True
        assert confidence == 100

    def test_card_too_short(self):
        """Test card too short."""
        is_valid, confidence = EntityValidator.validate_credit_card("12345678")
        assert is_valid is False
        assert confidence == 0

    def test_card_too_long(self):
        """Test card too long."""
        is_valid, confidence = EntityValidator.validate_credit_card("123456789012345678901")
        assert is_valid is False
        assert confidence == 0


class TestIBANValidator:
    """Tests for IBAN validation."""

    def test_valid_german_iban(self):
        """Test valid German IBAN."""
        is_valid, confidence = EntityValidator.validate_iban("DE89370400440532013000")
        assert is_valid is True
        assert confidence == 100

    def test_valid_iban_with_spaces(self):
        """Test IBAN with spaces."""
        is_valid, confidence = EntityValidator.validate_iban("DE89 3704 0044 0532 0130 00")
        assert is_valid is True
        assert confidence == 100

    def test_valid_iban_with_hyphens(self):
        """Test IBAN with hyphens."""
        is_valid, confidence = EntityValidator.validate_iban("DE89-3704-0044-0532-0130-00")
        assert is_valid is True
        assert confidence == 100

    def test_invalid_iban_wrong_country(self):
        """Test IBAN with invalid country code."""
        is_valid, confidence = EntityValidator.validate_iban("XX00000000000000000000")
        assert is_valid is False

    def test_invalid_iban_format(self):
        """Test IBAN with invalid format."""
        is_valid, confidence = EntityValidator.validate_iban("INVALID")
        assert is_valid is False
        assert confidence == 0

    def test_invalid_iban_checksum(self):
        """Test IBAN with invalid checksum."""
        is_valid, confidence = EntityValidator.validate_iban("DE00370400440532013000")
        assert is_valid is False
        assert confidence <= 20

    def test_iban_too_short(self):
        """Test IBAN too short."""
        is_valid, confidence = EntityValidator.validate_iban("DE89370")
        assert is_valid is False
        assert confidence == 20

    def test_iban_too_long(self):
        """Test IBAN too long."""
        is_valid, confidence = EntityValidator.validate_iban("DE89370400440532013000123456789012345")
        assert is_valid is False
        assert confidence == 20

    def test_valid_french_iban(self):
        """Test valid French IBAN."""
        is_valid, confidence = EntityValidator.validate_iban("FR1420041010050500013M02606")
        assert is_valid is True
        assert confidence == 100

    def test_valid_uk_iban(self):
        """Test valid UK IBAN."""
        is_valid, confidence = EntityValidator.validate_iban("GB82WEST12345698765432")
        assert is_valid is True
        assert confidence == 100


class TestPublicAPI:
    """Tests for public validate_entity function."""

    def test_validate_entity_ssn(self):
        """Test validate_entity with SSN."""
        is_valid, confidence = validate_entity("SSN", "000-00-0000")
        assert is_valid is False
        assert confidence == 10

    def test_validate_entity_email(self):
        """Test validate_entity with email."""
        is_valid, confidence = validate_entity("EMAIL", "john@example.com")
        assert is_valid is True
        assert confidence == 95

    def test_validate_entity_phone(self):
        """Test validate_entity with phone."""
        is_valid, confidence = validate_entity("PHONE_NUMBER", "(555) 123-4567", "phone_us_ca")
        assert is_valid is True
        assert confidence == 90

    def test_validate_entity_credit_card(self):
        """Test validate_entity with credit card."""
        is_valid, confidence = validate_entity("CREDIT_CARD", "4111111111111111")
        assert is_valid is False
        assert confidence == 15

    def test_validate_entity_iban(self):
        """Test validate_entity with IBAN."""
        is_valid, confidence = validate_entity("IBAN", "DE89370400440532013000")
        assert is_valid is True
        assert confidence == 100

    def test_validate_entity_unknown_type(self):
        """Test validate_entity with unknown type."""
        is_valid, confidence = validate_entity("UNKNOWN", "value")
        assert is_valid is True
        assert confidence == 85

    def test_validate_entity_case_insensitive(self):
        """Test validate_entity is case insensitive."""
        is_valid, confidence = validate_entity("ssn", "000-00-0000")
        assert is_valid is False
        assert confidence == 10

    def test_validate_entity_with_whitespace(self):
        """Test validate_entity handles whitespace in entity type."""
        is_valid, confidence = validate_entity("  CREDIT_CARD  ", "4111111111111111")
        assert is_valid is False
        assert confidence == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
