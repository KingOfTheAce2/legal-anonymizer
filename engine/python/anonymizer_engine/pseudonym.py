from typing import Dict, Tuple, List

# ---------------------------------------------------------------------------
# Realistic pseudonym pools
# Names drawn from common EU first names + neutral last names.
# ---------------------------------------------------------------------------

_PERSONS: List[Tuple[str, str]] = [
    ("James", "Wilson"),       ("Maria", "Mueller"),    ("Robert", "Johnson"),
    ("Sarah", "Schmidt"),      ("Michael", "Taylor"),   ("Emma", "Garcia"),
    ("David", "Anderson"),     ("Sophie", "Martinez"),  ("Thomas", "Brown"),
    ("Laura", "Davis"),        ("Alexander", "Harris"), ("Christina", "Lewis"),
    ("Matthew", "Clark"),      ("Hannah", "Robinson"),  ("Christopher", "Walker"),
    ("Catherine", "Hall"),     ("Jonathan", "Allen"),   ("Victoria", "Young"),
    ("Benjamin", "King"),      ("Elizabeth", "Wright"), ("Nicolas", "Dupont"),
    ("Isabelle", "Bernard"),   ("Marco", "Rossi"),      ("Giulia", "Ferrari"),
    ("Erik", "Johansson"),     ("Anna", "Lindqvist"),   ("Piotr", "Kowalski"),
    ("Katarzyna", "Nowak"),    ("Jan", "Novak"),        ("Eva", "Horvath"),
]

_ORGS: List[str] = [
    "Acme Corporation",        "Global Services Ltd",   "Northern Consulting Group",
    "Atlantic Partners",       "Summit Advisory Group", "Meridian Holdings",
    "Apex Solutions",          "Cornerstone Associates","Lighthouse Ventures",
    "Pinnacle Capital",        "Horizon Group",         "Sterling & Partners",
    "Westgate Advisors",       "Crestwood Legal",       "Blueline Associates",
]

_LOCATIONS: List[str] = [
    "Springfield", "Riverside", "Lakewood", "Fairview", "Burlington",
    "Greenfield",  "Maplewood", "Oakdale",  "Hillcrest", "Westfield",
    "Clearwater",  "Eastbrook", "Northgate","Millbrook",  "Stonehaven",
]

_EMAIL_DOMAINS: List[str] = [
    "example.com", "mailbox.net", "corp-example.org", "testmail.eu",
]

_STREETS: List[str] = [
    "Oak Street", "Maple Avenue", "Elm Road", "Cedar Lane",
    "Pine Drive",  "Birch Way",   "Ash Court", "Willow Close",
]


class PseudonymMapper:
    """
    Maps detected PII values to stable pseudonyms within a single document run.

    Same input value always returns the same pseudonym (consistent replacement),
    but two different values of the same entity type get different pseudonyms.

    style:
        "neutral"   — ENTITY_001, ENTITY_002, … (default, format-neutral)
        "realistic" — James Wilson, j.wilson@example.com, … (human-readable)
    """

    def __init__(self, style: str = "neutral") -> None:
        self._style = style
        self._counters: Dict[str, int] = {}
        self._mapping: Dict[str, str] = {}

    def pseudonymise(self, entity_type: str, value: str) -> str:
        key = f"{entity_type}:{value}"

        if key in self._mapping:
            return self._mapping[key]

        count = self._counters.get(entity_type, 0) + 1
        self._counters[entity_type] = count

        token = (
            self._realistic(entity_type, count)
            if self._style == "realistic"
            else f"{entity_type}_{count:03d}"
        )

        self._mapping[key] = token
        return token

    # ------------------------------------------------------------------
    # Realistic generator
    # ------------------------------------------------------------------

    def _realistic(self, entity_type: str, count: int) -> str:
        idx = (count - 1) % len(_PERSONS)
        first, last = _PERSONS[idx]

        if entity_type == "PERSON":
            return f"{first} {last}"

        if entity_type in ("EMAIL", "EMAIL_ADDRESS"):
            domain = _EMAIL_DOMAINS[(count - 1) % len(_EMAIL_DOMAINS)]
            return f"{first[0].lower()}.{last.lower()}@{domain}"

        if entity_type in ("PHONE_NUMBER", "PHONE"):
            return f"+1-555-{count:04d}"

        if entity_type == "ORGANIZATION":
            return _ORGS[(count - 1) % len(_ORGS)]

        if entity_type in ("LOCATION", "CITY", "GPE", "COUNTRY"):
            return _LOCATIONS[(count - 1) % len(_LOCATIONS)]

        if entity_type == "ADDRESS":
            street = _STREETS[(count - 1) % len(_STREETS)]
            city = _LOCATIONS[(count - 1) % len(_LOCATIONS)]
            return f"{count * 7 + 10} {street}, {city}"

        if entity_type in ("DATE", "DATE_TIME"):
            year  = 1975 + (count % 25)
            month = (count % 12) + 1
            day   = (count % 28) + 1
            return f"{year:04d}-{month:02d}-{day:02d}"

        if entity_type == "DATE_OF_BIRTH":
            year  = 1960 + (count % 35)
            month = (count % 12) + 1
            day   = (count % 28) + 1
            return f"{year:04d}-{month:02d}-{day:02d}"

        if entity_type in ("NATIONAL_ID", "US_SSN", "NRP"):
            return f"XXX-XX-{count:04d}"

        if entity_type in ("CREDIT_CARD", "CREDIT_CARD_NUMBER"):
            return f"**** **** **** {count:04d}"

        if entity_type == "IBAN":
            return f"GB{count:02d}XXXX{count:08d}"

        if entity_type == "IP_ADDRESS":
            return f"10.0.{(count >> 4) & 0xFF}.{count & 0xFF}"

        if entity_type in ("URL", "DOMAIN_NAME"):
            return f"https://example-{count:03d}.com"

        if entity_type == "MONEY":
            return f"${count * 1000:,}"

        if entity_type in ("BANK_ACCOUNT", "US_BANK_NUMBER"):
            return f"****{count:04d}"

        if entity_type == "VEHICLE_ID":
            return f"XX{count:04d}"

        if entity_type == "PASSPORT_NUMBER":
            return f"XX{count:07d}"

        # Fallback for any unrecognised entity type
        return f"{entity_type}_{count:03d}"
