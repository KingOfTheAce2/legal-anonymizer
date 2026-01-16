"""
Comprehensive Global PII Detection Patterns

This module contains regex patterns for detecting various types of
Personally Identifiable Information (PII) across ALL global jurisdictions.

Coverage:
- Americas (US, Canada, Brazil, Mexico, Argentina, Colombia, Chile, Peru)
- Europe - Full EU27 Coverage:
  * Western: Germany, France, Netherlands, Belgium, Austria, Luxembourg, Ireland
  * Southern: Spain, Italy, Portugal, Greece, Malta, Cyprus
  * Northern: Sweden, Denmark, Finland, Estonia, Latvia, Lithuania
  * Central/Eastern: Poland, Czech Republic, Slovakia, Hungary, Romania, Bulgaria, Croatia, Slovenia
  * Plus: UK, Switzerland, Norway
- Asia (China, Japan, Korea, India, Singapore, Hong Kong, Taiwan, Indonesia, Malaysia,
       Thailand, Vietnam, Philippines, Pakistan, Bangladesh)
- Africa (South Africa, Nigeria, Kenya, Egypt, Morocco, Algeria)
- Middle East (UAE, Saudi Arabia, Israel, Turkey)
- Oceania (Australia, New Zealand)
- Russia & CIS (Russia, Ukraine)

Patterns are organized by entity type and include:
- Email addresses
- Phone numbers (international formats)
- National IDs (all major countries)
- Passport numbers
- Credit cards (with Luhn validation)
- Bank accounts (IBAN, SWIFT, regional formats)
- IP addresses (IPv4 and IPv6)
- Dates (multiple formats including Asian)
- Addresses (global formats)
- Vehicle IDs / License plates
- Medical IDs
- URLs and usernames
- Tax IDs
"""

import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Result of a pattern match."""
    start: int
    end: int
    entity_type: str
    value: str
    confidence: int
    pattern_name: str


# =============================================================================
# EMAIL PATTERNS
# =============================================================================

EMAIL_PATTERNS = [
    # Standard email
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "EMAIL", 95, "email_standard"),
]

# =============================================================================
# PHONE NUMBER PATTERNS - GLOBAL
# =============================================================================

PHONE_PATTERNS = [
    # International format with + prefix
    (r"\+\d{1,4}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}", "PHONE_NUMBER", 90, "phone_international"),

    # === AMERICAS ===
    # US/Canada: (123) 456-7890 or 123-456-7890
    (r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "PHONE_NUMBER", 90, "phone_us_ca"),
    # Brazil: +55 11 91234-5678
    (r"\+55\s?\d{2}\s?\d{4,5}[-.]?\d{4}\b", "PHONE_NUMBER", 90, "phone_brazil"),
    # Mexico: +52 55 1234 5678
    (r"\+52\s?\d{2,3}\s?\d{4}\s?\d{4}\b", "PHONE_NUMBER", 90, "phone_mexico"),

    # === EUROPE ===
    # UK format: 07xxx xxxxxx or +44 7xxx xxxxxx
    (r"\b0\d{4}\s?\d{6}\b", "PHONE_NUMBER", 85, "phone_uk"),
    (r"\+44\s?7\d{3}\s?\d{6}\b", "PHONE_NUMBER", 90, "phone_uk_intl"),
    # European format: +31 6 12345678, +49 xxx xxxxx
    (r"\+\d{2}\s?\d{1,3}\s?\d{6,8}\b", "PHONE_NUMBER", 90, "phone_eu"),
    # France: 06 12 34 56 78
    (r"\b0[67]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\b", "PHONE_NUMBER", 90, "phone_france"),

    # === ASIA ===
    # China: +86 1xx xxxx xxxx or 1xx-xxxx-xxxx
    (r"\+86\s?1[3-9]\d\s?\d{4}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_china"),
    (r"\b1[3-9]\d[-\s]?\d{4}[-\s]?\d{4}\b", "PHONE_NUMBER", 85, "phone_china_local"),
    # Japan: +81 90-1234-5678 or 090-1234-5678
    (r"\+81\s?[789]0[-\s]?\d{4}[-\s]?\d{4}\b", "PHONE_NUMBER", 95, "phone_japan"),
    (r"\b0[789]0[-\s]?\d{4}[-\s]?\d{4}\b", "PHONE_NUMBER", 90, "phone_japan_local"),
    # South Korea: +82 10-1234-5678
    (r"\+82\s?10[-\s]?\d{4}[-\s]?\d{4}\b", "PHONE_NUMBER", 95, "phone_korea"),
    (r"\b010[-\s]?\d{4}[-\s]?\d{4}\b", "PHONE_NUMBER", 90, "phone_korea_local"),
    # India: +91 98765 43210
    (r"\+91\s?[6-9]\d{4}\s?\d{5}\b", "PHONE_NUMBER", 95, "phone_india"),
    (r"\b[6-9]\d{4}\s?\d{5}\b", "PHONE_NUMBER", 85, "phone_india_local"),
    # Singapore: +65 9123 4567
    (r"\+65\s?[89]\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_singapore"),
    # Hong Kong: +852 9123 4567
    (r"\+852\s?[5-9]\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_hongkong"),
    # Taiwan: +886 9xx xxx xxx
    (r"\+886\s?9\d{2}[-\s]?\d{3}[-\s]?\d{3}\b", "PHONE_NUMBER", 95, "phone_taiwan"),
    # Indonesia: +62 8xx-xxxx-xxxx
    (r"\+62\s?8\d{2}[-\s]?\d{4}[-\s]?\d{3,4}\b", "PHONE_NUMBER", 95, "phone_indonesia"),
    # Malaysia: +60 1x-xxx xxxx
    (r"\+60\s?1[0-9][-\s]?\d{3,4}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_malaysia"),
    # Thailand: +66 8x-xxx-xxxx
    (r"\+66\s?[89]\d[-\s]?\d{3}[-\s]?\d{4}\b", "PHONE_NUMBER", 95, "phone_thailand"),
    # Vietnam: +84 9x xxx xx xx
    (r"\+84\s?[389]\d\s?\d{3}\s?\d{2}\s?\d{2}\b", "PHONE_NUMBER", 95, "phone_vietnam"),
    # Philippines: +63 9xx xxx xxxx
    (r"\+63\s?9\d{2}\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_philippines"),

    # === MIDDLE EAST ===
    # UAE: +971 5x xxx xxxx
    (r"\+971\s?5[0-9]\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_uae"),
    # Saudi Arabia: +966 5x xxx xxxx
    (r"\+966\s?5[0-9]\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_saudi"),
    # Israel: +972 5x-xxx-xxxx
    (r"\+972\s?5[0-9][-\s]?\d{3}[-\s]?\d{4}\b", "PHONE_NUMBER", 95, "phone_israel"),

    # === AFRICA ===
    # South Africa: +27 xx xxx xxxx
    (r"\+27\s?\d{2}\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_southafrica"),
    # Nigeria: +234 xxx xxx xxxx
    (r"\+234\s?\d{3}\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_nigeria"),
    # Kenya: +254 7xx xxx xxx
    (r"\+254\s?7\d{2}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_kenya"),
    # Egypt: +20 1x xxxx xxxx
    (r"\+20\s?1[0-2]\s?\d{4}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_egypt"),

    # === OCEANIA ===
    # Australia: +61 4xx xxx xxx
    (r"\+61\s?4\d{2}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_australia"),
    # New Zealand: +64 2x xxx xxxx
    (r"\+64\s?2[0-9]\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_newzealand"),

    # === RUSSIA & CIS ===
    # Russia: +7 9xx xxx-xx-xx
    (r"\+7\s?9\d{2}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b", "PHONE_NUMBER", 95, "phone_russia"),
    (r"\b8\s?9\d{2}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b", "PHONE_NUMBER", 90, "phone_russia_local"),
    # Ukraine: +380 xx xxx xx xx
    (r"\+380\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b", "PHONE_NUMBER", 95, "phone_ukraine"),

    # === TURKEY ===
    # Turkey: +90 5xx xxx xx xx
    (r"\+90\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b", "PHONE_NUMBER", 95, "phone_turkey"),
    (r"\b05\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b", "PHONE_NUMBER", 90, "phone_turkey_local"),

    # === SOUTH AMERICA ===
    # Argentina: +54 9 11 xxxx-xxxx
    (r"\+54\s?9?\s?\d{2,4}\s?\d{4}[-\s]?\d{4}\b", "PHONE_NUMBER", 95, "phone_argentina"),
    # Colombia: +57 3xx xxx xxxx
    (r"\+57\s?3\d{2}\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_colombia"),
    # Chile: +56 9 xxxx xxxx
    (r"\+56\s?9\s?\d{4}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_chile"),
    # Peru: +51 9xx xxx xxx
    (r"\+51\s?9\d{2}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_peru"),

    # === SOUTH ASIA ===
    # Pakistan: +92 3xx xxxxxxx
    (r"\+92\s?3\d{2}[-\s]?\d{7}\b", "PHONE_NUMBER", 95, "phone_pakistan"),
    (r"\b03\d{2}[-\s]?\d{7}\b", "PHONE_NUMBER", 90, "phone_pakistan_local"),
    # Bangladesh: +880 1xxx-xxxxxx
    (r"\+880\s?1\d{3}[-\s]?\d{6}\b", "PHONE_NUMBER", 95, "phone_bangladesh"),

    # === NORDICS ===
    # Sweden: +46 7x xxx xx xx
    (r"\+46\s?7\d[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b", "PHONE_NUMBER", 95, "phone_sweden"),
    (r"\b07\d[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b", "PHONE_NUMBER", 90, "phone_sweden_local"),
    # Norway: +47 4xx xx xxx or 9xx xx xxx
    (r"\+47\s?[49]\d{2}\s?\d{2}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_norway"),
    # Denmark: +45 xx xx xx xx
    (r"\+45\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\b", "PHONE_NUMBER", 95, "phone_denmark"),
    # Finland: +358 4x xxx xxxx
    (r"\+358\s?4\d\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_finland"),

    # === OTHER EU ===
    # Austria: +43 6xx xxxxxx
    (r"\+43\s?6\d{2}\s?\d{6}\b", "PHONE_NUMBER", 95, "phone_austria"),
    # Portugal: +351 9xx xxx xxx
    (r"\+351\s?9\d{2}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_portugal"),
    # Greece: +30 6xx xxx xxxx
    (r"\+30\s?6\d{2}\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_greece"),
    # Ireland: +353 8x xxx xxxx
    (r"\+353\s?8\d\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_ireland"),
    # Czech Republic: +420 xxx xxx xxx
    (r"\+420\s?\d{3}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_czech"),
    # Romania: +40 7xx xxx xxx
    (r"\+40\s?7\d{2}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_romania"),
    # Hungary: +36 xx xxx xxxx
    (r"\+36\s?\d{2}\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_hungary"),
    # Poland: +48 xxx xxx xxx
    (r"\+48\s?\d{3}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_poland"),
    # Bulgaria: +359 xx xxx xxxx
    (r"\+359\s?\d{2}\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_bulgaria"),
    # Croatia: +385 9x xxx xxxx
    (r"\+385\s?9\d\s?\d{3}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_croatia"),
    # Cyprus: +357 9x xxxxxx
    (r"\+357\s?9\d\s?\d{6}\b", "PHONE_NUMBER", 95, "phone_cyprus"),
    # Estonia: +372 xxxx xxxx
    (r"\+372\s?\d{4}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_estonia"),
    # Latvia: +371 2x xxx xxx
    (r"\+371\s?2\d\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_latvia"),
    # Lithuania: +370 6xx xxxxx
    (r"\+370\s?6\d{2}\s?\d{5}\b", "PHONE_NUMBER", 95, "phone_lithuania"),
    # Luxembourg: +352 6xx xxx xxx
    (r"\+352\s?6\d{2}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_luxembourg"),
    # Malta: +356 99xx xxxx
    (r"\+356\s?99\d{2}\s?\d{4}\b", "PHONE_NUMBER", 95, "phone_malta"),
    # Slovakia: +421 9xx xxx xxx
    (r"\+421\s?9\d{2}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_slovakia"),
    # Slovenia: +386 xx xxx xxx
    (r"\+386\s?\d{2}\s?\d{3}\s?\d{3}\b", "PHONE_NUMBER", 95, "phone_slovenia"),

    # === NORTH AFRICA ===
    # Morocco: +212 6xx-xxxxxx
    (r"\+212\s?6\d{2}[-\s]?\d{6}\b", "PHONE_NUMBER", 95, "phone_morocco"),
    # Algeria: +213 x xx xx xx xx
    (r"\+213\s?\d\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\b", "PHONE_NUMBER", 95, "phone_algeria"),

    # Generic international (fallback)
    (r"\b\+?\d[\d\s().-]{8,}\d\b", "PHONE_NUMBER", 75, "phone_generic"),
]

# =============================================================================
# NATIONAL ID PATTERNS - GLOBAL
# =============================================================================

NATIONAL_ID_PATTERNS = [
    # === AMERICAS ===
    # US Social Security Number: XXX-XX-XXXX
    (r"\b\d{3}-\d{2}-\d{4}\b", "NATIONAL_ID", 95, "ssn_us"),
    # Canada SIN: XXX-XXX-XXX
    (r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b", "NATIONAL_ID", 85, "sin_canada"),
    # Brazil CPF: XXX.XXX.XXX-XX
    (r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "NATIONAL_ID", 95, "cpf_brazil"),
    # Mexico CURP: 18 alphanumeric
    (r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b", "NATIONAL_ID", 95, "curp_mexico"),

    # === EUROPE ===
    # Netherlands BSN: 9 digits with checksum
    (r"\b\d{9}\b", "NATIONAL_ID", 70, "bsn_nl"),
    # UK National Insurance: AB123456C
    (r"\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b", "NATIONAL_ID", 95, "nino_uk"),
    # German Tax ID (Steuer-ID): 11 digits
    (r"\b\d{11}\b", "NATIONAL_ID", 60, "steuer_id_de"),
    # Spanish NIE: X1234567L
    (r"\b[XYZ]\d{7}[A-Z]\b", "NATIONAL_ID", 95, "nie_spain"),
    # Spanish DNI: 12345678A
    (r"\b\d{8}[A-Z]\b", "NATIONAL_ID", 90, "dni_spain"),
    # French INSEE: 15 digits
    (r"\b[12]\d{2}(?:0[1-9]|1[0-2])\d{2}\d{3}\d{3}\d{2}\b", "NATIONAL_ID", 95, "insee_france"),
    # Belgian National Number: YY.MM.DD-XXX.XX
    (r"\b\d{2}\.\d{2}\.\d{2}-\d{3}\.\d{2}\b", "NATIONAL_ID", 95, "rn_belgium"),
    # Italian Codice Fiscale: 16 chars alphanumeric
    (r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b", "NATIONAL_ID", 95, "cf_italy"),
    # Swiss AHV: 756.XXXX.XXXX.XX
    (r"\b756\.\d{4}\.\d{4}\.\d{2}\b", "NATIONAL_ID", 95, "ahv_swiss"),
    # Polish PESEL: 11 digits
    (r"\b\d{11}\b", "NATIONAL_ID", 70, "pesel_poland"),

    # === ASIA ===
    # China ID Card: 18 digits (last can be X)
    (r"\b\d{17}[\dXx]\b", "NATIONAL_ID", 95, "id_china"),
    # China ID: 15 digit old format
    (r"\b\d{15}\b", "NATIONAL_ID", 80, "id_china_old"),
    # Japan My Number: 12 digits
    (r"\b\d{4}\s?\d{4}\s?\d{4}\b", "NATIONAL_ID", 85, "mynumber_japan"),
    # South Korea RRN: YYMMDD-XXXXXXX
    (r"\b\d{6}[-\s]?\d{7}\b", "NATIONAL_ID", 95, "rrn_korea"),
    # India Aadhaar: 12 digits (4-4-4 format)
    (r"\b\d{4}\s?\d{4}\s?\d{4}\b", "NATIONAL_ID", 85, "aadhaar_india"),
    # India PAN: AAAAA1234A
    (r"\b[A-Z]{5}\d{4}[A-Z]\b", "NATIONAL_ID", 95, "pan_india"),
    # Singapore NRIC/FIN: S1234567A
    (r"\b[STFG]\d{7}[A-Z]\b", "NATIONAL_ID", 95, "nric_singapore"),
    # Hong Kong ID: X123456(A)
    (r"\b[A-Z]{1,2}\d{6}\([0-9A]\)\b", "NATIONAL_ID", 95, "hkid_hongkong"),
    (r"\b[A-Z]{1,2}\d{6}[0-9A]\b", "NATIONAL_ID", 90, "hkid_hongkong_alt"),
    # Taiwan ID: A123456789
    (r"\b[A-Z][12]\d{8}\b", "NATIONAL_ID", 95, "id_taiwan"),
    # Malaysia NRIC: YYMMDD-XX-XXXX
    (r"\b\d{6}[-\s]?\d{2}[-\s]?\d{4}\b", "NATIONAL_ID", 90, "nric_malaysia"),
    # Indonesia NIK: 16 digits
    (r"\b\d{16}\b", "NATIONAL_ID", 85, "nik_indonesia"),
    # Thailand ID: 13 digits (X-XXXX-XXXXX-XX-X)
    (r"\b\d[-\s]?\d{4}[-\s]?\d{5}[-\s]?\d{2}[-\s]?\d\b", "NATIONAL_ID", 95, "id_thailand"),
    (r"\b\d{13}\b", "NATIONAL_ID", 80, "id_thailand_plain"),
    # Vietnam CCCD: 12 digits
    (r"\b\d{12}\b", "NATIONAL_ID", 75, "cccd_vietnam"),
    # Philippines SSS: XX-XXXXXXX-X or PSN
    (r"\b\d{2}[-\s]?\d{7}[-\s]?\d\b", "NATIONAL_ID", 90, "sss_philippines"),

    # === MIDDLE EAST ===
    # UAE Emirates ID: 784-XXXX-XXXXXXX-X
    (r"\b784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d\b", "NATIONAL_ID", 95, "eid_uae"),
    # Saudi Arabia ID: 10 digits starting with 1 or 2
    (r"\b[12]\d{9}\b", "NATIONAL_ID", 85, "id_saudi"),
    # Israel ID: 9 digits
    (r"\b\d{9}\b", "NATIONAL_ID", 70, "id_israel"),

    # === AFRICA ===
    # South Africa ID: 13 digits YYMMDDSSSSCAZ
    (r"\b\d{6}\d{4}[01]\d{2}\b", "NATIONAL_ID", 95, "id_southafrica"),
    # Nigeria NIN: 11 digits
    (r"\b\d{11}\b", "NATIONAL_ID", 75, "nin_nigeria"),
    # Nigeria BVN: 11 digits
    (r"\b\d{11}\b", "NATIONAL_ID", 75, "bvn_nigeria"),
    # Kenya ID: 8 digits
    (r"\b\d{8}\b", "NATIONAL_ID", 70, "id_kenya"),
    # Egypt ID: 14 digits
    (r"\b\d{14}\b", "NATIONAL_ID", 85, "id_egypt"),

    # === OCEANIA ===
    # Australia TFN: 8-9 digits
    (r"\b\d{3}\s?\d{3}\s?\d{2,3}\b", "NATIONAL_ID", 70, "tfn_australia"),
    # New Zealand IRD: XX-XXX-XXX
    (r"\b\d{2}[-\s]?\d{3}[-\s]?\d{3}\b", "NATIONAL_ID", 85, "ird_newzealand"),

    # === RUSSIA & CIS ===
    # Russia Internal Passport: XX XX XXXXXX
    (r"\b\d{2}\s?\d{2}\s?\d{6}\b", "NATIONAL_ID", 85, "passport_russia_internal"),
    # Russia SNILS (pension): XXX-XXX-XXX XX
    (r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\s?\d{2}\b", "NATIONAL_ID", 90, "snils_russia"),
    # Russia INN (personal): 12 digits
    (r"\b\d{12}\b", "NATIONAL_ID", 70, "inn_russia_personal"),
    # Ukraine INN: 10 digits
    (r"\b\d{10}\b", "NATIONAL_ID", 70, "inn_ukraine"),

    # === TURKEY ===
    # Turkey TC Kimlik: 11 digits starting with non-zero
    (r"\b[1-9]\d{10}\b", "NATIONAL_ID", 90, "tc_kimlik_turkey"),

    # === SOUTH AMERICA ===
    # Argentina DNI: 8 digits
    (r"\b\d{8}\b", "NATIONAL_ID", 70, "dni_argentina"),
    # Argentina CUIL/CUIT: XX-XXXXXXXX-X
    (r"\b(?:20|23|24|27|30|33|34)[-\s]?\d{8}[-\s]?\d\b", "NATIONAL_ID", 95, "cuil_argentina"),
    # Colombia CC (Cédula): 8-10 digits
    (r"\b\d{8,10}\b", "NATIONAL_ID", 65, "cc_colombia"),
    # Chile RUT: XX.XXX.XXX-X
    (r"\b\d{1,2}\.?\d{3}\.?\d{3}[-]?[\dkK]\b", "NATIONAL_ID", 90, "rut_chile"),
    # Peru DNI: 8 digits
    (r"\b\d{8}\b", "NATIONAL_ID", 70, "dni_peru"),

    # === SOUTH ASIA ===
    # Pakistan CNIC: XXXXX-XXXXXXX-X
    (r"\b\d{5}[-\s]?\d{7}[-\s]?\d\b", "NATIONAL_ID", 95, "cnic_pakistan"),
    # Bangladesh NID: 10, 13, or 17 digits
    (r"\b\d{10}\b", "NATIONAL_ID", 70, "nid_bangladesh_10"),
    (r"\b\d{13}\b", "NATIONAL_ID", 80, "nid_bangladesh_13"),
    (r"\b\d{17}\b", "NATIONAL_ID", 85, "nid_bangladesh_17"),

    # === NORDICS ===
    # Sweden Personnummer: YYMMDD-XXXX or YYYYMMDD-XXXX
    (r"\b\d{6}[-+]?\d{4}\b", "NATIONAL_ID", 90, "personnummer_sweden"),
    (r"\b\d{8}[-+]?\d{4}\b", "NATIONAL_ID", 95, "personnummer_sweden_full"),
    # Norway Fødselsnummer: DDMMYYXXXXX (11 digits)
    (r"\b\d{11}\b", "NATIONAL_ID", 75, "fodselsnummer_norway"),
    # Denmark CPR: DDMMYY-XXXX
    (r"\b\d{6}[-]?\d{4}\b", "NATIONAL_ID", 90, "cpr_denmark"),
    # Finland Henkilötunnus: DDMMYY-XXXX or DDMMYYAXXXX
    (r"\b\d{6}[-+A]\d{3}[\dA-Z]\b", "NATIONAL_ID", 95, "hetu_finland"),

    # === OTHER EU ===
    # Austria Sozialversicherungsnummer: XXXX DDMMYY
    (r"\b\d{4}\s?\d{6}\b", "NATIONAL_ID", 80, "svnr_austria"),
    # Portugal NIF: 9 digits
    (r"\b\d{9}\b", "NATIONAL_ID", 70, "nif_portugal"),
    # Greece AFM: 9 digits
    (r"\b\d{9}\b", "NATIONAL_ID", 70, "afm_greece"),
    # Ireland PPS: XXXXXXXFA (7 digits + 1-2 letters)
    (r"\b\d{7}[A-Z]{1,2}\b", "NATIONAL_ID", 95, "pps_ireland"),
    # Czech Rodné číslo: YYMMDD/XXXX
    (r"\b\d{6}/?\d{3,4}\b", "NATIONAL_ID", 90, "rc_czech"),
    # Romania CNP: 13 digits starting with 1-8
    (r"\b[1-8]\d{12}\b", "NATIONAL_ID", 95, "cnp_romania"),
    # Hungary Personal ID: XXXXXX-XXXX
    (r"\b\d{6}[-]?\d{4}\b", "NATIONAL_ID", 85, "id_hungary"),

    # === REMAINING EU MEMBER STATES ===
    # Bulgaria EGN: 10 digits (YYMMDDXXXXC)
    (r"\b\d{10}\b", "NATIONAL_ID", 70, "egn_bulgaria"),
    # Croatia OIB: 11 digits
    (r"\b\d{11}\b", "NATIONAL_ID", 75, "oib_croatia"),
    # Cyprus ID: 1-10 digits
    (r"\b\d{1,10}\b", "NATIONAL_ID", 60, "id_cyprus"),
    # Estonia Isikukood: 11 digits (GYYMMDDXXXC)
    (r"\b[1-6]\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{4}\b", "NATIONAL_ID", 95, "isikukood_estonia"),
    # Latvia Personas kods: DDMMYY-XXXXX (11 digits with dash)
    (r"\b\d{6}[-]?\d{5}\b", "NATIONAL_ID", 90, "pk_latvia"),
    # Lithuania Asmens kodas: 11 digits (GYYMMDDXXXXC)
    (r"\b[3-6]\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{4}\b", "NATIONAL_ID", 95, "ak_lithuania"),
    # Luxembourg National ID: 13 digits (YYYYMMDDXXXXX)
    (r"\b\d{4}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{5}\b", "NATIONAL_ID", 95, "nin_luxembourg"),
    # Malta ID: 7 digits + 1 letter
    (r"\b\d{7}[A-Z]\b", "NATIONAL_ID", 95, "id_malta"),
    # Slovakia Rodné číslo: YYMMDD/XXXX (same format as Czech)
    (r"\b\d{6}/?\d{3,4}\b", "NATIONAL_ID", 90, "rc_slovakia"),
    # Slovenia EMŠO: 13 digits
    (r"\b\d{13}\b", "NATIONAL_ID", 80, "emso_slovenia"),

    # === NORTH AFRICA ===
    # Morocco CIN: 1-2 letters + 6 digits
    (r"\b[A-Z]{1,2}\d{6}\b", "NATIONAL_ID", 85, "cin_morocco"),
    # Algeria NIN: 18 digits
    (r"\b\d{18}\b", "NATIONAL_ID", 80, "nin_algeria"),
]

# =============================================================================
# PASSPORT PATTERNS - GLOBAL
# =============================================================================

PASSPORT_PATTERNS = [
    # Generic passport: 1-2 letters + 6-9 digits
    (r"\b[A-Z]{1,2}\d{6,9}\b", "PASSPORT_NUMBER", 75, "passport_generic"),
    # US Passport: 9 digits
    (r"\b\d{9}\b", "PASSPORT_NUMBER", 60, "passport_us"),
    # UK Passport: 9 digits
    (r"\b\d{9}\b", "PASSPORT_NUMBER", 60, "passport_uk"),
    # German Passport: 10 alphanumeric
    (r"\b[CFGHJKLMNPRTVWXYZ0-9]{10}\b", "PASSPORT_NUMBER", 80, "passport_de"),
    # China Passport: E/G + 8 digits
    (r"\b[EGeg]\d{8}\b", "PASSPORT_NUMBER", 90, "passport_china"),
    # Japan Passport: 2 letters + 7 digits
    (r"\b[A-Z]{2}\d{7}\b", "PASSPORT_NUMBER", 85, "passport_japan"),
    # India Passport: 1 letter + 7 digits
    (r"\b[A-Z]\d{7}\b", "PASSPORT_NUMBER", 80, "passport_india"),
    # South Korea Passport: 1 letter + 8 digits
    (r"\b[A-Z]\d{8}\b", "PASSPORT_NUMBER", 85, "passport_korea"),
]

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

    # SWIFT/BIC code: 8 or 11 characters
    (r"\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b", "BANK_ACCOUNT", 90, "swift_bic"),

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
# MEDICAL ID PATTERNS - GLOBAL
# =============================================================================

MEDICAL_ID_PATTERNS = [
    # UK NHS Number: 10 digits (3-3-4)
    (r"\b\d{3}\s?\d{3}\s?\d{4}\b", "MEDICAL_ID", 80, "nhs_uk"),
    # US Medicare: 1A12-A12-A123
    (r"\b\d[A-Z]\d{2}-?[A-Z]\d{2}-?[A-Z]\d{3}\b", "MEDICAL_ID", 90, "medicare_us"),
    # Generic medical record number
    (r"\b(?:MRN|Medical\s+Record|Patient\s+ID|病历号|カルテ番号)[\s:#]*\d{6,12}\b", "MEDICAL_ID", 95, "mrn_generic"),
    # Australia Medicare: XXXX XXXXX X
    (r"\b\d{4}\s?\d{5}\s?\d\b", "MEDICAL_ID", 85, "medicare_australia"),
    # Canada Health Card (Ontario): XXXX-XXX-XXX
    (r"\b\d{4}[-\s]?\d{3}[-\s]?\d{3}\b", "MEDICAL_ID", 85, "health_card_canada"),
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


# =============================================================================
# PATTERN COMPILATION AND DETECTION
# =============================================================================

# Combine all patterns
ALL_PATTERNS: Dict[str, List[Tuple[str, str, int, str]]] = {
    "EMAIL": EMAIL_PATTERNS,
    "PHONE_NUMBER": PHONE_PATTERNS,
    "NATIONAL_ID": NATIONAL_ID_PATTERNS,
    "PASSPORT_NUMBER": PASSPORT_PATTERNS,
    "CREDIT_CARD": CREDIT_CARD_PATTERNS,
    "BANK_ACCOUNT": BANK_ACCOUNT_PATTERNS,
    "IP_ADDRESS": IP_ADDRESS_PATTERNS,
    "DATE": DATE_PATTERNS,
    "DATE_OF_BIRTH": DATE_OF_BIRTH_PATTERNS,
    "ADDRESS": ADDRESS_PATTERNS,
    "VEHICLE_ID": VEHICLE_PATTERNS,
    "MEDICAL_ID": MEDICAL_ID_PATTERNS,
    "ACCOUNT_USERNAME": ONLINE_PATTERNS,
    "MONEY": MONEY_PATTERNS,
    "TAX_ID": TAX_ID_PATTERNS,
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
                pass  # Skip invalid patterns silently

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
