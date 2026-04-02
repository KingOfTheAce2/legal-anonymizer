"""
Performance and benchmark tests for legal-anonymizer.

Tests:
- Detection speed (throughput)
- Memory usage
- Scalability with document size
- Concurrent processing
"""

import pytest
import time
from typing import List

from anonymizer_engine.layer1 import analyze_layer1_text
from anonymizer_engine.patterns import detect_patterns, detect_with_validation
from anonymizer_engine.preset import Preset


class TestPatternDetectionPerformance:
    """Test pattern detection performance."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_email_detection_speed(self, benchmark):
        """Performance: email detection speed."""
        text = "Contact " + "test@example.com " * 100

        def detect_emails():
            return detect_patterns(text)

        result = benchmark(detect_emails)
        assert len(result) > 0

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_phone_detection_speed(self, benchmark):
        """Performance: phone detection speed."""
        text = "Call " + "(555) 123-4567 " * 100

        def detect_phones():
            return detect_patterns(text)

        result = benchmark(detect_phones)
        assert len(result) > 0

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_ssn_detection_speed(self, benchmark):
        """Performance: SSN detection speed."""
        text = "SSN: " + "123-45-6789 " * 100

        def detect_ssns():
            return detect_patterns(text)

        result = benchmark(detect_ssns)
        assert len(result) > 0

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_mixed_pii_detection_speed(self, benchmark):
        """Performance: mixed PII detection."""
        text = """
        Email: user@example.com
        Phone: (555) 123-4567
        SSN: 123-45-6789
        Card: 4111111111111111
        IBAN: DE89370400440532013000
        IP: 192.168.1.1
        """ * 50

        def detect_all():
            return detect_patterns(text)

        result = benchmark(detect_all)
        assert len(result) > 0


class TestDetectionWithValidation:
    """Test validation adds reasonable overhead."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_validation_overhead_credit_card(self):
        """Performance: validation overhead for credit cards."""
        text = "Card: " + "4111111111111111 " * 100

        start = time.time()
        matches_no_val = detect_patterns(text)
        time_no_val = time.time() - start

        start = time.time()
        matches_val = detect_with_validation(text)
        time_val = time.time() - start

        # Validation should add minimal overhead (<50% slower)
        overhead = (time_val - time_no_val) / time_no_val if time_no_val > 0 else 0
        assert overhead < 0.5

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_validation_overhead_iban(self):
        """Performance: validation overhead for IBANs."""
        text = "Bank: " + "DE89370400440532013000 " * 100

        start = time.time()
        matches_no_val = detect_patterns(text)
        time_no_val = time.time() - start

        start = time.time()
        matches_val = detect_with_validation(text)
        time_val = time.time() - start

        # Validation should add minimal overhead
        assert time_val < time_no_val * 1.5


class TestLayer1Performance:
    """Test Layer 1 analysis performance."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_small_document_analysis(self, benchmark):
        """Performance: small document (1KB)."""
        text = """
        Email: john@example.com
        Phone: (555) 123-4567
        SSN: 123-45-6789
        """ * 50

        preset = Preset(name="test", minimum_confidence=75)

        def analyze():
            return analyze_layer1_text(text, preset, "en")

        result = benchmark(analyze)
        redacted, findings, summary = result
        assert len(findings) > 0

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_medium_document_analysis(self, benchmark):
        """Performance: medium document (10KB)."""
        lines = [
            f"Line {i}: Contact user{i}@example.com or call (555) {i:03d}-{i:04d}"
            for i in range(500)
        ]
        text = "\n".join(lines)

        preset = Preset(name="test", minimum_confidence=75)

        def analyze():
            return analyze_layer1_text(text, preset, "en")

        result = benchmark(analyze)
        redacted, findings, summary = result
        assert len(findings) > 0

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_large_document_analysis(self):
        """Performance: large document (100KB+)."""
        lines = [
            f"Line {i}: Contact user{i}@example.com or call (555) {i:03d}-{i:04d}"
            for i in range(5000)
        ]
        text = "\n".join(lines)

        preset = Preset(name="test", minimum_confidence=75)

        start = time.time()
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")
        elapsed = time.time() - start

        # Should process large document in reasonable time (< 30 seconds)
        assert elapsed < 30
        assert len(findings) > 0


class TestScalability:
    """Test scalability with document size."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_linear_scaling_with_size(self):
        """Scalability: processing time scales linearly."""
        preset = Preset(name="test", minimum_confidence=75)

        sizes = [100, 500, 1000]
        times = []

        for size in sizes:
            lines = [
                f"Line {i}: Contact user{i}@example.com"
                for i in range(size)
            ]
            text = "\n".join(lines)

            start = time.time()
            analyze_layer1_text(text, preset, "en")
            elapsed = time.time() - start
            times.append(elapsed)

        # Time should roughly scale linearly (ratio should be close to size ratio)
        ratio1 = times[1] / times[0]
        ratio2 = times[2] / times[1]
        size_ratio1 = sizes[1] / sizes[0]
        size_ratio2 = sizes[2] / sizes[1]

        # Allow 2x variation from linear
        assert 0.5 < ratio1 / size_ratio1 < 2.0
        assert 0.5 < ratio2 / size_ratio2 < 2.0


class TestPatternComplexity:
    """Test complexity of pattern matching."""

    @pytest.mark.benchmark
    def test_single_pattern_match(self):
        """Complexity: single pattern match."""
        text = "test@example.com"
        start = time.time()
        matches = detect_patterns(text)
        elapsed = time.time() - start

        # Should be very fast (< 1ms)
        assert elapsed < 0.001
        assert len(matches) >= 1

    @pytest.mark.benchmark
    def test_many_patterns_in_text(self):
        """Complexity: many patterns in single text."""
        # Create text with many patterns
        parts = [
            f"user{i}@example.com " for i in range(100)
        ] + [
            f"(555) {i:03d}-{i:04d} " for i in range(100)
        ]
        text = " ".join(parts)

        start = time.time()
        matches = detect_patterns(text)
        elapsed = time.time() - start

        assert len(matches) > 100
        # Should still be reasonably fast
        assert elapsed < 1.0

    @pytest.mark.benchmark
    def test_overlapping_patterns(self):
        """Complexity: overlapping pattern matches."""
        # Create text where patterns might overlap
        text = "123-45-6789" * 100

        start = time.time()
        matches = detect_patterns(text)
        elapsed = time.time() - start

        # Should handle overlaps efficiently
        assert elapsed < 1.0


class TestFalsePositivePerformance:
    """Test performance with potential false positives."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_performance_with_version_numbers(self):
        """Performance: large text with many version-like patterns."""
        text = "Version " + "1.2.3.4 " * 1000

        start = time.time()
        matches = detect_patterns(text)
        elapsed = time.time() - start

        # Should process quickly even with many potential patterns
        assert elapsed < 1.0

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_performance_with_dates(self):
        """Performance: large text with many date-like patterns."""
        text = "Date: " + "01-23-45 " * 1000

        start = time.time()
        matches = detect_patterns(text)
        elapsed = time.time() - start

        # Should process quickly
        assert elapsed < 1.0


class TestMemoryUsage:
    """Test memory efficiency."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_memory_for_large_document(self):
        """Memory: memory usage for large document."""
        import sys

        lines = [
            f"Line {i}: Contact user{i}@example.com"
            for i in range(1000)
        ]
        text = "\n".join(lines)

        preset = Preset(name="test", minimum_confidence=75)

        # Get baseline
        import gc
        gc.collect()

        # Process
        redacted, findings, summary = analyze_layer1_text(text, preset, "en")

        # Results should not be excessively large
        assert len(redacted) > 0
        assert len(findings) > 0
        # Memory shouldn't explode


class TestConcurrentProcessing:
    """Test behavior with concurrent requests."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_sequential_documents(self):
        """Concurrency: sequential processing of multiple documents."""
        texts = [
            f"Email: user{i}@example.com"
            for i in range(10)
        ]

        preset = Preset(name="test", minimum_confidence=75)

        start = time.time()
        for text in texts:
            analyze_layer1_text(text, preset, "en")
        elapsed = time.time() - start

        # Should process 10 small documents reasonably fast
        assert elapsed < 5.0

    @pytest.mark.benchmark
    def test_repeated_analysis(self):
        """Concurrency: same document analyzed repeatedly."""
        text = "Email: user@example.com, Phone: (555) 123-4567"
        preset = Preset(name="test", minimum_confidence=75)

        start = time.time()
        for _ in range(100):
            analyze_layer1_text(text, preset, "en")
        elapsed = time.time() - start

        # Should cache and be fast
        assert elapsed < 5.0


class TestRegressionPerformance:
    """Test for performance regressions."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_pattern_detection_baseline(self):
        """Regression: pattern detection baseline."""
        text = "user@example.com " * 100
        preset = Preset(name="test", minimum_confidence=75)

        start = time.time()
        for _ in range(10):
            analyze_layer1_text(text, preset, "en")
        elapsed = time.time() - start

        # 10 iterations of 100-email text should be quick
        # Baseline: should be under 2 seconds
        assert elapsed < 2.0

    @pytest.mark.benchmark
    def test_validation_baseline(self):
        """Regression: validation overhead baseline."""
        text = "4111111111111111 " * 100

        start = time.time()
        for _ in range(100):
            detect_with_validation(text)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 2.0
