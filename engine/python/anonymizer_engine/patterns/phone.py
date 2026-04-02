"""
Phone number pattern definitions.

Comprehensive global phone number formats for all major countries and regions.

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
"""

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
