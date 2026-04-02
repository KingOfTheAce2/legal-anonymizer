"""
Legal Entity Preservation Lists

Certain entities should NOT be redacted in legal documents as they are:
- Public information (court names, case citations)
- Essential for legal interpretation (statutory references)
- Already publicly disclosed (published case law)

This module provides patterns and logic to preserve such entities.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PreservationRule:
    """A rule for preserving entities in legal documents."""
    category: str
    patterns: List[str]
    description: str
    confidence: int = 100


# Court Names - Should NOT be redacted (public record)
COURT_PRESERVATION = PreservationRule(
    category="courts",
    patterns=[
        # US Courts
        r"\b(?:United States )?Supreme Court(?: of the United States)?\b",
        r"\b(?:U\.S\. )?District Court(?: for the .+)?\b",
        r"\b(?:U\.S\. )?Court of Appeals(?: for the .+)?\b",
        r"\bCircuit Court(?: of .+)?\b",
        r"\bBankruptcy Court\b",
        r"\bTax Court\b",

        # UK Courts
        r"\bSupreme Court of the United Kingdom\b",
        r"\bHigh Court of Justice\b",
        r"\bCourt of Appeal\b",
        r"\bCrown Court\b",
        r"\bMagistrates['\']? Court\b",
        r"\bEmployment (?:Appeal )?Tribunal\b",

        # EU Courts
        r"\bCourt of Justice of the European Union\b",
        r"\bEuropean Court of Justice\b",
        r"\bGeneral Court\b",
        r"\bEuropean Court of Human Rights\b",

        # Other jurisdictions
        r"\bInternational Court of Justice\b",
        r"\bPermanent Court of Arbitration\b",
    ],
    description="Court names are public and essential for legal context"
)

# Case Citations - Should NOT be redacted (public record)
CITATION_PRESERVATION = PreservationRule(
    category="citations",
    patterns=[
        # US Citations: Volume Reporter Page (Year)
        r"\b\d+\s+[A-Z](?:\.\s*)?(?:2d|3d|4th)?\s+\d+(?:\s*,\s*\d+)?\s*\(\d{4}\)",
        r"\b\d+\s+U\.S\.(?:C\.)?\s+(?:§\s*)?\d+",
        r"\b\d+\s+F\.(?:2d|3d|4th)?\s+\d+",
        r"\b\d+\s+S\.\s*Ct\.\s+\d+",

        # UK Citations: [Year] Court Abbreviation Number
        r"\[\d{4}\]\s+[A-Z]+\s+\d+",
        r"\(\d{4}\)\s+[A-Z]+\s+\d+",

        # EU Citations
        r"\bCase [CT]-\d+/\d+",
        r"\bECLI:[A-Z]{2}:[A-Z]+:\d{4}:[A-Z0-9]+",

        # General docket numbers
        r"\bNo\.\s+\d{1,2}[-–]\d+",
        r"\bCase No\.\s+[\d:A-Z-]+",
    ],
    description="Case citations are public references"
)

# Statutory References - Should NOT be redacted
STATUTE_PRESERVATION = PreservationRule(
    category="statutes",
    patterns=[
        # US Code
        r"\b\d+\s+U\.S\.C\.\s+§\s*\d+(?:[a-z])?(?:\(\w+\))*",
        r"\bUSC\s+§\s*\d+",

        # CFR (Code of Federal Regulations)
        r"\b\d+\s+C\.F\.R\.\s+§?\s*\d+(?:\.\d+)*",

        # Public Laws
        r"\bPub\.\s*L\.\s*No\.\s*\d+-\d+",

        # GDPR & EU Regulations
        r"\bGDPR\s+Article\s+\d+(?:\(\d+\))?(?:\([a-z]\))?",
        r"\bRegulation \(EU\) \d+/\d+",
        r"\bDirective \d+/\d+/EC",
        r"\bAI Act\s+Article\s+\d+",

        # UK Acts
        r"\b(?:Data Protection|Human Rights|Employment Rights) Act \d{4}",
        r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)* Act \d{4}",
    ],
    description="Statutory references are public law"
)

# Legal Terms of Art - Should NOT be redacted
LEGAL_TERMS_PRESERVATION = PreservationRule(
    category="legal_terms",
    patterns=[
        r"\b(?:plaintiff|defendant|appellant|appellee|respondent|petitioner)\b",
        r"\b(?:claimant|respondent|applicant|intervener)\b",
        r"\b(?:in re|ex parte|pro se|amicus curiae)\b",
        r"\b(?:habeas corpus|certiorari|mandamus|quo warranto)\b",
        r"\b(?:voir dire|res judicata|stare decisis)\b",
    ],
    description="Legal terms of art should be preserved",
    confidence=95
)

# Combine all preservation rules
ALL_PRESERVATION_RULES: List[PreservationRule] = [
    COURT_PRESERVATION,
    CITATION_PRESERVATION,
    STATUTE_PRESERVATION,
    LEGAL_TERMS_PRESERVATION,
]


def check_legal_preservation(
    text: str,
    start: int,
    end: int,
    context_window: int = 100
) -> Optional[Tuple[str, str, int]]:
    """
    Check if a detected entity should be preserved in legal context.

    Args:
        text: Full document text
        start: Start position of detected entity
        end: End position of detected entity
        context_window: Characters to check before/after entity

    Returns:
        Tuple of (category, description, confidence) if should be preserved,
        None otherwise
    """
    # Get context around the entity
    context_start = max(0, start - context_window)
    context_end = min(len(text), end + context_window)
    context = text[context_start:context_end]

    # Check against all preservation rules
    for rule in ALL_PRESERVATION_RULES:
        for pattern in rule.patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return (rule.category, rule.description, rule.confidence)

    return None


def is_public_case_reference(text: str, start: int, end: int) -> bool:
    """
    Quick check if entity is part of a public case reference.

    Args:
        text: Full document text
        start: Start position of entity
        end: End position of entity

    Returns:
        True if entity is part of public case reference
    """
    # Check 200 chars before and after
    context = text[max(0, start - 200):min(len(text), end + 200)]

    # Look for case citation patterns
    citation_indicators = [
        r"\bv\.\s+",  # versus in case name
        r"\[\d{4}\]",  # year in brackets
        r"\(\d{4}\)",  # year in parentheses
        r"\b\d+\s+[A-Z]\.(?:2d|3d)?\s+\d+",  # reporter citation
        r"\bCase\s+(?:No\.|C-|T-)",  # case number
    ]

    for indicator in citation_indicators:
        if re.search(indicator, context, re.IGNORECASE):
            return True

    return False


def get_preservation_summary() -> str:
    """Get a summary of all preservation rules for documentation."""
    summary = ["# Legal Entity Preservation Rules\n"]

    for rule in ALL_PRESERVATION_RULES:
        summary.append(f"\n## {rule.category.upper()}")
        summary.append(f"**Description:** {rule.description}")
        summary.append(f"**Confidence:** {rule.confidence}%")
        summary.append(f"**Patterns:** {len(rule.patterns)}")
        summary.append("\nExample patterns:")
        for pattern in rule.patterns[:3]:  # Show first 3 patterns
            summary.append(f"- `{pattern}`")

    return "\n".join(summary)


# Example usage and testing
if __name__ == "__main__":
    test_text = """
    In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the Court of Appeals held
    that GDPR Article 5 requires transparency in automated decision-making.
    See also 15 U.S.C. § 1681 for related statutory provisions.
    """

    # Test preservation check
    result = check_legal_preservation(test_text, 20, 30)  # "Jones" in case name
    if result:
        print(f"Should preserve: {result}")

    # Print preservation summary
    print("\n" + get_preservation_summary())
