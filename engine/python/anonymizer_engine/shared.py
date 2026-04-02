"""
Shared utilities for all detection layers.

This module contains common functions and constants used across
Layer 1, Layer 2, and Layer 3 detection engines.
"""

import logging
from typing import Dict

# Configure logging for user-visible messages
logger = logging.getLogger("anonymizer")

# Entity priority mapping - determines how aggressively each entity type is handled
# Higher priority = more likely to be redacted vs pseudonymised
PRIORITY: Dict[str, int] = {
    # Priority 100: Always redact - highest risk identifiers
    "NATIONAL_ID": 100,
    "PASSPORT_NUMBER": 100,
    "MEDICAL_ID": 100,
    # Priority 90: Always redact - financial identifiers
    "BANK_ACCOUNT": 90,
    "CREDIT_CARD": 90,
    # Priority 80: Default pseudonymise - personal identifiers
    "PERSON": 80,
    "DATE_OF_BIRTH": 80,
    "EMAIL": 80,
    "PHONE_NUMBER": 80,
    "VEHICLE_ID": 80,
    # Priority 70: Default redact - location data
    "ADDRESS": 70,
    "IP_ADDRESS": 70,
    # Priority 60: Configurable - organizational data
    "ORGANIZATION": 60,
    "LOCATION": 60,
    "ACCOUNT_USERNAME": 60,
    # Priority 40 and below: Optional
    "DATE": 40,
    "MONEY": 30,
    "URL": 20,
}


def get_context(text: str, start: int, end: int, span: int = 30) -> str:
    """
    Extract context snippet around a detected entity.

    Shows surrounding text to help lawyers understand the detection context.

    Args:
        text: Full text being analyzed
        start: Start position of detected entity
        end: End position of detected entity
        span: Number of characters to include before/after (default 30)

    Returns:
        Context snippet with entity and surrounding text
    """
    context_start = max(0, start - span)
    context_end = min(len(text), end + span)
    return text[context_start:context_end]


def mask_value(value: str) -> str:
    """
    Mask a sensitive value, showing only first and last 2 characters.

    Used for uncertain detections where full redaction isn't warranted
    but the value shouldn't be fully visible.

    Examples:
        "john@example.com" -> "jo************om"
        "12345" -> "12*45"
        "ABC" -> "***"

    Args:
        value: The sensitive value to mask

    Returns:
        Masked version of the value
    """
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


class DetectionError(Exception):
    """Exception raised when a detection layer encounters an error."""

    def __init__(self, layer: str, message: str, cause: Exception = None):
        self.layer = layer
        self.message = message
        self.cause = cause
        super().__init__(f"[{layer}] {message}")


def log_detection_warning(layer: str, message: str, exception: Exception = None):
    """
    Log a warning about detection issues.

    These warnings are shown to users so they understand when
    detection accuracy may be reduced.

    Args:
        layer: Which detection layer (Layer 1, Layer 2, Layer 3)
        message: Human-readable description of the issue
        exception: Optional underlying exception for debugging
    """
    full_message = f"[{layer}] {message}"
    if exception:
        full_message += f" (Technical details: {type(exception).__name__}: {exception})"
    logger.warning(full_message)


def log_detection_error(layer: str, message: str, exception: Exception = None):
    """
    Log an error that prevents detection from working properly.

    These errors indicate something went wrong that lawyers should know about.

    Args:
        layer: Which detection layer (Layer 1, Layer 2, Layer 3)
        message: Human-readable description of the error
        exception: Optional underlying exception for debugging
    """
    full_message = f"[{layer}] {message}"
    if exception:
        full_message += f" (Technical details: {type(exception).__name__}: {exception})"
    logger.error(full_message)
