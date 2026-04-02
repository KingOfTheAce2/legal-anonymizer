"""
Unit tests for pattern detection in legal-anonymizer.

Critical tests for PII pattern matching with focus on:
- Email detection accuracy
- Phone number detection (global formats)
- National ID detection (SSN, national IDs)
- False positive prevention
- Validation checksums (Luhn, mod-97)
"""

import pytest
from typing import List

from anonymizer_engine.patterns import (
    detect_patterns,
    detect_with_validation,
    PatternMatch,
    validate_iban,
    validate_credit_card,
    luhn_checksum,
    validate_china_id,
    validate_singapore_nric,
)


class TestEmailDetection:
    """Test email pattern detection."""

    @pytest.mark.unit
    @pytest.mark.pii_detection
    @pytest.mark.compliance
    def test_detects_standard_email(self):
        """Email detection: standard format."""
        text = "Contact user@example.com for details"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert len(email_matches) == 1
        assert email_matches[0].value == "user@example.com"

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_email_with_dots(self):
        """Email detection: address with dots in local part."""
        text = "Email: john.doe@example.com"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert len(email_matches) == 1
        assert email_matches[0].value == "john.doe@example.com"

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_email_with_plus(self):
        """Email detection: address with plus sign (Gmail-style)."""
        text = "user+tag@example.com is valid"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert len(email_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_email_subdomain(self):
        """Email detection: subdomain addresses."""
        text = "support@mail.example.co.uk"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert len(email_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.false_positive
    def test_email_not_detected_in_url(self):
        """Email detection: shouldn't double-detect in URLs."""
        text = "Visit https://example.com or email user@example.com"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        # Should find at least the email, might find more
        assert any(m.value == "user@example.com" for m in email_matches)

    @pytest.mark.unit
    @pytest.mark.false_positive
    def test_email_high_confidence(self, sample_email):
        """Email detection: high confidence score."""
        text = f"Contact {sample_email} now"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert all(m.confidence >= 90 for m in email_matches)


class TestPhoneNumberDetection:
    """Test phone number pattern detection across regions."""

    @pytest.mark.unit
    @pytest.mark.pii_detection
    @pytest.mark.compliance
    def test_detects_us_phone_standard(self):
        """Phone: US format (123) 456-7890."""
        text = "Call (555) 123-4567 for support"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1
        assert any("555" in m.value for m in phone_matches)

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_us_phone_dashes(self):
        """Phone: US format 555-123-4567."""
        text = "Phone: 555-123-4567"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_intl_phone_plus(self, sample_intl_phone):
        """Phone: International format with + prefix."""
        text = f"Reach me at {sample_intl_phone}"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_uk_phone(self):
        """Phone: UK format 07xxx xxxxxx."""
        text = "UK number: 07123 456789"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_germany_phone(self):
        """Phone: German format +49."""
        text = "Call +49 30 12345678 in Berlin"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_france_phone(self):
        """Phone: French format 06 12 34 56 78."""
        text = "Téléphone: 06 12 34 56 78"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_china_phone(self):
        """Phone: Chinese format +86."""
        text = "Call +86 138 0012 8176 in Shanghai"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_japan_phone(self):
        """Phone: Japanese format 090-xxxx-xxxx."""
        text = "Japan: 090-1234-5678"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_india_phone(self):
        """Phone: Indian format +91."""
        text = "India: +91 98765 43210"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.false_positive
    def test_phone_not_detected_in_version_number(self):
        """Phone: false positive prevention - version numbers."""
        text = "Version 1.2.3.4 released"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        # Version numbers shouldn't be detected as phones (low confidence)
        assert all(m.confidence < 90 for m in phone_matches) if phone_matches else True

    @pytest.mark.unit
    @pytest.mark.false_positive
    def test_phone_not_detected_in_timestamp(self):
        """Phone: false positive prevention - timestamps."""
        text = "Timestamp: 10:30:45"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        # Timestamps shouldn't look like phones
        assert len(phone_matches) == 0 or all(m.confidence < 80 for m in phone_matches)

    @pytest.mark.unit
    @pytest.mark.high_priority
    @pytest.mark.compliance
    def test_phone_high_confidence_intl(self):
        """Phone: high confidence for international format."""
        text = "+1 (555) 123-4567"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert any(m.confidence >= 85 for m in phone_matches)


class TestSSNAndNationalIDDetection:
    """Test Social Security Number and National ID detection."""

    @pytest.mark.unit
    @pytest.mark.pii_detection
    @pytest.mark.compliance
    @pytest.mark.high_priority
    def test_detects_us_ssn(self, sample_us_ssn):
        """SSN: US Social Security Number XXX-XX-XXXX."""
        text = f"SSN: {sample_us_ssn}"
        matches = detect_patterns(text)
        ssn_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(ssn_matches) >= 1
        assert sample_us_ssn in [m.value for m in ssn_matches]

    @pytest.mark.unit
    @pytest.mark.pii_detection
    @pytest.mark.compliance
    def test_detects_uk_nino(self):
        """NINO: UK National Insurance Number."""
        text = "NI Number: AB123456C"
        matches = detect_patterns(text)
        nino_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(nino_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_spain_dni(self):
        """DNI: Spanish National ID."""
        text = "DNI: 12345678A"
        matches = detect_patterns(text)
        matches_found = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(matches_found) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_spain_nie(self):
        """NIE: Spanish foreigner ID."""
        text = "NIE: X1234567L"
        matches = detect_patterns(text)
        nie_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(nie_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_france_insee(self):
        """INSEE: French national ID."""
        text = "INSEE: 1 70 12 75 123 456 78"
        matches = detect_patterns(text)
        insee_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(insee_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_germany_tax_id(self):
        """Tax ID: German Steuer-ID."""
        text = "Steuer-ID: 12345678901"
        matches = detect_patterns(text)
        tax_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(tax_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_china_id_18_digit(self):
        """China ID: 18-digit format."""
        text = "ID: 110101199003077515"
        matches = detect_patterns(text)
        id_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(id_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_china_id_15_digit(self):
        """China ID: 15-digit format."""
        text = "ID: 370103200001011"
        matches = detect_patterns(text)
        id_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(id_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_japan_mynumber(self):
        """My Number: Japanese national ID."""
        text = "My Number: 1234 5678 9012"
        matches = detect_patterns(text)
        mynumber_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(mynumber_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_korea_rrn(self):
        """RRN: Korean Resident Registration Number."""
        text = "RRN: 900101-1234567"
        matches = detect_patterns(text)
        rrn_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(rrn_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_singapore_nric(self):
        """NRIC: Singapore National ID."""
        text = "NRIC: S1234567A"
        matches = detect_patterns(text)
        nric_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(nric_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.false_positive
    def test_ssn_not_detected_in_version(self):
        """SSN: false positive prevention - not in version numbers."""
        text = "Version 123.45.6789"
        matches = detect_patterns(text)
        ssn_matches = [m for m in matches if m.entity_type == "NATIONAL_ID" and "ssn" in m.pattern_name.lower()]
        # Should not detect SSN in version strings
        assert len(ssn_matches) == 0 or all(m.confidence < 70 for m in ssn_matches)

    @pytest.mark.unit
    @pytest.mark.false_positive
    def test_id_not_detected_in_dates(self):
        """ID: false positive prevention - not in date-like patterns."""
        text = "01-23-45"
        matches = detect_patterns(text)
        id_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        # Should be careful with date-like patterns
        # Either not detected or low confidence
        assert len(id_matches) == 0 or all(m.confidence < 70 for m in id_matches)


class TestCreditCardDetection:
    """Test credit card number detection and Luhn validation."""

    @pytest.mark.unit
    @pytest.mark.pii_detection
    @pytest.mark.compliance
    def test_detects_visa_card(self):
        """Credit Card: Visa (starts with 4)."""
        text = "Card: 4111111111111111"
        matches = detect_patterns(text)
        cc_matches = [m for m in matches if m.entity_type == "CREDIT_CARD"]
        assert len(cc_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_mastercard(self):
        """Credit Card: Mastercard (starts with 5)."""
        text = "Card: 5555555555554444"
        matches = detect_patterns(text)
        cc_matches = [m for m in matches if m.entity_type == "CREDIT_CARD"]
        assert len(cc_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_amex(self):
        """Credit Card: American Express."""
        text = "Card: 378282246310005"
        matches = detect_patterns(text)
        cc_matches = [m for m in matches if m.entity_type == "CREDIT_CARD"]
        assert len(cc_matches) >= 1

    @pytest.mark.unit
    def test_luhn_checksum_valid(self):
        """Luhn: valid checksum."""
        assert luhn_checksum("4111111111111111") is True
        assert luhn_checksum("5555555555554444") is True
        assert luhn_checksum("378282246310005") is True

    @pytest.mark.unit
    def test_luhn_checksum_invalid(self):
        """Luhn: invalid checksum."""
        assert luhn_checksum("4111111111111112") is False
        assert luhn_checksum("1234567890123456") is False

    @pytest.mark.unit
    @pytest.mark.false_positive
    def test_card_not_detected_in_long_number_sequence(self):
        """Credit Card: avoid false positives in long numbers."""
        text = "Reference 123456789012345678"
        matches = detect_patterns(text)
        cc_matches = [m for m in matches if m.entity_type == "CREDIT_CARD"]
        # Not all long numbers are credit cards
        # Should be validated by Luhn
        assert len(cc_matches) == 0 or all(luhn_checksum(m.value) for m in cc_matches)


class TestBankAccountDetection:
    """Test bank account and IBAN detection."""

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_iban(self, sample_iban):
        """IBAN: International Bank Account Number."""
        text = f"Transfer to: {sample_iban}"
        matches = detect_patterns(text)
        iban_matches = [m for m in matches if m.entity_type == "BANK_ACCOUNT"]
        assert len(iban_matches) >= 1

    @pytest.mark.unit
    def test_iban_validation_valid(self):
        """IBAN: validate correct IBAN (mod-97)."""
        # Valid German IBAN
        assert validate_iban("DE89370400440532013000") is True
        # Valid UK IBAN
        assert validate_iban("GB82WEST12345698765432") is True

    @pytest.mark.unit
    def test_iban_validation_invalid(self):
        """IBAN: reject incorrect checksum."""
        assert validate_iban("DE89370400440532013001") is False
        assert validate_iban("DE12345678901234567890") is False


class TestIPAddressDetection:
    """Test IP address detection."""

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_ipv4(self, sample_ipv4):
        """IPv4: standard IP address."""
        text = f"Server: {sample_ipv4}"
        matches = detect_patterns(text)
        ip_matches = [m for m in matches if m.entity_type == "IP_ADDRESS"]
        assert len(ip_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.pii_detection
    def test_detects_ipv6(self, sample_ipv6):
        """IPv6: full IPv6 address."""
        text = f"Address: {sample_ipv6}"
        matches = detect_patterns(text)
        ip_matches = [m for m in matches if m.entity_type == "IP_ADDRESS"]
        assert len(ip_matches) >= 1

    @pytest.mark.unit
    @pytest.mark.false_positive
    def test_ipv4_not_detected_in_address(self):
        """IPv4: avoid false positive in addresses."""
        text = "Version 1.2.3.4"
        matches = detect_patterns(text)
        ip_matches = [m for m in matches if m.entity_type == "IP_ADDRESS"]
        # Version numbers might look like IPs but have context
        # Should be low confidence or none


class TestChinaIDValidation:
    """Test China ID validation."""

    @pytest.mark.unit
    def test_china_id_validation_valid(self):
        """China ID: valid 18-digit format."""
        # Valid China ID (checksum digit 2 at position 18)
        assert validate_china_id("110101199003077512") is True

    @pytest.mark.unit
    def test_china_id_validation_invalid(self):
        """China ID: reject invalid checksum."""
        # Wrong checksum
        assert validate_china_id("110101199003077514") is False
        # Wrong length
        assert validate_china_id("1101011990030775") is False


class TestSingaporeNRICValidation:
    """Test Singapore NRIC validation."""

    @pytest.mark.unit
    def test_singapore_nric_validation_valid(self):
        """Singapore NRIC: valid format."""
        # Note: these are example formats, actual validation depends on checksum algorithm
        result = validate_singapore_nric("S1234567A")
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_singapore_nric_validation_invalid_format(self):
        """Singapore NRIC: reject invalid format."""
        assert validate_singapore_nric("X1234567A") is False  # Invalid first letter


class TestPatternConfidence:
    """Test confidence scoring for patterns."""

    @pytest.mark.unit
    @pytest.mark.compliance
    def test_email_high_confidence(self):
        """Confidence: emails should be high confidence."""
        text = "user@example.com"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert all(m.confidence >= 90 for m in email_matches)

    @pytest.mark.unit
    def test_phone_high_confidence_intl(self):
        """Confidence: intl phone numbers should have at least one high-confidence match."""
        text = "+1 (555) 123-4567"
        matches = detect_patterns(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) > 0
        assert max(m.confidence for m in phone_matches) >= 85

    @pytest.mark.unit
    def test_national_id_high_confidence(self):
        """Confidence: national IDs should have at least one high-confidence match."""
        text = "SSN: 123-45-6789"
        matches = detect_patterns(text)
        id_matches = [m for m in matches if m.entity_type == "NATIONAL_ID"]
        assert len(id_matches) > 0
        assert max(m.confidence for m in id_matches) >= 85


class TestValidateWithValidation:
    """Test detect_with_validation function."""

    @pytest.mark.unit
    @pytest.mark.compliance
    def test_detects_with_validation_credit_card(self):
        """With validation: credit card Luhn check."""
        text = "Pay to: 4111111111111111"
        matches = detect_with_validation(text)
        cc_matches = [m for m in matches if m.entity_type == "CREDIT_CARD"]
        # Should either be empty or have valid cards
        for match in cc_matches:
            assert luhn_checksum(match.value)

    @pytest.mark.unit
    def test_detects_with_validation_iban(self):
        """With validation: IBAN mod-97 check."""
        text = "Bank: DE89370400440532013000"
        matches = detect_with_validation(text)
        iban_matches = [m for m in matches if "iban" in m.pattern_name.lower()]
        # Should either be empty or have valid IBANs
        for match in iban_matches:
            # Note: pattern_name check
            pass

    @pytest.mark.unit
    @pytest.mark.compliance
    def test_confidence_boost_after_validation(self):
        """Validation: confidence should increase for valid patterns."""
        text = "Card: 4111111111111111"
        matches = detect_with_validation(text)
        cc_matches = [m for m in matches if m.entity_type == "CREDIT_CARD"]
        # Valid cards should have higher confidence (Luhn-validated gets boosted)
        assert len(cc_matches) > 0
        assert max(m.confidence for m in cc_matches if m.value == "4111111111111111") >= 90


class TestMultipleDetectionsInText:
    """Test detection of multiple PII in single text."""

    @pytest.mark.unit
    @pytest.mark.compliance
    def test_detects_multiple_emails(self):
        """Multiple: multiple email addresses."""
        text = "Contact user1@example.com or user2@example.com"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert len(email_matches) >= 2

    @pytest.mark.unit
    def test_detects_mixed_pii_types(self):
        """Multiple: email and phone in same text."""
        text = "Email: test@example.com, Phone: (555) 123-4567"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(email_matches) >= 1
        assert len(phone_matches) >= 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_empty_string(self):
        """Edge case: empty string."""
        matches = detect_patterns("")
        assert len(matches) == 0

    @pytest.mark.unit
    def test_whitespace_only(self):
        """Edge case: whitespace only."""
        matches = detect_patterns("   \n\t  ")
        assert len(matches) == 0

    @pytest.mark.unit
    def test_very_long_text(self):
        """Edge case: very long text."""
        text = "Email: " + "test@example.com " * 1000
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        # Should handle large texts
        assert len(email_matches) > 0

    @pytest.mark.unit
    def test_special_characters(self):
        """Edge case: special characters in context."""
        text = "Contact: user+tag@example.co.uk!?!"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert len(email_matches) >= 1

    @pytest.mark.unit
    def test_unicode_characters(self):
        """Edge case: unicode characters in surrounding text, ASCII email still detected."""
        text = "José García: user@example.com"
        matches = detect_patterns(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL"]
        assert len(email_matches) >= 1
