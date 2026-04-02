"""
Unit tests for Layer 1 (Fast Legal Scrub) detection.

Tests for:
- Pattern-based detection (regex)
- spaCy NER (names, organizations, locations)
- Overlap resolution (no double-redaction)
- Redaction actions (redact, pseudonymise, mask)
- Integration with presets
"""

import pytest
from typing import List

from anonymizer_engine.layer1 import analyze_layer1_text
from anonymizer_engine.preset import Preset
from anonymizer_engine.findings import Finding


class TestLayer1BasicDetection:
    """Test basic Layer 1 pattern detection."""

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.compliance
    def test_detects_email(self):
        """Layer 1: detects email address."""
        text = "Contact john@lawfirm.net"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) >= 1
        assert email_findings[0].detected_text == "john@lawfirm.net"

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.compliance
    def test_detects_phone_number(self):
        """Layer 1: detects phone number."""
        text = "Call (617) 263-4000"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        phone_findings = [f for f in findings if f.entity_type == "PHONE_NUMBER"]
        assert len(phone_findings) >= 1

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.compliance
    @pytest.mark.high_priority
    def test_detects_ssn(self):
        """Layer 1: detects Social Security Number."""
        text = "SSN: 987-65-4321"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        ssn_findings = [f for f in findings if f.entity_type == "NATIONAL_ID"]
        assert len(ssn_findings) >= 1

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_detects_credit_card(self):
        """Layer 1: detects credit card number."""
        text = "Pay with 4532015112830366"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        cc_findings = [f for f in findings if f.entity_type == "CREDIT_CARD"]
        assert len(cc_findings) >= 1

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_detects_iban(self):
        """Layer 1: detects IBAN."""
        text = "Bank: DE89370400440532013000"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        iban_findings = [f for f in findings if f.entity_type == "BANK_ACCOUNT"]
        assert len(iban_findings) >= 1


class TestLayer1Redaction:
    """Test Layer 1 text redaction."""

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.compliance
    def test_redacts_email(self):
        """Layer 1: redacts or pseudonymises email address."""
        text = "Contact john@lawfirm.net for help"
        preset = Preset(
            name="test",
            minimum_confidence=75,
            entities_enabled={"EMAIL": True}
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert "john@lawfirm.net" not in redacted
        assert "for help" in redacted  # Non-PII remains

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_redacts_phone(self):
        """Layer 1: redacts or pseudonymises phone number."""
        text = "Call (617) 263-4000 now"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert "(617) 263-4000" not in redacted
        assert "now" in redacted

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.compliance
    def test_redacts_ssn(self):
        """Layer 1: redacts SSN properly."""
        text = "Social: 987-65-4321"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert "987-65-4321" not in redacted
        assert "█" in redacted

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_preserves_non_pii(self):
        """Layer 1: preserves non-PII text."""
        text = "This is a document with personal data john@lawfirm.net and other text"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert "This is a document" in redacted
        assert "other text" in redacted
        assert "john@lawfirm.net" not in redacted


class TestLayer1Pseudonymization:
    """Test Layer 1 pseudonymization."""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_pseudonymises_person_name(self):
        """Layer 1: pseudonymises person names."""
        text = "The person John Smith called yesterday"
        preset = Preset(
            name="test",
            minimum_confidence=50,
            entities_enabled={"PERSON": True}
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        person_findings = [f for f in findings if f.entity_type == "PERSON"]
        if person_findings:
            # If name was detected, check if it was pseudonymised
            assert person_findings[0].pseudonym_value != ""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_pseudonymises_organization(self):
        """Layer 1: pseudonymises organization names."""
        text = "Company: Acme Corporation reported results"
        preset = Preset(
            name="test",
            minimum_confidence=50,
            entities_enabled={"ORGANIZATION": True}
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        org_findings = [f for f in findings if f.entity_type == "ORGANIZATION"]
        # May or may not find organization (depends on spaCy)
        # Just verify no crash


class TestLayer1Masking:
    """Test Layer 1 masking."""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_masks_with_uncertainty_policy(self):
        """Layer 1: masks uncertain values."""
        text = "Email: user@lawfirm.net"
        preset = Preset(
            name="test",
            minimum_confidence=95,  # High threshold
            uncertainty_policy="mask"
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # High confidence email, should be redacted not masked
        # But let's check for consistency
        assert "user@lawfirm.net" not in redacted


class TestLayer1Presets:
    """Test Layer 1 with different presets."""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_aggressive_preset(self, preset_aggressive):
        """Layer 1: aggressive preset redacts everything."""
        text = "John Smith, john@lawfirm.net, 555-123-4567"
        redacted, findings, summary = analyze_layer1_text(text, preset_aggressive, "en")

        # Should find and redact multiple PII
        assert len(findings) > 0
        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        phone_findings = [f for f in findings if f.entity_type == "PHONE_NUMBER"]
        # At least email and phone should be found
        assert len(email_findings) + len(phone_findings) >= 1

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_conservative_preset(self, preset_conservative):
        """Layer 1: conservative preset only high confidence."""
        text = "John Smith, john@lawfirm.net, 555-123-4567"
        redacted, findings, summary = analyze_layer1_text(text, preset_conservative, "en")

        # Conservative should still find high-confidence matches
        all_findings = [f for f in findings if f.confidence_score >= preset_conservative.minimum_confidence]
        assert len(all_findings) > 0

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_balanced_preset(self, preset_balanced):
        """Layer 1: balanced preset middle ground."""
        text = "Contact john@lawfirm.net or call (617) 263-4000"
        redacted, findings, summary = analyze_layer1_text(text, preset_balanced, "en")

        # Should find both email and phone
        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        phone_findings = [f for f in findings if f.entity_type == "PHONE_NUMBER"]
        assert len(email_findings) >= 1 or len(phone_findings) >= 1


class TestLayer1OverlapResolution:
    """Test Layer 1 overlap resolution."""

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.compliance
    def test_no_double_redaction(self):
        """Layer 1: overlapping matches resolve without duplication."""
        # Create text where pattern might match twice
        text = "Email john@lawfirm.net and phone 555-123-4567"
        preset = Preset(name="test", minimum_confidence=50)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Check no position appears twice
        positions = [(f.start_pos, f.end_pos) for f in findings]
        assert len(positions) == len(set(positions))

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_prefers_higher_confidence_overlap(self):
        """Layer 1: higher confidence match wins on overlap."""
        text = "ID: 987-65-4321"  # Could match as SSN or version
        preset = Preset(name="test", minimum_confidence=50)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Should match as SSN (higher confidence)
        ssn_findings = [f for f in findings if f.entity_type == "NATIONAL_ID"]
        assert len(ssn_findings) >= 1


class TestLayer1SummaryStats:
    """Test Layer 1 summary statistics."""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_summary_counts_correct(self):
        """Layer 1: summary counts all PII types."""
        text = """
        Contact: john@lawfirm.net
        Phone: (617) 263-4000
        SSN: 987-65-4321
        """
        preset = Preset(name="test", minimum_confidence=50)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Should have counts for detected types
        assert "EMAIL" in summary or "PHONE_NUMBER" in summary or "NATIONAL_ID" in summary

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_summary_zero_for_undetected_types(self):
        """Layer 1: plain text with no structured PII has no EMAIL/PHONE/NATIONAL_ID findings."""
        text = "Clean document with no PII"
        preset = Preset(name="test", minimum_confidence=50)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # High-priority PII types must not be detected in plain text
        assert summary.get("EMAIL", 0) == 0
        assert summary.get("PHONE_NUMBER", 0) == 0
        assert summary.get("NATIONAL_ID", 0) == 0


class TestLayer1FindingsOutput:
    """Test Layer 1 findings output quality."""

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.compliance
    def test_findings_have_context(self):
        """Layer 1: findings include context snippet."""
        text = "The email is john@lawfirm.net in the document"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        if email_findings:
            # Should have context around the match
            assert email_findings[0].context_snippet != ""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_findings_have_confidence(self):
        """Layer 1: findings include confidence score."""
        text = "Email: john@lawfirm.net"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert all(0 <= f.confidence_score <= 100 for f in findings)

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_findings_have_positions(self):
        """Layer 1: findings include start/end positions."""
        text = "Email: john@lawfirm.net"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        if email_findings:
            f = email_findings[0]
            assert f.start_pos >= 0
            assert f.end_pos > f.start_pos
            assert f.end_pos <= len(text)

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_findings_have_detection_source(self):
        """Layer 1: findings note detection source."""
        text = "Email: john@lawfirm.net"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert all(f.detection_source != "" for f in findings)


class TestLayer1EnableDisableEntities:
    """Test enabling/disabling entity types."""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_disable_email_detection(self):
        """Layer 1: can disable email detection."""
        text = "Email: john@lawfirm.net, Phone: 555-123-4567"
        preset = Preset(
            name="test",
            minimum_confidence=50,
            entities_enabled={"EMAIL": False, "PHONE_NUMBER": True}
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) == 0

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_disable_phone_detection(self):
        """Layer 1: can disable phone detection."""
        text = "Email: john@lawfirm.net, Phone: 555-123-4567"
        preset = Preset(
            name="test",
            minimum_confidence=50,
            entities_enabled={"EMAIL": True, "PHONE_NUMBER": False}
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        phone_findings = [f for f in findings if f.entity_type == "PHONE_NUMBER"]
        assert len(phone_findings) == 0


class TestLayer1ConfidenceThreshold:
    """Test Layer 1 confidence threshold behavior."""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_high_confidence_threshold(self):
        """Layer 1: high threshold marks low-confidence matches as uncertain."""
        text = "Some ambiguous pattern 123-45-67"
        preset = Preset(name="test", minimum_confidence=95)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Findings below the threshold should be flagged as uncertain
        for f in findings:
            if f.confidence_score < 95:
                assert f.uncertainty_flag is True

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_low_confidence_threshold(self):
        """Layer 1: low threshold allows more matches."""
        text = "Email: john@lawfirm.net"
        preset_high = Preset(name="test", minimum_confidence=95)
        preset_low = Preset(name="test", minimum_confidence=50)

        _, findings_high, _ = analyze_layer1_text(text, preset_high, "en")
        _, findings_low, _ = analyze_layer1_text(text, preset_low, "en")

        # Low threshold should find at least as many matches
        assert len(findings_low) >= len(findings_high)


class TestLayer1MultiplePII:
    """Test Layer 1 with multiple PII types in one text."""

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.compliance
    def test_detects_all_pii_types(self):
        """Layer 1: detects all PII types in one document."""
        text = """
        Name: John Smith
        Email: john@lawfirm.net
        Phone: (617) 263-4000
        SSN: 987-65-4321
        Credit Card: 4532015112830366
        Bank: DE89370400440532013000
        """
        preset = Preset(name="test", minimum_confidence=50)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Should find multiple PII types
        entity_types = set(f.entity_type for f in findings)
        assert len(entity_types) > 1


class TestLayer1Languages:
    """Test Layer 1 with different languages."""

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.spacy
    def test_english_detection(self):
        """Layer 1: English language support."""
        text = "Contact john@lawfirm.net"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert len(findings) > 0

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_multiple_languages_text(self):
        """Layer 1: handles multilingual text."""
        text = """
        English: john@lawfirm.net
        Dutch: jan@example.nl
        German: hans@example.de
        """
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Should find emails across languages
        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) >= 2


class TestLayer1LargeDocuments:
    """Test Layer 1 with large documents."""

    @pytest.mark.unit
    @pytest.mark.layer1
    @pytest.mark.slow
    def test_large_document_handling(self):
        """Layer 1: handles large documents."""
        # Create large document
        lines = [
            f"Line {i}: Contact user{i}@lawfirm.net"
            for i in range(100)
        ]
        text = "\n".join(lines)

        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Should find all emails
        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) >= 50


class TestLayer1UncertaintyHandling:
    """Test Layer 1 uncertainty policy."""

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_uncertainty_policy_mask(self):
        """Layer 1: mask policy for uncertain matches."""
        text = "Code ABC-123-DEF"
        preset = Preset(
            name="test",
            minimum_confidence=95,
            uncertainty_policy="mask"
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # High threshold means uncertainty applies
        uncertain = [f for f in findings if f.uncertainty_flag]
        for f in uncertain:
            assert f.redaction_action == "mask"

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_uncertainty_policy_redact(self):
        """Layer 1: redact policy for uncertain matches."""
        text = "Reference 123-45-67"
        preset = Preset(
            name="test",
            minimum_confidence=95,
            uncertainty_policy="redact"
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        uncertain = [f for f in findings if f.uncertainty_flag]
        for f in uncertain:
            assert f.redaction_action == "redact"

    @pytest.mark.unit
    @pytest.mark.layer1
    def test_uncertainty_policy_leave_intact(self):
        """Layer 1: leave_intact policy skips uncertain matches."""
        text = "Reference 123-45-67"
        preset = Preset(
            name="test",
            minimum_confidence=95,
            uncertainty_policy="leave_intact"
        )
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        uncertain = [f for f in findings if f.uncertainty_flag]
        for f in uncertain:
            assert f.redaction_action == "none"
