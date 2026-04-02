# Patterns Module

Comprehensive PII pattern detection for global use with 400+ patterns across 14 categories.

## Quick Start

```python
from anonymizer_engine.patterns import detect_with_validation

# Detect PII in text
matches = detect_with_validation("Email: john@example.com, Phone: +1-555-123-4567")

for match in matches:
    print(f"{match.entity_type}: {match.value} (confidence: {match.confidence}%)")
```

## Available Patterns

### Direct Imports
```python
from anonymizer_engine.patterns import (
    EMAIL_PATTERNS,
    PHONE_PATTERNS,
    NATIONAL_ID_PATTERNS,
    PASSPORT_PATTERNS,
    CREDIT_CARD_PATTERNS,
    BANK_ACCOUNT_PATTERNS,
    IP_ADDRESS_PATTERNS,
    DATE_PATTERNS,
    DATE_OF_BIRTH_PATTERNS,
    ADDRESS_PATTERNS,
    VEHICLE_PATTERNS,
    MEDICAL_ID_PATTERNS,
    ONLINE_PATTERNS,
    MONEY_PATTERNS,
    TAX_ID_PATTERNS,
)
```

### Functions
```python
from anonymizer_engine.patterns import (
    detect_patterns,           # Basic detection
    detect_with_validation,    # Detection with validation
    luhn_checksum,            # Credit card validation
    validate_iban,            # IBAN validation
    validate_dutch_bsn,       # Dutch ID validation
    validate_china_id,        # Chinese ID validation
    validate_singapore_nric,  # Singapore ID validation
)
```

### Data Classes
```python
from anonymizer_engine.patterns import PatternMatch

# PatternMatch contains:
# - start: int (position in text)
# - end: int (position in text)
# - entity_type: str (type of PII found)
# - value: str (matched text)
# - confidence: int (0-100)
# - pattern_name: str (specific pattern used)
```

## Module Organization

| Module | Patterns | Coverage |
|--------|----------|----------|
| email.py | 1 | Standard email |
| phone.py | 90+ | All major countries |
| national_ids.py | 100+ | Global ID formats |
| financial.py | 60+ | Cards, IBANs, bank accounts |
| addresses.py | 150+ | Addresses, IPs, dates, money, vehicles, tax IDs |
| medical.py | 5 | Health IDs |

See [STRUCTURE.md](./STRUCTURE.md) for detailed architecture.

## Examples

### Email Detection
```python
text = "Contact: john@example.com"
matches = detect_with_validation(text)
# -> PatternMatch with entity_type="EMAIL"
```

### Phone Numbers (Global)
```python
text = """
US: (555) 123-4567
UK: +44 7700 900000
China: +86 138 0000 0000
"""
matches = detect_with_validation(text)
# -> 3 PatternMatch objects
```

### National IDs
```python
text = "SSN: 123-45-6789, Tax ID: 12-3456789"
matches = detect_with_validation(text)
# -> 2 PatternMatch objects
```

### Credit Cards
```python
text = "Visa: 4532-1234-5678-9010"
matches = detect_with_validation(text)
# PatternMatch with validated confidence
```

### IBAN Accounts
```python
text = "Account: DE89 3704 0044 0532 0130 00"
matches = detect_with_validation(text)
# -> PatternMatch with IBAN validation
```

## Coverage by Region

### Americas
- United States: SSN, phone, postal codes, addresses, bank accounts
- Canada: SIN, postal codes, phone
- Brazil: CPF, phone, postal codes
- Mexico: CURP, phone
- Argentina: DNI, CUIL, phone
- Colombia: CC, phone
- Chile: RUT, phone
- Peru: DNI, phone

### Europe (All EU27 + UK, Switzerland, Norway)
- National IDs for all countries
- Phone numbers for all countries
- IBANs for all countries
- Postal codes for all countries
- License plates for all countries

### Asia
- China: ID card, phone, postal code
- Japan: My Number, phone, passport
- South Korea: RRN, phone
- India: Aadhaar, PAN, phone
- Singapore: NRIC, phone
- Hong Kong: ID, phone
- Taiwan: ID, phone
- Indonesia: NIK, phone
- Malaysia: NRIC, phone
- Thailand: ID, phone
- Vietnam: CCCD, phone
- Philippines: SSS, phone
- Pakistan: CNIC, phone
- Bangladesh: NID, phone

### Africa
- South Africa: ID, phone, postal code
- Nigeria: NIN, BVN, phone
- Kenya: ID, phone
- Egypt: ID, phone
- Morocco: CIN, phone
- Algeria: NIN, phone

### Middle East
- UAE: Emirates ID, phone, postal code
- Saudi Arabia: ID, phone
- Israel: ID, phone
- Turkey: TC Kimlik, phone

### Oceania
- Australia: TFN, Medicare, phone
- New Zealand: IRD, phone

### Russia & CIS
- Russia: Passport, SNILS, INN, phone
- Ukraine: INN, phone

## Validation Features

Some patterns include additional validation:

- **Credit Cards**: Luhn algorithm validation
- **IBANs**: Mod-97 checksum validation
- **China ID**: Checksum validation
- **Singapore NRIC**: Checksum validation
- **Dutch BSN**: 11-check validation

Use `detect_with_validation()` for these enhanced checks.

## Performance

- All patterns compiled once and cached globally
- O(1) pattern access
- Efficient regex matching with compiled patterns
- No performance penalty from modularization

## Adding New Patterns

1. Choose appropriate module (or create new one)
2. Add pattern tuple: `(regex, entity_type, confidence, name)`
3. Pattern automatically available through `__init__.py`

Example:
```python
# In addresses.py
TAX_ID_PATTERNS = [
    (r"\bXX-\d{7}\b", "TAX_ID", 90, "my_tax_id"),
]
```

## Files

- `base.py` - Core infrastructure
- `email.py` - Email patterns
- `phone.py` - Phone patterns (90+)
- `national_ids.py` - National IDs and passports
- `financial.py` - Credit cards and bank accounts
- `addresses.py` - Addresses and related (150+ patterns)
- `medical.py` - Medical IDs
- `__init__.py` - Module interface
- `STRUCTURE.md` - Architecture documentation
- `README.md` - This file

## Backward Compatibility

100% compatible with original patterns.py. All existing imports work unchanged:

```python
# Both work:
from anonymizer_engine.patterns import PHONE_PATTERNS
from anonymizer_engine.patterns.phone import PHONE_PATTERNS
```

## Documentation

- [STRUCTURE.md](./STRUCTURE.md) - Detailed architecture and design
- [REFACTOR_PATTERNS.md](../../REFACTOR_PATTERNS.md) - Refactoring guide
- [PATTERNS_REFACTORING_SUMMARY.md](../../PATTERNS_REFACTORING_SUMMARY.md) - Complete summary

## License

Same license as parent project.

## Support

For issues, features, or pattern additions, see the main project documentation.

---

**Total Patterns:** 400+
**Categories:** 14
**Countries:** 100+
**Status:** Production Ready
