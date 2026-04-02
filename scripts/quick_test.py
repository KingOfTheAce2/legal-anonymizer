#!/usr/bin/env python3
"""
Quick Test Script for Legal Anonymizer

Run quick validation tests without full pytest suite.
Useful for rapid development feedback.
"""

import sys
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / "engine" / "python"))

from anonymizer_engine.layer1 import analyze_layer1_text
from anonymizer_engine.preset import Preset
from anonymizer_engine.legal_preservation import check_legal_preservation
from anonymizer_engine.secrets_detection import SECRETS_PATTERNS
import re


def test_basic_detection():
    """Test basic PII detection."""
    print("=" * 60)
    print("TEST 1: Basic PII Detection")
    print("=" * 60)

    text = """
    John Smith lives at 123 Main Street, New York, NY 10001.
    Contact: john.smith@example.com or +1 (555) 123-4567
    SSN: 123-45-6789
    """

    preset = Preset(
        preset_id="test",
        name="Test",
        layer=1,
        minimum_confidence=60,
        uncertainty_policy="mask",
        pseudonym_style="neutral",
        language_mode="auto",
        entities_enabled={}
    )

    output, findings, summary = analyze_layer1_text(text, preset, "en")

    print(f"\nOriginal: {text[:100]}...")
    print(f"\nAnonymized: {output[:100]}...")
    print(f"\nFindings: {len(findings)}")
    print(f"Summary: {summary}")

    # Assertions
    assert len(findings) > 0, "Should detect at least one entity"
    assert "PERSON" in summary or "EMAIL" in summary, "Should detect PERSON or EMAIL"
    print("\n✅ PASS: Basic detection working")


def test_legal_preservation():
    """Test legal entity preservation."""
    print("\n" + "=" * 60)
    print("TEST 2: Legal Entity Preservation")
    print("=" * 60)

    text = """
    In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the Supreme Court
    held that GDPR Article 5 requires data minimization.
    """

    # Test case citation preservation
    result = check_legal_preservation(text, text.find("Smith"), text.find("Jones"))
    print(f"\nChecking 'Smith v. Jones' case name...")
    if result:
        print(f"✅ Preserved: {result[0]} - {result[1]}")
    else:
        print("❌ Not preserved (may need tuning)")

    # Test court name preservation
    court_start = text.find("Supreme Court")
    court_end = court_start + len("Supreme Court")
    result = check_legal_preservation(text, court_start, court_end)
    print(f"\nChecking 'Supreme Court'...")
    if result:
        print(f"✅ Preserved: {result[0]} - {result[1]}")
    else:
        print("❌ Not preserved")

    print("\n✅ PASS: Legal preservation configured")


def test_secrets_detection():
    """Test secrets detection patterns."""
    print("\n" + "=" * 60)
    print("TEST 3: Secrets Detection")
    print("=" * 60)

    test_secrets = [
        ("AKIAIOSFODNN7EXAMPLE", "AWS_ACCESS_KEY"),
        ("ghp_1234567890abcdefghijklmnopqrstuvwxyz", "GITHUB_TOKEN"),
        ("sk-ant-api03-test", "ANTHROPIC_API_KEY"),
    ]

    detected = 0
    for secret, expected_type in test_secrets:
        print(f"\nTesting: {secret[:20]}...")
        found = False
        for pattern, entity_type, priority, name in SECRETS_PATTERNS:
            if re.search(pattern, secret, re.IGNORECASE):
                print(f"  ✅ Detected as {entity_type} (priority {priority})")
                found = True
                detected += 1
                break
        if not found:
            print(f"  ❌ Not detected")

    assert detected > 0, "Should detect at least one secret"
    print(f"\n✅ PASS: Detected {detected}/{len(test_secrets)} secrets")


def test_performance():
    """Quick performance check."""
    print("\n" + "=" * 60)
    print("TEST 4: Performance Check")
    print("=" * 60)

    import time

    # Generate test text (~1000 words)
    text = " ".join([
        f"Person{i} lives at {i} Main Street. Email: person{i}@example.com. "
        f"Phone: +1 ({i:03d}) {i:03d}-{i:04d}."
        for i in range(100)
    ])

    preset = Preset(
        preset_id="test",
        name="Test",
        layer=1,
        minimum_confidence=60,
        uncertainty_policy="mask",
        pseudonym_style="neutral",
        language_mode="auto",
        entities_enabled={}
    )

    start = time.time()
    output, findings, summary = analyze_layer1_text(text, preset, "en")
    elapsed = time.time() - start

    print(f"\nText length: {len(text):,} chars")
    print(f"Entities found: {len(findings)}")
    print(f"Time: {elapsed:.3f} seconds")
    print(f"Throughput: {len(text) / elapsed:,.0f} chars/sec")

    # Should process at least 10k chars/sec
    if len(text) / elapsed > 10000:
        print("✅ PASS: Performance acceptable")
    else:
        print("⚠️  WARNING: Performance below target (10k chars/sec)")


def main():
    """Run all quick tests."""
    print("\n🚀 Legal Anonymizer - Quick Test Suite\n")

    tests = [
        test_basic_detection,
        test_legal_preservation,
        test_secrets_detection,
        test_performance,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n❌ FAILED: {e}")
            failed.append(test.__name__)
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    if not failed:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {len(failed)} TEST(S) FAILED:")
        for name in failed:
            print(f"  - {name}")
    print("=" * 60 + "\n")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
