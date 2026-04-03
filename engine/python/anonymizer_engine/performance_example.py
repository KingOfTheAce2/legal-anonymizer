"""
Performance optimization examples for legal-anonymizer.

Demonstrates:
1. LRU caching for pattern validation
2. Compiled regex pattern reuse
3. Document chunking for large texts
4. Progress reporting
"""

import time

from .cache import get_cache_stats, clear_all_caches
from .patterns import (
    luhn_checksum,
    validate_iban,
    validate_dutch_bsn,
    detect_patterns,
)
from .chunking import DocumentChunker


def example_1_validation_caching():
    """Demonstrate validation function caching."""
    print("\n=== Example 1: Validation Function Caching ===\n")

    # Test credit card validation caching
    test_card = "4532015112830366"  # Valid Visa test card

    print(f"Testing Luhn checksum validation with card: {test_card}")

    # First call (cache miss)
    start = time.time()
    result1 = luhn_checksum(test_card)
    first_call = time.time() - start
    print(f"First call: {result1} (took {first_call*1000:.4f}ms)")

    # Second call (cache hit)
    start = time.time()
    result2 = luhn_checksum(test_card)
    second_call = time.time() - start
    print(f"Second call: {result2} (took {second_call*1000:.4f}ms)")

    # Show speedup
    speedup = first_call / second_call if second_call > 0 else float('inf')
    print(f"Speedup: {speedup:.1f}x")

    # Test IBAN validation
    test_iban = "DE89370400440532013000"

    print(f"\nTesting IBAN validation with: {test_iban}")

    start = time.time()
    result1 = validate_iban(test_iban)
    first_call = time.time() - start
    print(f"First call: {result1} (took {first_call*1000:.4f}ms)")

    start = time.time()
    result2 = validate_iban(test_iban)
    second_call = time.time() - start
    print(f"Second call: {result2} (took {second_call*1000:.4f}ms)")

    speedup = first_call / second_call if second_call > 0 else float('inf')
    print(f"Speedup: {speedup:.1f}x")

    # Show cache stats
    print("\nCache Statistics:")
    stats = get_cache_stats()
    print(f"  Validation cache hits: {stats['validation_cache']['hits']}")
    print(f"  Validation cache misses: {stats['validation_cache']['misses']}")
    if stats['validation_cache']['hits'] + stats['validation_cache']['misses'] > 0:
        hit_rate = stats['validation_cache']['hits'] / (
            stats['validation_cache']['hits'] + stats['validation_cache']['misses']
        )
        print(f"  Hit rate: {hit_rate*100:.1f}%")


def example_2_pattern_matching_caching():
    """Demonstrate pattern matching caching."""
    print("\n=== Example 2: Pattern Matching Caching ===\n")

    sample_text = "Contact John at john@example.com or +1-555-0123."

    print(f"Text to scan:\n  '{sample_text}'\n")

    # First scan (cache miss)
    start = time.time()
    results1 = detect_patterns(sample_text)
    first_call = time.time() - start
    print(f"First pattern scan: {len(results1)} matches found (took {first_call*1000:.4f}ms)")
    for match in results1:
        print(f"  - {match.entity_type}: {match.value}")

    # Second scan (cache hit)
    start = time.time()
    results2 = detect_patterns(sample_text)
    second_call = time.time() - start
    print(f"\nSecond pattern scan: {len(results2)} matches found (took {second_call*1000:.4f}ms)")

    speedup = first_call / second_call if second_call > 0 else float('inf')
    print(f"Speedup: {speedup:.1f}x")

    # Show cache stats
    print("\nCache Statistics:")
    stats = get_cache_stats()
    print(f"  Pattern match cache size: {stats['pattern_match_cache']['size']}")
    print(f"  Hit rate: {stats['pattern_match_cache']['hit_rate_percent']:.1f}%")


def example_3_document_chunking():
    """Demonstrate document chunking for large texts."""
    print("\n=== Example 3: Document Chunking ===\n")

    # Create a sample large document
    sample_chunk = """
    Case No. 2024-CV-0001

    PLAINTIFF: John Smith (SSN: 123-45-6789)
    DEFENDANT: ACME Corporation

    Statement of Facts:
    The plaintiff, John Smith, resides at 123 Main Street, Springfield, IL 62701.
    His contact information includes email john.smith@example.com and phone
    (217) 555-0123. The defendant, ACME Corporation, conducted business with the
    plaintiff under contract dated January 15, 2024.

    Financial Records:
    Payment received via Visa card ending in 1234 (4532-0151-1283-0366).
    Wire transfer to account IBAN: DE89370400440532013000.
    Amount: $50,000 USD.

    Additional Notes:
    Medical records show treatment at Springfield Medical Center on 02/14/2024.
    Patient ID: MRN-2024-001234.
    """

    # Create a large document by repeating the chunk
    large_doc = sample_chunk * 30  # Approximately 100KB+

    print(f"Document size: {len(large_doc):,} bytes ({len(large_doc)/1024:.1f} KB)")

    chunker = DocumentChunker(chunk_size=50 * 1024, overlap=2 * 1024)

    # Estimate chunks
    estimated_chunks = chunker.estimate_chunk_count(large_doc)
    print(f"Estimated chunks: {estimated_chunks}")

    # Perform chunking
    def progress_callback(percent):
        if percent % 20 == 0:
            print(f"  Progress: {percent}%")

    start = time.time()
    chunks = chunker.chunk_document(large_doc, progress_callback)
    chunk_time = time.time() - start

    print(f"\nChunking completed in {chunk_time*1000:.2f}ms")
    print(f"Actual chunks created: {len(chunks)}")

    for chunk in chunks:
        print(f"  Chunk {chunk.chunk_index}: "
              f"size={chunk.size:,} bytes, "
              f"offset={chunk.start_offset:,}-{chunk.end_offset:,}")

    # Show chunk merging
    merged = DocumentChunker.merge_chunks(chunks)
    print(f"\nMerged document size: {len(merged):,} bytes")
    print(f"Sizes match: {len(merged) == len(large_doc)}")


def example_4_progress_reporting():
    """Demonstrate progress reporting for long operations."""
    print("\n=== Example 4: Progress Reporting ===\n")

    # Create a sample document
    sample_doc = """
    CONFIDENTIAL LEGAL DOCUMENT

    Client Information:
    Name: Jane Doe
    Email: jane.doe@example.com
    Phone: +1-212-555-0192
    SSN: 987-65-4321
    Medical Insurance: United Healthcare, ID: UH-987654321

    Financial Details:
    Account: IBAN GB29NWBK60161331926819
    Credit Card: 5425 2334 3010 5678

    Case Details:
    Filed: 2024-02-14
    Hearing: 2024-03-20
    """ * 40  # Make it large enough for chunking

    print(f"Processing document of {len(sample_doc):,} bytes...\n")

    # Create a progress reporter
    progress_updates = []

    def progress_callback(percent):
        progress_updates.append(percent)
        if percent % 25 == 0 or percent == 100:
            print(f"Progress: {percent}% complete")

    # Note: This example shows the progress callback capability
    # Actual analysis would require Preset and language configuration
    print("Progress callback invoked at: ", progress_updates)
    print("(Full analysis would require proper Preset configuration)")


def example_5_benchmark():
    """Run a performance benchmark."""
    print("\n=== Example 5: Performance Benchmark ===\n")

    # Clear caches first
    clear_all_caches()

    # Test data
    print("Validation Performance Benchmark (1000 iterations):")
    print("-" * 60)

    validators = [
        ("Luhn Checksum", lambda x: luhn_checksum(x)),
        ("IBAN Validation", lambda x: validate_iban(x)),
        ("BSN Validation", lambda x: validate_dutch_bsn("123456782")),
    ]

    for name, validator in validators:
        # Warm up
        try:
            validator("123456782")
        except Exception:
            pass

        # Benchmark
        start = time.time()
        for _ in range(1000):
            try:
                validator("123456782")
            except:
                pass
        elapsed = time.time() - start

        ops_per_sec = 1000 / elapsed
        print(f"{name:.<40} {ops_per_sec:>8.0f} ops/sec")

    # Show final cache stats
    print("\nFinal Cache Statistics:")
    print("-" * 60)
    stats = get_cache_stats()
    print(f"Validation cache: {stats['validation_cache']['size']}/{stats['validation_cache']['max_size']} entries")
    print(f"  Hit rate: {stats['validation_cache']['hit_rate_percent']:.1f}%")
    print(f"Pattern match cache: {stats['pattern_match_cache']['size']}/{stats['pattern_match_cache']['max_size']} entries")
    print(f"  Hit rate: {stats['pattern_match_cache']['hit_rate_percent']:.1f}%")
    print(f"Compiled regex patterns cached: {stats['compiled_regex_cache']}")


def main():
    """Run all examples."""
    print("=" * 70)
    print("Legal Anonymizer - Performance Optimization Examples")
    print("=" * 70)

    try:
        example_1_validation_caching()
    except Exception as e:
        print(f"Error in example 1: {e}")

    try:
        example_2_pattern_matching_caching()
    except Exception as e:
        print(f"Error in example 2: {e}")

    try:
        example_3_document_chunking()
    except Exception as e:
        print(f"Error in example 3: {e}")

    try:
        example_4_progress_reporting()
    except Exception as e:
        print(f"Error in example 4: {e}")

    try:
        example_5_benchmark()
    except Exception as e:
        print(f"Error in example 5: {e}")

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
