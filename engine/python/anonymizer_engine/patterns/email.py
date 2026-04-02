"""
Email pattern definitions.

Standard email address detection patterns.
"""

# =============================================================================
# EMAIL PATTERNS
# =============================================================================

EMAIL_PATTERNS = [
    # Standard email
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "EMAIL", 95, "email_standard"),
]
