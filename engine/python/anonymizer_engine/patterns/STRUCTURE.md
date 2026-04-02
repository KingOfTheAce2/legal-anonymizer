# Patterns Module Structure

## Directory Layout

```
anonymizer_engine/
└── patterns/
    ├── __init__.py              # Main export point - backward compatible
    ├── base.py                  # Core classes and functions
    ├── email.py                 # EMAIL_PATTERNS
    ├── phone.py                 # PHONE_PATTERNS (90+ global formats)
    ├── national_ids.py          # NATIONAL_ID_PATTERNS, PASSPORT_PATTERNS
    ├── financial.py             # CREDIT_CARD_PATTERNS, BANK_ACCOUNT_PATTERNS
    ├── addresses.py             # IP, DATE, ADDRESS, VEHICLE, ONLINE, MONEY, TAX patterns
    ├── medical.py               # MEDICAL_ID_PATTERNS
    └── STRUCTURE.md             # This file
```

## Module Contents

### base.py
Core infrastructure for all pattern detection:
- `PatternMatch` - Dataclass for match results
- `ALL_PATTERNS` - Master dictionary of all patterns
- Pattern compilation and caching
- Detection functions (`detect_patterns`, `detect_with_validation`)
- Validation functions (Luhn, IBAN, BSN, China ID, Singapore NRIC)

### email.py
**Size:** 406 bytes | **Patterns:** 1

Standard email address detection.

### phone.py
**Size:** 9.3 KB | **Patterns:** 90+

Comprehensive international phone number formats:
- International prefix format
- Americas (5 countries)
- Europe (28 countries)
- Asia (13 countries)
- Africa (4 countries)
- Middle East (3 countries)
- Oceania (2 countries)
- Russia & CIS (2 countries)
- Turkey (1 country)
- South America (4 countries)
- South Asia (2 countries)
- Nordics (5 countries)
- Other EU (11 countries)
- North Africa (2 countries)
- Generic fallback

### national_ids.py
**Size:** 9.9 KB | **Patterns:** 108

National identification numbers and passport numbers for:
- All countries in phone.py plus additional formats
- Regional variations (international vs local formats)
- Both current and legacy ID formats
- Specialized patterns (SSN, NIR, NIN, etc.)

Passport patterns: Generic + country-specific (8 patterns)

### financial.py
**Size:** 5.6 KB | **Patterns:** 60+

Credit card and bank account detection:

**Credit Cards (8 patterns):**
- Visa, Mastercard, American Express, Discover, JCB, UnionPay, Diners Club, Generic

**Bank Accounts:**
- Generic IBAN (2 patterns)
- Country-specific IBANs (30 patterns for EU countries)
- Regional accounts (UK sort code, US routing, SWIFT/BIC)
- Asia-specific bank formats (China, Japan, India, South Africa)

### addresses.py
**Size:** 15 KB | **Patterns:** 150+

Comprehensive address-related patterns:

**IP_ADDRESS_PATTERNS (4):**
- IPv4, IPv6 full, IPv6 compressed, IPv6 prefix

**DATE_PATTERNS (10):**
- ISO, European, US, short year
- Asian formats (Chinese, Japanese, Korean)
- Written English formats

**DATE_OF_BIRTH_PATTERNS (2):**
- Explicit DOB markers (multilingual)
- Born/nato variations with dates

**ADDRESS_PATTERNS (20):**
- Street addresses (US, Dutch, German)
- Postal codes (US, Canada, Brazil, Netherlands, Germany, UK, France, China, Japan, Korea, India, Singapore, UAE, South Africa, Australia)
- PO Box patterns

**VEHICLE_PATTERNS (15):**
- VIN (17-char format)
- License plates (Europe, Asia, Middle East, Africa)
- Generic EU format

**ONLINE_PATTERNS (5):**
- URLs, Twitter/Instagram handles
- WeChat IDs
- Generic username patterns

**MONEY_PATTERNS (60):**
- Currency symbols (45+ formats)
- Currency codes (all major world currencies)
- Regional variations

**TAX_ID_PATTERNS (6):**
- US EIN, UK VAT, EU VAT, Australia ABN, India GSTIN, China Tax ID

### medical.py
**Size:** 967 bytes | **Patterns:** 5

Medical identification numbers:
- UK NHS, US Medicare, Generic MRN
- Australia Medicare, Canada Health Card

### __init__.py
**Size:** 2.2 KB

Main export point providing:
- All pattern lists for import
- All functions for import
- `__all__` definition for explicit exports
- Complete backward compatibility with original patterns.py

## Import Examples

### Import Everything (Backward Compatible)
```python
from anonymizer_engine.patterns import (
    PatternMatch,
    detect_with_validation,
    detect_patterns,
    ALL_PATTERNS,
    EMAIL_PATTERNS,
    PHONE_PATTERNS,
    # ... any other pattern or function
)
```

### Import from Specific Modules
```python
from anonymizer_engine.patterns.phone import PHONE_PATTERNS
from anonymizer_engine.patterns.financial import CREDIT_CARD_PATTERNS, BANK_ACCOUNT_PATTERNS
from anonymizer_engine.patterns.base import detect_with_validation, PatternMatch
```

### Import Module for Organization
```python
from anonymizer_engine import patterns
patterns.detect_with_validation(text)
patterns.PHONE_PATTERNS
```

## Pattern Count Summary

| Module | Type | Count |
|--------|------|-------|
| email.py | Email | 1 |
| phone.py | Phone | 90+ |
| national_ids.py | National ID | 100+ |
| national_ids.py | Passport | 8 |
| financial.py | Credit Card | 8 |
| financial.py | Bank Account | 60+ |
| addresses.py | IP Address | 4 |
| addresses.py | Date | 10 |
| addresses.py | Date of Birth | 2 |
| addresses.py | Address | 20 |
| addresses.py | Vehicle | 15 |
| addresses.py | Online | 5 |
| addresses.py | Money | 60+ |
| addresses.py | Tax ID | 6 |
| medical.py | Medical | 5 |
| **TOTAL** | | **~400+** |

## Design Principles

1. **Modularity** - Each file handles one category
2. **Backward Compatibility** - Original API unchanged
3. **Single Responsibility** - Clear purpose for each module
4. **Scalability** - Easy to add new patterns
5. **Performance** - Same efficiency as original
6. **Organization** - Logical grouping for maintainability

## Adding New Patterns

### Add a Pattern to Existing Module
1. Edit the relevant module file (e.g., `phone.py`)
2. Add new tuple to the `XXXXX_PATTERNS` list
3. Tuple format: `(regex, entity_type, confidence, pattern_name)`
4. Pattern automatically available through `__init__.py`

### Create New Pattern Category
1. Create new file (e.g., `crypto.py`)
2. Define `CRYPTO_PATTERNS` list with tuples
3. Import in `base.py` ALL_PATTERNS
4. Re-export in `__init__.py`
5. Add to `__all__` list

### Example
```python
# In crypto.py
CRYPTO_PATTERNS = [
    (r"\b0x[a-fA-F0-9]{40}\b", "CRYPTO_WALLET", 95, "ethereum_address"),
    (r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b", "CRYPTO_WALLET", 85, "bitcoin_address"),
]
```

Then in `__init__.py`:
```python
from .crypto import CRYPTO_PATTERNS
# Add to ALL_PATTERNS in base.py
# Add to __all__
```

## Performance Notes

- All patterns are compiled once and cached globally
- No performance difference from original patterns.py
- Modularization has zero runtime cost
- Pattern matching efficiency unchanged

## Backward Compatibility

- 100% compatible with existing code
- All original function signatures preserved
- All original pattern names preserved
- Original patterns.py still exists unchanged
- No migration needed for existing code

## Testing

To test the refactored patterns:
```python
from anonymizer_engine.patterns import detect_with_validation

text = """
Email: john@example.com
Phone: +1-555-123-4567
Credit Card: 4532-1234-5678-9010
Bank Account: DE89 3704 0044 0532 0130 00
"""

matches = detect_with_validation(text)
assert len(matches) >= 4, "Should detect all 4 PII items"
```

## Files Summary

- **Total Patterns:** 400+
- **Total Lines:** ~1500 (modular, organized)
- **Original patterns.py:** 1092 lines (kept for reference)
- **Module Files:** 8 (1 main + 7 pattern categories)
- **Total Size:** ~51 KB (slightly larger due to documentation)
