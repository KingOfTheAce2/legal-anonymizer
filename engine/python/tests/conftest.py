"""
Pytest configuration and shared fixtures for legal-anonymizer tests.

This module provides:
- Common test fixtures
- Mock objects for external dependencies
- Test data builders
- Pytest hooks and configuration
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from anonymizer_engine.patterns import PatternMatch
from anonymizer_engine.findings import Finding
from anonymizer_engine.preset import Preset


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "compliance: mark test as compliance-critical"
    )
    config.addinivalue_line(
        "markers", "pii_detection: mark test as testing PII detection"
    )
    config.addinivalue_line(
        "markers", "false_positive: mark test as testing false positive prevention"
    )


# =============================================================================
# BASIC FIXTURES
# =============================================================================

@pytest.fixture
def sample_email():
    """Sample email address for testing."""
    return "john.doe@example.com"


@pytest.fixture
def sample_us_phone():
    """Sample US phone number."""
    return "(123) 456-7890"


@pytest.fixture
def sample_us_ssn():
    """Sample US Social Security Number."""
    return "123-45-6789"


@pytest.fixture
def sample_intl_phone():
    """Sample international phone number."""
    return "+44 7123 456789"


@pytest.fixture
def sample_credit_card():
    """Sample credit card number (valid Luhn checksum)."""
    return "4532015112830366"


@pytest.fixture
def sample_iban():
    """Sample IBAN (valid mod-97 checksum)."""
    return "DE89370400440532013000"


@pytest.fixture
def sample_ipv4():
    """Sample IPv4 address."""
    return "192.168.1.1"


@pytest.fixture
def sample_ipv6():
    """Sample IPv6 address."""
    return "2001:0db8:85a3:0000:0000:8a2e:0370:7334"


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_legal_document():
    """Sample legal document with multiple PII types."""
    return """
SETTLEMENT AGREEMENT

This agreement is made between John Smith (SSN: 987-65-4321) and ABC Corporation.

Contact Information:
Email: john.smith@smithlaw.net
Phone: (617) 263-4000
Address: 123 Main Street, New York, NY 10001

Terms:
The settlement amount is $50,000 USD. Payment should be made to:
Bank Account: DE89370400440532013000
SWIFT Code: DEUTDEDD

Dated: January 1, 2024
Signature: ________________________
"""


@pytest.fixture
def sample_multilingual_text():
    """Sample text with multiple languages containing PII."""
    return """
English: Contact john.doe@example.com or call +1 (555) 123-4567
Dutch: Bel +31 6 12345678 of stuur een email naar jan.jansen@example.nl
German: Rufen Sie +49 30 12345678 an oder schreiben Sie an hans.mueller@example.de
"""


@pytest.fixture
def sample_false_positive_cases():
    """Sample text with patterns that resemble PII but aren't."""
    return {
        "version": "Version 1.2.3.4 is stable",  # Looks like IP/phone
        "date_us": "The date 01-23-45 was significant",  # Could look like SSN
        "date_eu": "Happened on 23.01.2024 in Berlin",  # European date format
        "time_stamp": "Time: 10:30:45",  # Could be mistaken for phone
        "math": "The result is 123 456.78 EUR",  # Numbers with spacing
        "code": "Use code ABC-123-DEF for reference",  # Pattern-like
    }


@pytest.fixture
def sample_edge_cases():
    """Sample text with edge cases and boundary conditions."""
    return {
        "empty_string": "",
        "whitespace_only": "   \n\t  ",
        "very_long_text": "a" * 100000,  # Large text
        "special_chars": "Email: user+tag@example.co.uk",
        "unicode": "Contact: José García <josé@example.com>",
        "mixed_case": "EMAIL: User@EXAMPLE.COM",
        "multiple_spaces": "Call    555    123    4567",
        "malformed_ssn": "SSN: 123--45-6789",  # Missing digit
    }


@pytest.fixture
def sample_high_priority_pii():
    """Sample text containing high-priority PII that must never be missed."""
    return {
        "us_ssn": "Social Security: 987-65-4321",
        "uk_nino": "National Insurance: AB123456C",
        "china_id": "身份证: 110101199003077515",
        "passport": "Passport: A12345678",
        "credit_card": "Card: 4111111111111111",
        "eu_tax_id": "VAT: DE123456789",
        "health_record": "Patient ID: MED-2024-001234",
    }


# =============================================================================
# PRESET FIXTURES
# =============================================================================

@pytest.fixture
def preset_aggressive():
    """Aggressive preset that redacts all detected PII."""
    return Preset(
        preset_id="aggressive",
        name="aggressive",
        minimum_confidence=50,
        uncertainty_policy="redact",
        entities_enabled={
            "EMAIL": True,
            "PHONE_NUMBER": True,
            "NATIONAL_ID": True,
            "PASSPORT": True,
            "CREDIT_CARD": True,
            "BANK_ACCOUNT": True,
            "IP_ADDRESS": True,
            "PERSON": True,
            "ORGANIZATION": True,
        }
    )


@pytest.fixture
def preset_conservative():
    """Conservative preset that only redacts high-confidence matches."""
    return Preset(
        preset_id="conservative",
        name="conservative",
        minimum_confidence=90,
        uncertainty_policy="leave_intact",
        entities_enabled={
            "EMAIL": True,
            "PHONE_NUMBER": True,
            "NATIONAL_ID": True,
            "PASSPORT": True,
            "CREDIT_CARD": True,
            "BANK_ACCOUNT": True,
            "IP_ADDRESS": False,
            "PERSON": False,
            "ORGANIZATION": False,
        }
    )


@pytest.fixture
def preset_balanced():
    """Balanced preset for general-purpose anonymization."""
    return Preset(
        preset_id="balanced",
        name="balanced",
        minimum_confidence=75,
        uncertainty_policy="mask",
        entities_enabled={
            "EMAIL": True,
            "PHONE_NUMBER": True,
            "NATIONAL_ID": True,
            "PASSPORT": True,
            "CREDIT_CARD": True,
            "BANK_ACCOUNT": True,
            "IP_ADDRESS": True,
            "PERSON": True,
            "ORGANIZATION": True,
        }
    )


# =============================================================================
# PATTERN MATCH BUILDERS
# =============================================================================

@pytest.fixture
def pattern_match_builder():
    """Factory for creating PatternMatch objects."""
    def _builder(
        value: str,
        entity_type: str = "EMAIL",
        start: int = 0,
        confidence: int = 95,
        pattern_name: str = "test_pattern",
    ) -> PatternMatch:
        return PatternMatch(
            start=start,
            end=start + len(value),
            entity_type=entity_type,
            value=value,
            confidence=confidence,
            pattern_name=pattern_name,
        )
    return _builder


# =============================================================================
# FINDING BUILDERS
# =============================================================================

@pytest.fixture
def finding_builder():
    """Factory for creating Finding objects."""
    def _builder(
        entity_type: str = "EMAIL",
        detected_text: str = "test@example.com",
        confidence_score: int = 95,
        redaction_action: str = "redact",
        file_id: str = "TEST_001",
    ) -> Finding:
        return Finding(
            file_id=file_id,
            original_filename="test.txt",
            page_or_location="1:10-25",
            entity_type=entity_type,
            entity_priority=90,
            detected_text=detected_text,
            context_snippet=f"...{detected_text}...",
            detection_source="pattern:test",
            model_id="",
            confidence_score=confidence_score,
            confidence_threshold=75,
            uncertainty_flag=False,
            redaction_action=redaction_action,
            pseudonym_value="",
            escalation_applied=False,
            whitelist_match=False,
            blacklist_match=False,
            language="en",
            start_pos=10,
            end_pos=25,
        )
    return _builder


# =============================================================================
# PHONE NUMBER TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def valid_phone_numbers():
    """Dictionary of valid phone numbers by region."""
    return {
        # Americas
        "us": [
            "+1 (555) 123-4567",
            "555-123-4567",
            "(555) 123-4567",
            "+1 555 123 4567",
        ],
        "canada": [
            "+1 (416) 555-0123",
            "416-555-0123",
        ],
        "brazil": [
            "+55 11 91234-5678",
            "+55 21 3333-4444",
        ],
        "mexico": [
            "+52 55 1234 5678",
            "+52 33 3333 4444",
        ],

        # Europe
        "uk": [
            "+44 7123 456789",
            "07123 456789",
            "+44 20 7123 4567",
        ],
        "france": [
            "+33 6 12 34 56 78",
            "06 12 34 56 78",
            "+33 1 42 34 56 78",
        ],
        "germany": [
            "+49 30 12345678",
            "+49 89 123 456",
        ],
        "netherlands": [
            "+31 6 12345678",
            "+31 20 1234567",
        ],

        # Asia
        "china": [
            "+86 138 0012 8176",
            "+86 10 1234 5678",
            "138-0012-8176",
        ],
        "japan": [
            "+81 90-1234-5678",
            "090-1234-5678",
            "+81 3-1234-5678",
        ],
        "korea": [
            "+82 10-1234-5678",
            "010-1234-5678",
        ],
        "india": [
            "+91 98765 43210",
            "+91 11 4567 8901",
        ],
        "singapore": [
            "+65 9123 4567",
            "+65 6789 0123",
        ],

        # Middle East & Africa
        "uae": [
            "+971 50 123 4567",
            "+971 4 123 4567",
        ],
        "southafrica": [
            "+27 21 123 4567",
            "+27 72 123 4567",
        ],
    }


@pytest.fixture
def invalid_phone_numbers():
    """List of invalid phone numbers that should NOT be detected."""
    return [
        "555",  # Too short
        "123",  # Too short
        "+999999999999999999999",  # Invalid country code
        "not a phone",
        "Call me sometime",
    ]


# =============================================================================
# SSN/NATIONAL ID TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def valid_national_ids():
    """Dictionary of valid national IDs by country."""
    return {
        "us_ssn": [
            "123-45-6789",
            "999-99-9999",
        ],
        "uk_nino": [
            "AB123456C",
            "JY123456D",
        ],
        "spain_dni": [
            "12345678A",
            "87654321Z",
        ],
        "spain_nie": [
            "X1234567L",
            "Y9876543M",
        ],
        "france_insee": [
            "1 70 12 75 123 456 78",
            "2 75 05 75 000 000 00",
        ],
        "germany_tax_id": [
            "12345678901",
            "98765432109",
        ],
        "netherlands_bsn": [
            "123456789",
            "987654321",
        ],
        "china_id_18": [
            "110101199003077515",
            "370103820001011234",
        ],
        "china_id_15": [
            "370103200001011",
        ],
        "japan_mynumber": [
            "1234 5678 9012",
        ],
        "korea_rrn": [
            "900101-1234567",
            "001231-1234567",
        ],
        "india_aadhaar": [
            "1234 5678 9012",
        ],
        "singapore_nric": [
            "S1234567A",
            "T9876543Z",
        ],
    }


# =============================================================================
# EMAIL TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def valid_emails():
    """List of valid email addresses."""
    return [
        "user@example.com",
        "john.doe@example.com",
        "user+tag@example.co.uk",
        "test.email+alex@leetcode.com",
        "user_123@example-domain.com",
        "a@example.com",  # Single char local part
        "user@sub.example.com",
        "user@example.co.uk",
        "josé@example.com",  # Unicode
    ]


@pytest.fixture
def invalid_emails():
    """List of invalid email addresses that should NOT be detected."""
    return [
        "user@.com",  # Missing domain
        "@example.com",  # Missing local part
        "user@example",  # Missing TLD
        "user example@example.com",  # Space in local part (if implementation strict)
        "user@exam ple.com",  # Space in domain
    ]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

@pytest.fixture
def assert_pii_found():
    """Helper to assert PII was found in text."""
    def _assert(findings: List[Finding], entity_type: str, count: int = None):
        matching = [f for f in findings if f.entity_type == entity_type]
        if count is not None:
            assert len(matching) == count, (
                f"Expected {count} {entity_type} findings, got {len(matching)}"
            )
        else:
            assert len(matching) > 0, f"No {entity_type} findings detected"
        return matching
    return _assert


@pytest.fixture
def assert_pii_not_found():
    """Helper to assert PII was NOT found in text."""
    def _assert(findings: List[Finding], entity_type: str):
        matching = [f for f in findings if f.entity_type == entity_type]
        assert len(matching) == 0, (
            f"Expected no {entity_type} findings, but found {len(matching)}: "
            f"{[f.detected_text for f in matching]}"
        )
    return _assert


@pytest.fixture
def assert_text_redacted():
    """Helper to assert text was properly redacted."""
    def _assert(original: str, redacted: str, expected_redaction: str = "█"):
        assert original != redacted, "Text was not redacted"
        assert expected_redaction in redacted, f"Expected redaction char '{expected_redaction}' not found"
    return _assert


@pytest.fixture
def assert_high_confidence_only():
    """Helper to assert only high-confidence matches."""
    def _assert(findings: List[Finding], min_confidence: int = 80):
        low_conf = [f for f in findings if f.confidence_score < min_confidence]
        assert len(low_conf) == 0, (
            f"Found {len(low_conf)} low-confidence matches: "
            f"{[(f.detected_text, f.confidence_score) for f in low_conf]}"
        )
    return _assert
