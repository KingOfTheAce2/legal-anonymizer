"""
Financial pattern definitions.

Credit card and bank account patterns with global coverage.
"""

# =============================================================================
# CREDIT CARD PATTERNS
# =============================================================================

CREDIT_CARD_PATTERNS = [
    # Visa: 4xxx xxxx xxxx xxxx
    (r"\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD", 95, "cc_visa"),
    # Mastercard: 5xxx or 2xxx
    (r"\b(?:5[1-5]\d{2}|2[2-7]\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD", 95, "cc_mastercard"),
    # American Express: 3xxx xxxxxx xxxxx
    (r"\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b", "CREDIT_CARD", 95, "cc_amex"),
    # Discover
    (r"\b6(?:011|5\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD", 95, "cc_discover"),
    # JCB (Japan)
    (r"\b35(?:2[89]|[3-8]\d)[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD", 95, "cc_jcb"),
    # UnionPay (China): starts with 62
    (r"\b62\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD", 95, "cc_unionpay"),
    # Diners Club
    (r"\b3(?:0[0-5]|[68]\d)\d[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2}\b", "CREDIT_CARD", 95, "cc_diners"),
    # Generic 16 digit card
    (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "CREDIT_CARD", 85, "cc_generic"),
]

# =============================================================================
# BANK ACCOUNT / IBAN PATTERNS - GLOBAL
# =============================================================================

BANK_ACCOUNT_PATTERNS = [
    # === IBAN (Europe & others) ===
    (r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", "BANK_ACCOUNT", 95, "iban"),
    (r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\s?[A-Z0-9]{1,4}\b", "BANK_ACCOUNT", 95, "iban_spaced"),
    # Country-specific IBANs - Western Europe
    (r"\bNL\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{2}\b", "BANK_ACCOUNT", 98, "iban_nl"),
    (r"\bDE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b", "BANK_ACCOUNT", 98, "iban_de"),
    (r"\bGB\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b", "BANK_ACCOUNT", 98, "iban_uk"),
    (r"\bFR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_fr"),
    (r"\bBE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_be"),
    (r"\bAT\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_at"),
    (r"\bLU\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_lu"),
    (r"\bIE\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b", "BANK_ACCOUNT", 98, "iban_ie"),
    # Country-specific IBANs - Southern Europe
    (r"\bES\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_es"),
    (r"\bIT\d{2}\s?[A-Z]\d{3}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_it"),
    (r"\bPT\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_pt"),
    (r"\bGR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_gr"),
    (r"\bMT\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_mt"),
    (r"\bCY\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_cy"),
    # Country-specific IBANs - Northern Europe
    (r"\bSE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_se"),
    (r"\bDK\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b", "BANK_ACCOUNT", 98, "iban_dk"),
    (r"\bFI\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b", "BANK_ACCOUNT", 98, "iban_fi"),
    (r"\bNO\d{2}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_no"),
    (r"\bEE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_ee"),
    (r"\bLV\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_lv"),
    (r"\bLT\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_lt"),
    # Country-specific IBANs - Central/Eastern Europe
    (r"\bPL\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_pl"),
    (r"\bCZ\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_cz"),
    (r"\bSK\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_sk"),
    (r"\bHU\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_hu"),
    (r"\bRO\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_ro"),
    (r"\bBG\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b", "BANK_ACCOUNT", 98, "iban_bg"),
    (r"\bHR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{1}\b", "BANK_ACCOUNT", 98, "iban_hr"),
    (r"\bSI\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_si"),
    # Country-specific IBANs - Middle East
    (r"\bSA\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "BANK_ACCOUNT", 98, "iban_saudi"),
    (r"\bAE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b", "BANK_ACCOUNT", 98, "iban_uae"),

    # UK Sort Code + Account: 00-00-00 12345678
    (r"\b\d{2}-\d{2}-\d{2}\s?\d{8}\b", "BANK_ACCOUNT", 90, "uk_bank_account"),

    # US Routing + Account
    (r"\b\d{9}\s?\d{8,17}\b", "BANK_ACCOUNT", 75, "us_bank_account"),

    # SWIFT/BIC code: 8 or 11 characters (bank code + ISO country code + location + optional branch)
    # Uses (?-i:...) to enforce case-sensitive matching (SWIFT codes are always uppercase)
    # and ISO country code at positions 5-6 to prevent matching English words
    (
        r"(?-i:\b[A-Z]{4}"
        r"(?:AD|AE|AF|AG|AL|AM|AO|AR|AT|AU|AZ|BA|BB|BD|BE|BF|BG|BH|BI|BN|BO|BR|BS|BT|BW|BY|BZ"
        r"|CA|CD|CF|CG|CH|CI|CM|CN|CO|CR|CU|CV|CY|CZ|DE|DJ|DK|DM|DO|DZ|EC|EE|EG|ER|ES|ET"
        r"|FI|FJ|FO|FR|GA|GB|GD|GE|GH|GI|GL|GM|GN|GQ|GR|GT|GW|GY|HK|HN|HR|HT|HU"
        r"|ID|IE|IL|IN|IQ|IR|IS|IT|JM|JO|JP|KE|KG|KH|KI|KM|KN|KP|KR|KW|KY|KZ"
        r"|LA|LB|LC|LI|LK|LR|LS|LT|LU|LV|LY|MA|MC|MD|ME|MG|MH|MK|ML|MM|MN|MO|MR|MT|MU|MV|MW|MX|MY|MZ"
        r"|NA|NE|NG|NI|NL|NO|NP|NR|NZ|OM|PA|PE|PG|PH|PK|PL|PR|PS|PT|PW|PY|QA|RO|RS|RU|RW"
        r"|SA|SB|SC|SD|SE|SG|SH|SI|SK|SL|SM|SN|SO|SR|SS|ST|SV|SY|SZ|TC|TG|TH|TJ|TL|TM|TN|TO|TR|TT|TV|TZ"
        r"|UA|UG|US|UY|UZ|VA|VC|VE|VG|VN|VU|WS|YE|ZA|ZM|ZW)"
        r"[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b)",
        "BANK_ACCOUNT", 90, "swift_bic"
    ),

    # === ASIA ===
    # China bank account: 16-19 digits
    (r"\b\d{16,19}\b", "BANK_ACCOUNT", 70, "bank_china"),
    # Japan bank account: 7 digits
    (r"\b\d{7}\b", "BANK_ACCOUNT", 60, "bank_japan"),
    # India bank account: 9-18 digits + IFSC
    (r"\b[A-Z]{4}0[A-Z0-9]{6}\b", "BANK_ACCOUNT", 90, "ifsc_india"),

    # === AFRICA ===
    # South Africa bank: 10-11 digits
    (r"\b\d{10,11}\b", "BANK_ACCOUNT", 65, "bank_southafrica"),
]
