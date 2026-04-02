"""
Medical ID pattern definitions.

Health-related identification numbers from major countries.
"""

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
