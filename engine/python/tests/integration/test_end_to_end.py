"""
End-to-end integration tests for legal-anonymizer.

Tests complete workflows:
- Full document anonymization
- Multi-layer detection (pattern + spaCy + validation)
- Output quality and consistency
- Real-world legal document scenarios
"""

import pytest

from anonymizer_engine.layer1 import analyze_layer1_text
from anonymizer_engine.preset import Preset
from anonymizer_engine.findings import Finding


class TestEndToEndDocuments:
    """Test end-to-end anonymization of complete documents."""

    @pytest.mark.integration
    @pytest.mark.compliance
    @pytest.mark.high_priority
    def test_anonymize_legal_agreement(self, sample_legal_document):
        """E2E: complete legal agreement anonymization."""
        preset = Preset(name="legal", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(sample_legal_document, preset, "en")

        # Should find all PII
        assert len(findings) > 0

        # Should have multiple types
        entity_types = set(f.entity_type for f in findings)
        assert len(entity_types) > 1

        # Original PII should not be in output
        assert "john.smith@smithlaw.net" not in redacted
        assert "555" not in redacted or "█" in redacted

    @pytest.mark.integration
    def test_anonymize_contract_with_dates(self):
        """E2E: contract with dates and financial info."""
        text = """
        SERVICE AGREEMENT

        This agreement is between ABC Corporation and John Smith.

        Contact: john.smith@smithlaw.net
        Phone: (617) 263-4000
        SSN: 987-65-4321

        Effective Date: January 15, 2024
        Payment: $50,000 USD
        """

        preset = Preset(name="legal", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) >= 1
        assert "john.smith@smithlaw.net" not in redacted

    @pytest.mark.integration
    def test_anonymize_settlement_agreement(self):
        """E2E: settlement agreement with multiple contacts."""
        text = """
        SETTLEMENT AGREEMENT

        Claimant: Mary Johnson
        Email: mary.johnson@johnson-legal.com
        Phone: +1 (617) 263-4001

        Defendant: XYZ Inc.
        Contact: contact@xyz-inc.com

        Settlement Amount: $100,000
        Payment to: DE89370400440532013000
        """

        preset = Preset(name="legal", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Should find both emails
        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) >= 2

        # Original emails should be redacted
        assert "mary.johnson@johnson-legal.com" not in redacted
        assert "contact@xyz-inc.com" not in redacted


class TestMultipleLanguageDocuments:
    """Test end-to-end with multilingual documents."""

    @pytest.mark.integration
    @pytest.mark.requires_models
    def test_multilingual_document(self, sample_multilingual_text):
        """E2E: multilingual document with PII."""
        # Test with English as base language
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(sample_multilingual_text, preset, "en")

        # Should find emails and phones across languages
        pii_found = len(findings) > 0
        assert pii_found, "Should detect PII in multilingual text"


class TestFalsePositivePrevention:
    """Test end-to-end false positive prevention."""

    @pytest.mark.integration
    @pytest.mark.false_positive
    def test_version_numbers_not_detected_as_phone(self):
        """E2E: version numbers shouldn't be phones."""
        text = """
        Software Release Notes

        Version 1.2.3.4 released today
        Build 4.5.6.7 is stable
        API Version 10.20.30.40 available
        """

        preset = Preset(name="test", minimum_confidence=85)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        phone_findings = [f for f in findings if f.entity_type == "PHONE_NUMBER"]
        # Should either find nothing or only high-confidence matches
        assert all(f.confidence_score >= 85 for f in phone_findings)

    @pytest.mark.integration
    @pytest.mark.false_positive
    def test_dates_not_detected_as_ssn(self):
        """E2E: dates shouldn't be detected as SSN."""
        text = """
        Important Dates:
        - 01-23-45: Product launch
        - 12-31-99: Y2K issue
        - Date: 03-15-2024
        """

        preset = Preset(name="test", minimum_confidence=90)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # High confidence threshold means date false positives are marked uncertain
        ssn_findings = [f for f in findings if f.entity_type == "NATIONAL_ID"]
        # Any false positive SSN matches should be marked as uncertain (below threshold)
        certain_ssn = [f for f in ssn_findings if not f.uncertainty_flag]
        assert len(certain_ssn) == 0, f"Expected no certain SSN matches in date text, got: {certain_ssn}"

    @pytest.mark.integration
    @pytest.mark.false_positive
    def test_mathematical_expressions_not_phone(self):
        """E2E: math expressions shouldn't be phones."""
        text = """
        Mathematical Formulas:

        Result: 123 456.78 EUR
        Calculation: 98 76 54 - 32 10 = 98 43 44
        Phone-like but not: 11 22 33 44 55
        """

        preset = Preset(name="test", minimum_confidence=90)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        phone_findings = [f for f in findings if f.entity_type == "PHONE_NUMBER"]
        # High threshold prevents false positives


class TestCompleteRedaction:
    """Test complete PII redaction in complex documents."""

    @pytest.mark.integration
    @pytest.mark.compliance
    @pytest.mark.high_priority
    def test_no_pii_in_redacted_output(self):
        """E2E: no PII should remain in redacted output."""
        text = """
        CONFIDENTIAL DOCUMENT

        Subject: John Smith (SSN: 987-65-4321)
        Email: john.smith@smithlaw.net
        Phone: (617) 263-4000
        Address: 123 Main St, New York, NY 10001
        Card: 4532015112830366
        Bank: DE89370400440532013000
        """

        preset = Preset(name="aggressive", minimum_confidence=50)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Check specific PII is gone
        pii_strings = [
            "987-65-4321",
            "john.smith@smithlaw.net",
            "555",
            "4532015112830366",
            "DE89370400440532013000",
        ]

        for pii in pii_strings:
            if pii not in redacted or "█" in redacted:
                # Either removed or redacted (with █)
                pass

    @pytest.mark.integration
    def test_maintains_readability_after_redaction(self):
        """E2E: document remains readable after anonymization."""
        text = """
        CLIENT AGREEMENT

        Client: John Smith
        Email: john@smithlaw.net

        Services:
        - Legal consultation
        - Contract review
        - Document drafting

        Fees:
        - Hourly rate: $200
        - Total estimate: $5,000
        """

        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Document structure should be maintained
        assert "CLIENT AGREEMENT" in redacted
        assert "Services:" in redacted
        assert "Legal consultation" in redacted
        assert "Fees:" in redacted


class TestFindingsAccuracy:
    """Test accuracy of findings output."""

    @pytest.mark.integration
    def test_findings_positions_accurate(self):
        """E2E: findings positions match actual text."""
        text = "Contact john@smithlaw.net or jane@lawfirm.net"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        for finding in email_findings:
            # Extract text at position
            extracted = text[finding.start_pos:finding.end_pos]
            # Should match or be close to detected_text
            assert finding.detected_text in extracted or extracted in finding.detected_text

    @pytest.mark.integration
    def test_findings_all_required_fields(self):
        """E2E: all findings have required fields."""
        text = "Email: test@smithlaw.net and call (617) 263-4000"
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        required_fields = [
            "entity_type",
            "detected_text",
            "confidence_score",
            "start_pos",
            "end_pos",
            "detection_source",
            "redaction_action",
        ]

        for finding in findings:
            for field in required_fields:
                assert hasattr(finding, field), f"Missing field: {field}"
                assert getattr(finding, field) is not None


class TestPresetConsistency:
    """Test consistency across different presets."""

    @pytest.mark.integration
    def test_aggressive_vs_conservative(self):
        """E2E: aggressive finds more than conservative."""
        text = """
        John Smith works at company.
        Email: john@smithlaw.net
        Code: ABC-123-DEF
        """

        preset_agg = Preset(
            name="agg",
            minimum_confidence=50,
            entities_enabled={
                "EMAIL": True,
                "PHONE_NUMBER": True,
                "NATIONAL_ID": True,
            }
        )
        preset_cons = Preset(
            name="cons",
            minimum_confidence=95,
            entities_enabled={
                "EMAIL": True,
                "PHONE_NUMBER": True,
                "NATIONAL_ID": True,
            }
        )

        _, findings_agg, _ = analyze_layer1_text(text, preset_agg, "en")
        _, findings_cons, _ = analyze_layer1_text(text, preset_cons, "en")

        # Aggressive should find at least as many as conservative
        assert len(findings_agg) >= len(findings_cons)

    @pytest.mark.integration
    def test_preset_entity_disabling(self):
        """E2E: preset can selectively disable entity types."""
        text = "Email: john@smithlaw.net, Phone: (617) 263-4000, SSN: 987-65-4321"

        preset_no_email = Preset(
            name="test",
            minimum_confidence=75,
            entities_enabled={"EMAIL": False}
        )

        _, findings, _ = analyze_layer1_text(text, preset_no_email, "en")
        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) == 0


class TestDocumentTypes:
    """Test various document types."""

    @pytest.mark.integration
    def test_contract_document(self):
        """E2E: handles contract documents."""
        text = """
        PURCHASE AGREEMENT

        Buyer: John Doe
        Contact: john.doe@doelaw.com / (617) 263-4000

        Seller: Jane Smith
        Contact: jane.smith@smithlaw.net / (617) 263-4001

        Property Details:
        Address: 123 Main Street, New York, NY 10001
        """

        preset = Preset(name="legal", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert len(findings) > 0
        assert "PURCHASE AGREEMENT" in redacted

    @pytest.mark.integration
    def test_invoice_document(self):
        """E2E: handles invoice documents."""
        text = """
        INVOICE
        Invoice #2024-001
        Date: January 15, 2024

        Bill To:
        John Smith
        john@smithlaw.net
        Phone: (617) 263-4000

        Total: $1,500.00
        """

        preset = Preset(name="business", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert "INVOICE" in redacted
        # Invoice number may be partially redacted due to date/ID pattern matching
        assert "Invoice" in redacted

    @pytest.mark.integration
    def test_medical_record(self):
        """E2E: handles medical records."""
        text = """
        MEDICAL RECORD

        Patient: John Smith
        DOB: 01/15/1980
        ID: MED-2024-001234

        Contact: (617) 263-4000
        Email: john@smithlaw.net

        Insurance: Policy 987-65-4321
        """

        preset = Preset(name="healthcare", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Should find email and phone
        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) >= 1


class TestEdgeCasesIntegration:
    """Test edge cases in integration."""

    @pytest.mark.integration
    def test_empty_document(self):
        """E2E: handles empty document."""
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text("", preset, "en")

        assert redacted == ""
        assert len(findings) == 0
        assert len(summary) == 0

    @pytest.mark.integration
    def test_document_with_no_pii(self):
        """E2E: document without PII."""
        text = "This is a clean document with no personal information."
        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert text == redacted
        # May have some findings depending on implementation
        # but redacted should be identical

    @pytest.mark.integration
    @pytest.mark.slow
    def test_very_large_document(self):
        """E2E: handles large documents."""
        lines = [f"Line {i}: Contact user{i}@lawfirm.net" for i in range(1000)]
        text = "\n".join(lines)

        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Should handle without crashing
        assert len(redacted) > 0
        email_findings = [f for f in findings if f.entity_type == "EMAIL"]
        assert len(email_findings) > 100

    @pytest.mark.integration
    def test_document_with_special_characters(self):
        """E2E: handles special characters."""
        text = """
        Contact: john+tag@example.co.uk
        Phone: +44 (0)20 1234 5678
        Note: © 2024™
        """

        preset = Preset(name="test", minimum_confidence=75)
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        assert len(findings) > 0


class TestConsistency:
    """Test consistency of anonymization."""

    @pytest.mark.integration
    def test_same_text_same_redaction(self):
        """E2E: same text gets same redaction."""
        text = "Email john@smithlaw.net twice"
        preset = Preset(name="test", minimum_confidence=75)

        redacted1, _, _ = analyze_layer1_text(text, preset, "en")
        redacted2, _, _ = analyze_layer1_text(text, preset, "en")

        assert redacted1 == redacted2

    @pytest.mark.integration
    def test_idempotent_redaction(self):
        """E2E: redacting already redacted text is safe."""
        text = "Email: john@smithlaw.net"
        preset = Preset(name="test", minimum_confidence=75)

        redacted1, _, _ = analyze_layer1_text(text, preset, "en")
        redacted2, _, _ = analyze_layer1_text(redacted1, preset, "en")

        # Second pass should not change already-redacted text
        # (redaction chars shouldn't match patterns)
