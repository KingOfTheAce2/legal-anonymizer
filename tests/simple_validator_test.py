"""
Simple validator tests - run directly without pytest dependency
"""
import sys
from pathlib import Path

# Add engine path to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "engine" / "python"))

from anonymizer_engine.validators import EntityValidator, validate_entity


def test_ssn_validation():
    """Test SSN validation."""
    print("Testing SSN Validation:")

    # Valid SSN
    is_valid, conf = EntityValidator.validate_ssn("234-56-7890")
    assert is_valid is True, "234-56-7890 should be valid"
    assert conf == 100, f"Expected 100, got {conf}"
    print("  ✓ Valid SSN (234-56-7890)")

    # Invalid - all zeros
    is_valid, conf = EntityValidator.validate_ssn("000-00-0000")
    assert is_valid is False, "000-00-0000 should be invalid"
    assert conf == 10, f"Expected 10, got {conf}"
    print("  ✓ Invalid SSN (000-00-0000)")

    # Invalid - sequential
    is_valid, conf = EntityValidator.validate_ssn("123-45-6789")
    assert is_valid is False, "123-45-6789 should be invalid (sequential)"
    assert conf == 25, f"Expected 25, got {conf}"
    print("  ✓ Invalid SSN (123-45-6789 - sequential)")

    # Invalid - area code 000
    is_valid, conf = EntityValidator.validate_ssn("000-12-3456")
    assert is_valid is False, "000-12-3456 should be invalid"
    print("  ✓ Invalid SSN (000-12-3456 - area code 000)")


def test_email_validation():
    """Test email validation."""
    print("\nTesting Email Validation:")

    # Valid business email
    is_valid, conf = EntityValidator.validate_email("john.smith@acme.com")
    assert is_valid is True, "john.smith@acme.com should be valid"
    assert conf == 95, f"Expected 95, got {conf}"
    print("  ✓ Valid email (john.smith@acme.com)")

    # Test email
    is_valid, conf = EntityValidator.validate_email("test@example.com")
    assert is_valid is False, "test@example.com should be invalid"
    assert conf == 20, f"Expected 20, got {conf}"
    print("  ✓ Invalid test email (test@example.com)")

    # Disposable domain
    is_valid, conf = EntityValidator.validate_email("user@tempmail.com")
    assert is_valid is False, "user@tempmail.com should be invalid"
    assert conf == 15, f"Expected 15, got {conf}"
    print("  ✓ Invalid disposable email (user@tempmail.com)")

    # Noreply
    is_valid, conf = EntityValidator.validate_email("noreply@company.com")
    assert is_valid is False, "noreply@company.com should be invalid"
    print("  ✓ Invalid noreply email (noreply@company.com)")


def test_phone_validation():
    """Test phone validation."""
    print("\nTesting Phone Validation:")

    # Valid US phone
    is_valid, conf = EntityValidator.validate_phone("(555) 123-4567", "phone_us_ca")
    assert is_valid is True, "(555) 123-4567 should be valid"
    assert conf == 90, f"Expected 90, got {conf}"
    print("  ✓ Valid US phone ((555) 123-4567)")

    # All zeros
    is_valid, conf = EntityValidator.validate_phone("000-000-0000", "phone_us_ca")
    assert is_valid is False, "000-000-0000 should be invalid"
    assert conf == 10, f"Expected 10, got {conf}"
    print("  ✓ Invalid phone (000-000-0000)")

    # All ones
    is_valid, conf = EntityValidator.validate_phone("111-111-1111", "phone_us_ca")
    assert is_valid is False, "111-111-1111 should be invalid"
    print("  ✓ Invalid phone (111-111-1111)")

    # Sequential
    is_valid, conf = EntityValidator.validate_phone("123-456-7890", "phone_us_ca")
    assert is_valid is False, "123-456-7890 should be invalid (sequential)"
    print("  ✓ Invalid phone (123-456-7890 - sequential)")


def test_credit_card_validation():
    """Test credit card validation."""
    print("\nTesting Credit Card Validation:")

    # Valid card (passes Luhn)
    is_valid, conf = EntityValidator.validate_credit_card("4532015112830366")
    assert is_valid is True, "4532015112830366 should be valid"
    assert conf == 100, f"Expected 100, got {conf}"
    print("  ✓ Valid credit card (4532015112830366)")

    # Test card - Visa
    is_valid, conf = EntityValidator.validate_credit_card("4111111111111111")
    assert is_valid is False, "4111111111111111 should be invalid (test card)"
    assert conf == 15, f"Expected 15, got {conf}"
    print("  ✓ Invalid test card (4111111111111111)")

    # Test card - Mastercard
    is_valid, conf = EntityValidator.validate_credit_card("5555555555554444")
    assert is_valid is False, "5555555555554444 should be invalid (test card)"
    print("  ✓ Invalid test card (5555555555554444)")

    # All ones
    is_valid, conf = EntityValidator.validate_credit_card("1111111111111111")
    assert is_valid is False, "1111111111111111 should be invalid"
    print("  ✓ Invalid card (1111111111111111)")


def test_iban_validation():
    """Test IBAN validation."""
    print("\nTesting IBAN Validation:")

    # Valid German IBAN
    is_valid, conf = EntityValidator.validate_iban("DE89370400440532013000")
    assert is_valid is True, "DE89370400440532013000 should be valid"
    assert conf == 100, f"Expected 100, got {conf}"
    print("  ✓ Valid German IBAN (DE89370400440532013000)")

    # With spaces
    is_valid, conf = EntityValidator.validate_iban("DE89 3704 0044 0532 0130 00")
    assert is_valid is True, "DE89 3704 0044 0532 0130 00 should be valid"
    print("  ✓ Valid IBAN with spaces")

    # Invalid format
    is_valid, conf = EntityValidator.validate_iban("INVALID")
    assert is_valid is False, "INVALID should be invalid"
    assert conf == 0, f"Expected 0, got {conf}"
    print("  ✓ Invalid IBAN (INVALID)")

    # Valid French IBAN
    is_valid, conf = EntityValidator.validate_iban("FR1420041010050500013M02606")
    assert is_valid is True, "FR1420041010050500013M02606 should be valid"
    print("  ✓ Valid French IBAN (FR1420041010050500013M02606)")


def test_public_api():
    """Test public API."""
    print("\nTesting Public API (validate_entity):")

    # SSN
    is_valid, conf = validate_entity("SSN", "000-00-0000")
    assert is_valid is False, "000-00-0000 should be invalid"
    print("  ✓ validate_entity('SSN', '000-00-0000')")

    # Email
    is_valid, conf = validate_entity("EMAIL", "john@example.com")
    assert is_valid is True, "john@example.com should be valid"
    print("  ✓ validate_entity('EMAIL', 'john@example.com')")

    # Phone
    is_valid, conf = validate_entity("PHONE_NUMBER", "(555) 123-4567", "phone_us_ca")
    assert is_valid is True, "(555) 123-4567 should be valid"
    print("  ✓ validate_entity('PHONE_NUMBER', '(555) 123-4567')")

    # Credit card
    is_valid, conf = validate_entity("CREDIT_CARD", "4111111111111111")
    assert is_valid is False, "4111111111111111 should be invalid"
    print("  ✓ validate_entity('CREDIT_CARD', '4111111111111111')")

    # IBAN
    is_valid, conf = validate_entity("IBAN", "DE89370400440532013000")
    assert is_valid is True, "DE89370400440532013000 should be valid"
    print("  ✓ validate_entity('IBAN', 'DE89370400440532013000')")

    # Unknown type
    is_valid, conf = validate_entity("UNKNOWN", "value")
    assert is_valid is True, "Unknown type should pass"
    assert conf == 85, f"Expected 85, got {conf}"
    print("  ✓ validate_entity('UNKNOWN', 'value')")

    # Case insensitive
    is_valid, conf = validate_entity("ssn", "000-00-0000")
    assert is_valid is False, "ssn should work lowercase"
    print("  ✓ validate_entity is case insensitive")


def run_all_tests():
    """Run all tests."""
    try:
        test_ssn_validation()
        test_email_validation()
        test_phone_validation()
        test_credit_card_validation()
        test_iban_validation()
        test_public_api()
        print("\n" + "="*50)
        print("ALL TESTS PASSED! ✓")
        print("="*50)
        return True
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
