"""
Base module for PII pattern detection.

Contains the PatternMatch dataclass, pattern compilation logic, and validation functions.
"""

import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

# Import pattern lists from sibling modules
from . import email
from . import phone
from . import national_ids
from . import financial
from . import addresses
from . import medical


@dataclass
class PatternMatch:
    """Result of a pattern match."""
    start: int
    end: int
    entity_type: str
    value: str
    confidence: int
    pattern_name: str


# Combine all patterns
ALL_PATTERNS: Dict[str, List[Tuple[str, str, int, str]]] = {
    "EMAIL": email.EMAIL_PATTERNS,
    "PHONE_NUMBER": phone.PHONE_PATTERNS,
    "NATIONAL_ID": national_ids.NATIONAL_ID_PATTERNS,
    "PASSPORT_NUMBER": national_ids.PASSPORT_PATTERNS,
    "CREDIT_CARD": financial.CREDIT_CARD_PATTERNS,
    "BANK_ACCOUNT": financial.BANK_ACCOUNT_PATTERNS,
    "IP_ADDRESS": addresses.IP_ADDRESS_PATTERNS,
    "DATE": addresses.DATE_PATTERNS,
    "DATE_OF_BIRTH": addresses.DATE_OF_BIRTH_PATTERNS,
    "ADDRESS": addresses.ADDRESS_PATTERNS,
    "VEHICLE_ID": addresses.VEHICLE_PATTERNS,
    "MEDICAL_ID": medical.MEDICAL_ID_PATTERNS,
    "ACCOUNT_USERNAME": addresses.ONLINE_PATTERNS,
    "MONEY": addresses.MONEY_PATTERNS,
    "TAX_ID": addresses.TAX_ID_PATTERNS,
}

# Pre-compile all patterns
_COMPILED_PATTERNS: Dict[str, List[Tuple[re.Pattern, str, int, str]]] = {}


def _compile_patterns():
    """Compile all regex patterns for efficiency."""
    global _COMPILED_PATTERNS
    if _COMPILED_PATTERNS:
        return _COMPILED_PATTERNS

    for entity_type, patterns in ALL_PATTERNS.items():
        _COMPILED_PATTERNS[entity_type] = []
        for pattern, etype, confidence, name in patterns:
            try:
                compiled = re.compile(pattern, re.IGNORECASE | re.UNICODE)
                _COMPILED_PATTERNS[entity_type].append((compiled, etype, confidence, name))
            except re.error as e:
                import warnings
                warnings.warn(
                    f"Invalid regex pattern '{name}': {e}",
                    stacklevel=2,
                )

    return _COMPILED_PATTERNS


def detect_patterns(text: str, entity_types: Optional[List[str]] = None) -> List[PatternMatch]:
    """
    Detect all PII patterns in text.

    Args:
        text: Input text to scan
        entity_types: Optional list of entity types to detect (None = all)

    Returns:
        List of PatternMatch objects
    """
    patterns = _compile_patterns()
    matches: List[PatternMatch] = []

    types_to_check = entity_types if entity_types else list(patterns.keys())

    for entity_type in types_to_check:
        if entity_type not in patterns:
            continue

        for compiled, etype, confidence, name in patterns[entity_type]:
            for match in compiled.finditer(text):
                matches.append(PatternMatch(
                    start=match.start(),
                    end=match.end(),
                    entity_type=etype,
                    value=match.group(),
                    confidence=confidence,
                    pattern_name=name,
                ))

    return matches


def luhn_checksum(card_number: str) -> bool:
    """Validate credit card number using Luhn algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d

    return checksum % 10 == 0


def validate_iban(iban: str) -> bool:
    """Validate IBAN using mod-97 algorithm."""
    iban = iban.replace(" ", "").upper()

    if len(iban) < 15 or len(iban) > 34:
        return False

    if not iban[:2].isalpha() or not iban[2:4].isdigit():
        return False

    rearranged = iban[4:] + iban[:4]

    numeric = ""
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - ord('A') + 10)
        else:
            numeric += char

    return int(numeric) % 97 == 1


def validate_dutch_bsn(bsn: str) -> bool:
    """Validate Dutch BSN (Burgerservicenummer) using 11-check."""
    bsn = bsn.replace(" ", "")

    if len(bsn) != 9 or not bsn.isdigit():
        return False

    weights = [9, 8, 7, 6, 5, 4, 3, 2, -1]
    total = sum(int(d) * w for d, w in zip(bsn, weights))

    return total % 11 == 0


def validate_china_id(id_number: str) -> bool:
    """Validate Chinese ID card number using checksum."""
    id_number = id_number.upper()

    if len(id_number) != 18:
        return False

    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    try:
        total = sum(int(id_number[i]) * weights[i] for i in range(17))
        return check_codes[total % 11] == id_number[17]
    except (ValueError, IndexError):
        return False


def validate_singapore_nric(nric: str) -> bool:
    """Validate Singapore NRIC/FIN."""
    nric = nric.upper()

    if len(nric) != 9:
        return False

    if nric[0] not in 'STFG':
        return False

    weights = [2, 7, 6, 5, 4, 3, 2]
    try:
        total = sum(int(nric[i+1]) * weights[i] for i in range(7))

        if nric[0] in 'TG':
            total += 4

        if nric[0] in 'ST':
            check_codes = 'JZIHGFEDCBA'
        else:
            check_codes = 'XWUTRQPNMLK'

        return check_codes[total % 11] == nric[8]
    except (ValueError, IndexError):
        return False


def detect_with_validation(text: str) -> List[PatternMatch]:
    """
    Detect patterns with additional validation for certain types.

    This performs extra validation (Luhn for credit cards, mod-97 for IBANs, etc.)
    and adjusts confidence scores accordingly.
    """
    matches = detect_patterns(text)
    validated: List[PatternMatch] = []

    for match in matches:
        # Validate credit cards with Luhn
        if match.entity_type == "CREDIT_CARD":
            if luhn_checksum(match.value):
                match = PatternMatch(
                    start=match.start,
                    end=match.end,
                    entity_type=match.entity_type,
                    value=match.value,
                    confidence=min(match.confidence + 5, 100),
                    pattern_name=match.pattern_name,
                )
                validated.append(match)
            continue

        # Validate IBANs
        if match.entity_type == "BANK_ACCOUNT" and "iban" in match.pattern_name.lower():
            if validate_iban(match.value):
                match = PatternMatch(
                    start=match.start,
                    end=match.end,
                    entity_type=match.entity_type,
                    value=match.value,
                    confidence=min(match.confidence + 5, 100),
                    pattern_name=match.pattern_name,
                )
            validated.append(match)
            continue

        # Validate China ID
        if match.pattern_name == "id_china" and validate_china_id(match.value):
            match = PatternMatch(
                start=match.start,
                end=match.end,
                entity_type=match.entity_type,
                value=match.value,
                confidence=min(match.confidence + 5, 100),
                pattern_name=match.pattern_name,
            )
            validated.append(match)
            continue

        # Validate Singapore NRIC
        if match.pattern_name == "nric_singapore" and validate_singapore_nric(match.value):
            match = PatternMatch(
                start=match.start,
                end=match.end,
                entity_type=match.entity_type,
                value=match.value,
                confidence=min(match.confidence + 5, 100),
                pattern_name=match.pattern_name,
            )
            validated.append(match)
            continue

        validated.append(match)

    return validated
