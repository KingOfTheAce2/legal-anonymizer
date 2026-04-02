"""
National ID and passport pattern definitions.

Comprehensive global coverage of:
- National identification numbers
- Passport numbers
- All major countries and regions
"""

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
