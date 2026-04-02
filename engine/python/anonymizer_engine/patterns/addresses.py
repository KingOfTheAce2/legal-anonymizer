"""
Address-related pattern definitions.

Includes IP addresses, dates, addresses, vehicle IDs, online identifiers, money, and tax IDs.
"""

# =============================================================================
# IP ADDRESS PATTERNS
# =============================================================================

IP_ADDRESS_PATTERNS = [
    # IPv4
    (r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b", "IP_ADDRESS", 95, "ipv4"),
    # IPv6 (simplified)
    (r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b", "IP_ADDRESS", 95, "ipv6_full"),
    (r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b", "IP_ADDRESS", 85, "ipv6_compressed"),
    (r"\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b", "IP_ADDRESS", 85, "ipv6_prefix"),
]

# =============================================================================
# DATE PATTERNS - GLOBAL
# =============================================================================

DATE_PATTERNS = [
    # ISO format: 2024-01-15
    (r"\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b", "DATE", 95, "date_iso"),
    # European: 15-01-2024 or 15/01/2024
    (r"\b(?:0[1-9]|[12]\d|3[01])[-/](?:0[1-9]|1[0-2])[-/]\d{4}\b", "DATE", 90, "date_eu"),
    # US format: 01/15/2024 or 01-15-2024
    (r"\b(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])[-/]\d{4}\b", "DATE", 85, "date_us"),
    # Short year: 15/01/24
    (r"\b(?:0[1-9]|[12]\d|3[01])[-/](?:0[1-9]|1[0-2])[-/]\d{2}\b", "DATE", 80, "date_short"),

    # Asian date formats
    # Chinese: 2024年01月15日
    (r"\b\d{4}年(?:0?[1-9]|1[0-2])月(?:0?[1-9]|[12]\d|3[01])日\b", "DATE", 95, "date_chinese"),
    # Japanese: 令和6年1月15日 or 2024年1月15日
    (r"\b(?:令和|平成|昭和)?\d{1,4}年(?:0?[1-9]|1[0-2])月(?:0?[1-9]|[12]\d|3[01])日\b", "DATE", 95, "date_japanese"),
    # Korean: 2024년 1월 15일
    (r"\b\d{4}년\s?(?:0?[1-9]|1[0-2])월\s?(?:0?[1-9]|[12]\d|3[01])일\b", "DATE", 95, "date_korean"),

    # Arabic date (day/month/year with Arabic numerals would need special handling)
    # Using Western numerals for Arabic regions
    (r"\b(?:0[1-9]|[12]\d|3[01])/(?:0[1-9]|1[0-2])/\d{4}\b", "DATE", 85, "date_arabic"),

    # Written English: January 15, 2024 or 15 January 2024
    (r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b", "DATE", 90, "date_written"),
    (r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b", "DATE", 90, "date_written_eu"),
]

# =============================================================================
# DATE OF BIRTH PATTERNS
# =============================================================================

DATE_OF_BIRTH_PATTERNS = [
    # Explicit DOB markers - multilingual
    (r"(?:DOB|D\.O\.B\.|Date\s+of\s+Birth|Geboren|Geboortedatum|Né\(e\)\s+le|Fecha\s+de\s+Nacimiento|Data\s+di\s+Nascita|出生日期|生年月日|생년월일)[\s:]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", "DATE_OF_BIRTH", 98, "dob_explicit"),
    (r"(?:born|geboren|née?|nacido|nato|出生|生まれ)[\s:]+(?:on\s+)?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", "DATE_OF_BIRTH", 95, "dob_born"),
]

# =============================================================================
# ADDRESS PATTERNS - GLOBAL
# =============================================================================

ADDRESS_PATTERNS = [
    # === AMERICAS ===
    # US street address
    (r"\b\d{1,5}\s+[A-Za-z]+(?:\s+[A-Za-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Way|Circle|Cir)\b", "ADDRESS", 85, "street_address_us"),
    # US ZIP code
    (r"\b\d{5}(?:-\d{4})?\b", "ADDRESS", 70, "zipcode_us"),
    # Canada postal code: A1A 1A1
    (r"\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b", "ADDRESS", 90, "postcode_ca"),
    # Brazil CEP: 12345-678
    (r"\b\d{5}-\d{3}\b", "ADDRESS", 90, "cep_brazil"),

    # === EUROPE ===
    # Dutch: Street Name 123
    (r"\b[A-Z][a-z]+(?:straat|weg|laan|plein|gracht|singel|kade)\s+\d{1,5}(?:\s?[a-z])?\b", "ADDRESS", 90, "street_address_nl"),
    # Dutch postcode: 1234 AB
    (r"\b\d{4}\s?[A-Z]{2}\b", "ADDRESS", 90, "postcode_nl"),
    # German: Street Name 123
    (r"\b[A-Z][a-z]+(?:straße|strasse|weg|platz|allee|gasse)\s+\d{1,5}(?:\s?[a-z])?\b", "ADDRESS", 90, "street_address_de"),
    # German postcode: 5 digits
    (r"\b\d{5}\b", "ADDRESS", 60, "postcode_de"),
    # UK postcode: SW1A 1AA
    (r"\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b", "ADDRESS", 90, "postcode_uk"),
    # France postcode: 5 digits
    (r"\b\d{5}\b", "ADDRESS", 60, "postcode_fr"),

    # === ASIA ===
    # China address pattern (Chinese characters + numbers)
    (r"\b\d{6}\b", "ADDRESS", 70, "postcode_china"),  # China postcode
    # Japan postcode: 〒123-4567 or 123-4567
    (r"\b〒?\d{3}-\d{4}\b", "ADDRESS", 90, "postcode_japan"),
    # South Korea postcode: 5 digits
    (r"\b\d{5}\b", "ADDRESS", 60, "postcode_korea"),
    # India PIN code: 6 digits
    (r"\b\d{6}\b", "ADDRESS", 70, "pin_india"),
    # Singapore postcode: 6 digits
    (r"\b\d{6}\b", "ADDRESS", 70, "postcode_singapore"),

    # === MIDDLE EAST ===
    # UAE: PO Box pattern
    (r"\b(?:P\.?O\.?\s*Box|صندوق\s*بريد)\s*\d+\b", "ADDRESS", 85, "po_box_uae"),

    # === AFRICA ===
    # South Africa postcode: 4 digits
    (r"\b\d{4}\b", "ADDRESS", 60, "postcode_southafrica"),

    # === OCEANIA ===
    # Australia postcode: 4 digits
    (r"\b\d{4}\b", "ADDRESS", 60, "postcode_australia"),

    # Generic PO Box
    (r"\b(?:P\.?O\.?\s*Box|Postbus|Postfach|Apartado|私書箱)\s*\d+\b", "ADDRESS", 85, "po_box"),
]

# =============================================================================
# VEHICLE IDENTIFICATION - GLOBAL
# =============================================================================

VEHICLE_PATTERNS = [
    # VIN: 17 characters excluding I, O, Q (global standard)
    (r"\b[A-HJ-NPR-Z0-9]{17}\b", "VEHICLE_ID", 85, "vin"),

    # === EUROPE ===
    (r"\b[A-Z]{1,3}[-\s]?\d{1,4}[-\s]?[A-Z]{1,3}\b", "VEHICLE_ID", 75, "license_plate_eu"),
    # Dutch license plate
    (r"\b\d{1,2}-[A-Z]{2,3}-[A-Z0-9]{1,2}\b", "VEHICLE_ID", 90, "license_plate_nl"),
    (r"\b[A-Z]{2}-\d{2,3}-[A-Z]{1,2}\b", "VEHICLE_ID", 90, "license_plate_nl2"),
    # UK license plate
    (r"\b[A-Z]{2}\d{2}\s?[A-Z]{3}\b", "VEHICLE_ID", 90, "license_plate_uk"),
    # German license plate
    (r"\b[A-Z]{1,3}[-\s]?[A-Z]{1,2}\s?\d{1,4}\b", "VEHICLE_ID", 85, "license_plate_de"),

    # === ASIA ===
    # China license plate (simplified - actual uses Chinese characters)
    (r"\b[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-Z0-9]{5}\b", "VEHICLE_ID", 95, "license_plate_china"),
    # Japan license plate (numbers only visible part)
    (r"\b\d{2,4}[-\s]?\d{2,4}\b", "VEHICLE_ID", 60, "license_plate_japan"),
    # India vehicle registration
    (r"\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,2}[-\s]?\d{4}\b", "VEHICLE_ID", 90, "license_plate_india"),
    # Singapore license plate
    (r"\bS[A-Z]{2}\s?\d{1,4}\s?[A-Z]\b", "VEHICLE_ID", 90, "license_plate_singapore"),

    # === MIDDLE EAST ===
    # UAE license plate
    (r"\b[A-Z]\s?\d{1,5}\b", "VEHICLE_ID", 70, "license_plate_uae"),
    # Saudi license plate
    (r"\b[A-Z]{3}\s?\d{1,4}\b", "VEHICLE_ID", 70, "license_plate_saudi"),

    # === AFRICA ===
    # South Africa license plate
    (r"\b[A-Z]{2,3}\s?\d{2,3}\s?[A-Z]{2,3}\b", "VEHICLE_ID", 80, "license_plate_southafrica"),
]

# =============================================================================
# ONLINE IDENTIFIERS
# =============================================================================

ONLINE_PATTERNS = [
    # URLs
    (r"\bhttps?://[^\s<>\"{}|\\^`\[\]]+", "URL", 95, "url"),
    # Social media handles
    (r"@[A-Za-z0-9_]{1,15}\b", "ACCOUNT_USERNAME", 80, "twitter_handle"),
    (r"@[A-Za-z0-9_.]{1,30}\b", "ACCOUNT_USERNAME", 75, "instagram_handle"),
    # WeChat ID (Chinese social media)
    (r"\b微信[号:]?\s?[A-Za-z0-9_-]{6,20}\b", "ACCOUNT_USERNAME", 85, "wechat_id"),
    # Generic username patterns
    (r"\b(?:username|user|login|account|用户名|ユーザー名)[\s:]+[A-Za-z0-9_.-]+\b", "ACCOUNT_USERNAME", 85, "username_labeled"),
]

# =============================================================================
# MONEY/CURRENCY PATTERNS - GLOBAL
# =============================================================================

MONEY_PATTERNS = [
    # === AMERICAS ===
    (r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_usd"),
    (r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?", "MONEY", 90, "currency_brl"),  # Brazilian Real
    (r"MX\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_mxn"),  # Mexican Peso

    # === EUROPE ===
    (r"€\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_eur"),
    (r"£\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_gbp"),
    (r"CHF\s?\d{1,3}(?:[',]\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_chf"),

    # === ASIA ===
    (r"¥\s?\d{1,3}(?:,\d{3})*", "MONEY", 90, "currency_cny_jpy"),  # Chinese Yuan / Japanese Yen
    (r"₩\s?\d{1,3}(?:,\d{3})*", "MONEY", 90, "currency_krw"),  # Korean Won
    (r"₹\s?\d{1,3}(?:,\d{2})*(?:,\d{3})?", "MONEY", 90, "currency_inr"),  # Indian Rupee (lakh system)
    (r"S\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_sgd"),  # Singapore Dollar
    (r"HK\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_hkd"),  # Hong Kong Dollar
    (r"NT\$\s?\d{1,3}(?:,\d{3})*", "MONEY", 90, "currency_twd"),  # Taiwan Dollar
    (r"฿\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_thb"),  # Thai Baht
    (r"₫\s?\d{1,3}(?:\.\d{3})*", "MONEY", 90, "currency_vnd"),  # Vietnamese Dong
    (r"₱\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_php"),  # Philippine Peso
    (r"Rp\s?\d{1,3}(?:\.\d{3})*", "MONEY", 90, "currency_idr"),  # Indonesian Rupiah
    (r"RM\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_myr"),  # Malaysian Ringgit

    # === MIDDLE EAST ===
    (r"(?:AED|د\.إ)\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_aed"),  # UAE Dirham
    (r"(?:SAR|ر\.س)\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_sar"),  # Saudi Riyal
    (r"₪\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_ils"),  # Israeli Shekel

    # === AFRICA ===
    (r"R\s?\d{1,3}(?:\s?\d{3})*(?:,\d{2})?", "MONEY", 85, "currency_zar"),  # South African Rand
    (r"₦\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_ngn"),  # Nigerian Naira
    (r"KSh\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_kes"),  # Kenyan Shilling
    (r"E£\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_egp"),  # Egyptian Pound

    # === OCEANIA ===
    (r"A\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_aud"),  # Australian Dollar
    (r"NZ\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", "MONEY", 90, "currency_nzd"),  # New Zealand Dollar

    # === RUSSIA & CIS ===
    (r"₽\s?\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_rub"),  # Russian Ruble
    (r"₴\s?\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_uah"),  # Ukrainian Hryvnia

    # === TURKEY ===
    (r"₺\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_try"),  # Turkish Lira

    # === SOUTH AMERICA ===
    (r"ARS?\$\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_ars"),  # Argentine Peso
    (r"CLP?\$\s?\d{1,3}(?:[.,]\d{3})*", "MONEY", 90, "currency_clp"),  # Chilean Peso
    (r"COL?\$\s?\d{1,3}(?:[.,]\d{3})*", "MONEY", 90, "currency_cop"),  # Colombian Peso
    (r"S/\.?\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_pen"),  # Peruvian Sol

    # === SOUTH ASIA ===
    (r"Rs\.?\s?\d{1,3}(?:,\d{2})*(?:,\d{3})?", "MONEY", 85, "currency_pkr"),  # Pakistani Rupee
    (r"৳\s?\d{1,3}(?:,\d{2})*(?:,\d{3})?", "MONEY", 90, "currency_bdt"),  # Bangladeshi Taka

    # === NORDICS ===
    (r"(?:SEK|kr)\s?\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_sek"),  # Swedish Krona
    (r"(?:NOK|kr)\s?\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_nok"),  # Norwegian Krone
    (r"(?:DKK|kr\.?)\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_dkk"),  # Danish Krone

    # === OTHER EU ===
    (r"(?:PLN|zł)\s?\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_pln"),  # Polish Zloty
    (r"(?:CZK|Kč)\s?\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_czk"),  # Czech Koruna
    (r"(?:HUF|Ft)\s?\d{1,3}(?:\s?\d{3})*", "MONEY", 90, "currency_huf"),  # Hungarian Forint
    (r"(?:RON|lei)\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_ron"),  # Romanian Leu
    (r"(?:BGN|лв\.?)\s?\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_bgn"),  # Bulgarian Lev

    # === NORTH AFRICA ===
    (r"(?:MAD|DH)\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_mad"),  # Moroccan Dirham
    (r"(?:DZD|DA)\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", "MONEY", 90, "currency_dzd"),  # Algerian Dinar

    # Amount with currency code (expanded - all major world currencies)
    (r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\s?(?:USD|EUR|GBP|CHF|JPY|CNY|KRW|INR|SGD|HKD|TWD|THB|VND|PHP|IDR|MYR|AED|SAR|ILS|ZAR|NGN|KES|EGP|AUD|NZD|BRL|MXN|CAD|RUB|UAH|TRY|ARS|CLP|COP|PEN|PKR|BDT|SEK|NOK|DKK|PLN|CZK|HUF|RON|BGN|HRK|MAD|DZD)\b", "MONEY", 90, "currency_coded"),
]

# =============================================================================
# TAX ID PATTERNS - GLOBAL
# =============================================================================

TAX_ID_PATTERNS = [
    # US EIN: XX-XXXXXXX
    (r"\b\d{2}-\d{7}\b", "TAX_ID", 90, "ein_us"),
    # UK VAT: GB XXX XXXX XX
    (r"\bGB\s?\d{3}\s?\d{4}\s?\d{2}\b", "TAX_ID", 95, "vat_uk"),
    # EU VAT numbers (generic)
    (r"\b[A-Z]{2}\d{8,12}\b", "TAX_ID", 85, "vat_eu"),
    # Australia ABN: XX XXX XXX XXX
    (r"\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b", "TAX_ID", 85, "abn_australia"),
    # India GSTIN: XX AAAAA XXXX X X ZX
    (r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d][A-Z]\d\b", "TAX_ID", 95, "gstin_india"),
    # China Tax ID: 18 digits
    (r"\b\d{18}\b", "TAX_ID", 75, "tax_china"),
]
