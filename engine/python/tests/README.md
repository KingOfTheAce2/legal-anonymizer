# Legal Anonymizer Test Suite

Comprehensive test suite for the legal-anonymizer project with focus on **legal compliance** and **PII detection accuracy**.

## Directory Structure

```
tests/
├── unit/                      # Unit tests for individual components
│   ├── test_patterns.py      # Pattern detection tests (emails, phones, IDs)
│   ├── test_layer1.py        # Layer 1 analysis tests (regex + spaCy)
│   └── __init__.py
├── integration/              # End-to-end integration tests
│   ├── test_end_to_end.py   # Complete document workflows
│   └── __init__.py
├── benchmarks/              # Performance/load tests
│   ├── test_performance.py  # Speed, memory, scalability
│   └── __init__.py
├── fixtures/                # Test data and fixtures
│   ├── test_documents.py    # Real-world sample documents
│   └── __init__.py
├── conftest.py             # Pytest configuration and shared fixtures
└── README.md               # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)

#### `test_patterns.py` (100+ tests)
Core pattern detection tests focusing on **legal compliance**:

- **Email Detection** (6 tests)
  - Standard format validation
  - Subdomains and special characters
  - High confidence scoring
  - False positive prevention

- **Phone Number Detection** (17 tests)
  - US/Canada formats
  - European formats (UK, France, Germany, etc.)
  - Asian formats (China, Japan, Korea, India)
  - Middle East & Africa
  - Version number false positives
  - High confidence requirements

- **National ID Detection** (15 tests)
  - US Social Security Numbers
  - UK National Insurance Numbers
  - European IDs (Spain DNI/NIE, France INSEE, Germany Steuer-ID)
  - Asian IDs (China, Japan, Korea, Singapore)
  - Validation checksums (mod-97, Luhn)
  - False positive prevention (dates vs IDs)

- **Credit Card Detection** (5 tests)
  - Visa, Mastercard, Amex
  - Luhn checksum validation
  - False positive prevention

- **Bank Account Detection** (3 tests)
  - IBAN validation (mod-97)
  - International formats

- **IP Address Detection** (2 tests)
  - IPv4 and IPv6
  - False positive prevention

- **Confidence Scoring** (3 tests)
  - High confidence for clear patterns
  - Validation confidence boost

#### `test_layer1.py` (60+ tests)
Layer 1 (Fast Legal Scrub) analysis tests:

- **Basic Detection** (4 tests)
  - Email, phone, SSN, credit card
  - Pattern + spaCy integration

- **Redaction Actions** (3 tests)
  - Text redaction with █ characters
  - Preservation of non-PII
  - Consistent output

- **Pseudonymization** (2 tests)
  - Person name replacement
  - Organization replacement

- **Masking** (1 test)
  - Uncertainty-based masking

- **Presets** (3 tests)
  - Aggressive (low threshold, many matches)
  - Conservative (high threshold, few matches)
  - Balanced (middle ground)

- **Overlap Resolution** (2 tests)
  - No double-redaction
  - Confidence-based winner selection

- **Summary Statistics** (2 tests)
  - Accurate entity counts
  - Proper zero counts

- **Findings Quality** (4 tests)
  - Context snippets included
  - Confidence scores present
  - Position accuracy
  - Detection sources noted

- **Entity Control** (2 tests)
  - Can disable email detection
  - Can disable phone detection

- **Confidence Thresholds** (2 tests)
  - High threshold filters matches
  - Low threshold allows more

- **Large Documents** (1 test)
  - Handles 100+ line documents
  - Performance acceptable

- **Language Support** (2 tests)
  - English detection
  - Multilingual text

- **Uncertainty Policies** (3 tests)
  - Mask policy
  - Redact policy
  - Leave intact policy

### Integration Tests (`tests/integration/`)

#### `test_end_to_end.py` (40+ tests)
Complete workflow tests with real-world documents:

- **Legal Documents** (3 tests)
  - Full agreement anonymization
  - Contract with dates and financials
  - Settlement agreement with multiple contacts

- **False Positive Prevention** (3 tests)
  - Version numbers → NOT phones
  - Dates → NOT SSNs
  - Math expressions → NOT phones

- **Complete Redaction** (2 tests)
  - No PII remains in output
  - Document readability preserved

- **Findings Accuracy** (2 tests)
  - Position accuracy verification
  - All required fields present

- **Preset Consistency** (2 tests)
  - Aggressive finds more than conservative
  - Selective entity disabling

- **Document Types** (3 tests)
  - Contract documents
  - Invoice documents
  - Medical records

- **Edge Cases** (4 tests)
  - Empty documents
  - Documents without PII
  - Very large documents
  - Special characters and Unicode

- **Consistency** (2 tests)
  - Same text → same redaction
  - Idempotent redaction

### Benchmark Tests (`tests/benchmarks/`)

#### `test_performance.py` (30+ tests)
Performance and scalability tests:

- **Pattern Detection Speed** (4 tests)
  - Email detection throughput
  - Phone detection throughput
  - SSN detection throughput
  - Mixed PII detection

- **Validation Overhead** (2 tests)
  - Credit card validation overhead (<50%)
  - IBAN validation overhead

- **Layer 1 Performance** (3 tests)
  - Small document (1KB)
  - Medium document (10KB)
  - Large document (100KB+)

- **Scalability** (1 test)
  - Linear scaling verification
  - Processing time vs document size

- **Pattern Complexity** (3 tests)
  - Single pattern match
  - Many patterns in text
  - Overlapping patterns

- **False Positive Performance** (2 tests)
  - Version numbers (1000x)
  - Dates (1000x)

- **Memory Usage** (1 test)
  - Large document memory efficiency

- **Concurrent Processing** (2 tests)
  - Sequential documents
  - Repeated analysis

- **Regression Detection** (2 tests)
  - Baseline performance verification

## Running Tests

### All Tests
```bash
pytest tests/
```

### Specific Test File
```bash
pytest tests/unit/test_patterns.py
pytest tests/unit/test_layer1.py
pytest tests/integration/test_end_to_end.py
pytest tests/benchmarks/test_performance.py
```

### Specific Test Class
```bash
pytest tests/unit/test_patterns.py::TestEmailDetection
pytest tests/unit/test_layer1.py::TestLayer1BasicDetection
```

### Specific Test
```bash
pytest tests/unit/test_patterns.py::TestEmailDetection::test_detects_standard_email
pytest tests/unit/test_layer1.py::TestLayer1BasicDetection::test_detects_email -v
```

### By Marker
```bash
# Compliance-critical tests only
pytest -m compliance

# PII detection tests
pytest -m pii_detection

# False positive prevention tests
pytest -m false_positive

# High-priority tests (legal compliance)
pytest -m high_priority

# Skip slow/benchmark tests
pytest -m "not slow"

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip tests requiring spaCy models
pytest -m "not requires_models"
```

### With Coverage
```bash
# Coverage report
pytest tests/ --cov=anonymizer_engine --cov-report=html

# Coverage with missing line details
pytest tests/ --cov=anonymizer_engine --cov-report=term-missing

# Coverage threshold enforcement (fails if < 80%)
pytest tests/ --cov=anonymizer_engine --cov-fail-under=80
```

### Verbose Output
```bash
pytest tests/ -v                    # Verbose
pytest tests/ -vv                   # Very verbose
pytest tests/ -vv -s                # With print statements
```

### Performance Tests Only
```bash
pytest tests/benchmarks/ -v
pytest tests/benchmarks/ --benchmark-only
```

## Test Markers

Markers are used to categorize and select tests:

| Marker | Meaning | Used For |
|--------|---------|----------|
| `unit` | Unit test | Individual components |
| `integration` | Integration test | Multi-component workflows |
| `benchmark` | Performance test | Speed/load testing |
| `compliance` | Legal/compliance requirement | Regulatory validation |
| `pii_detection` | PII detection accuracy | Pattern matching verification |
| `false_positive` | False positive prevention | Avoiding incorrect matches |
| `layer1` | Layer 1 tests | Pattern + spaCy |
| `high_priority` | Critical for legal compliance | Must-pass tests |
| `requires_models` | Requires NLP models | spaCy dependencies |
| `slow` | Time-consuming tests | Performance/load |
| `spacy` | Requires spaCy | NLP functionality |

## Test Data

### Real-World Documents (`fixtures/test_documents.py`)

The test suite includes realistic legal documents:

- **Service Agreement**: Consulting contract with multiple PII types
- **Settlement Agreement**: Legal settlement with contact details
- **Medical Record**: Healthcare record with patient info
- **Invoice**: Business invoice with payment details
- **Employment Contract**: Hiring agreement with salary
- **Multilingual**: Documents in English, Spanish, French, German, Dutch
- **False Positives**: Text designed to trigger false matches
- **High-Priority PII**: All critical PII types

### Fixtures in `conftest.py`

Common test data and helpers:

- **Sample Data**: Emails, phones, SSNs, credit cards, IBANs
- **Presets**: Aggressive, conservative, balanced
- **Phone Numbers**: Valid numbers by region
- **National IDs**: Valid formats by country
- **Builders**: PatternMatch and Finding factories
- **Assertions**: Helper functions for common checks

## Critical Test Categories

### For Legal Compliance

**Must-pass tests** (marked with `compliance` and `high_priority`):

1. **SSN/National ID Detection** (20+ tests)
   - No false negatives on valid SSNs
   - No false positives on dates
   - All international formats supported

2. **Email Detection** (6+ tests)
   - All common email formats
   - High confidence scoring
   - Unicode support

3. **Phone Detection** (17+ tests)
   - All major country formats
   - No version number confusion
   - High confidence for known patterns

4. **Credit Card Detection** (5+ tests)
   - Luhn validation
   - All major card types
   - PCI compliance

5. **Redaction Quality** (10+ tests)
   - No PII remains in output
   - Output is readable
   - Consistency across runs

## Coverage Goals

Target coverage by component:

```
anonymizer_engine/
  patterns.py                 >95%  (critical for PII detection)
  layer1.py                   >90%  (core anonymization logic)
  preset.py                   >85%  (configuration)
  findings.py                 >80%  (output formatting)
  shared.py                   >80%  (utilities)
```

Overall target: **>80% statement coverage** with:
- >75% branch coverage
- >80% function coverage

## Performance Targets

Benchmark targets for Layer 1:

| Document Size | Target Time | Notes |
|---------------|-------------|-------|
| 1 KB | <100 ms | Small documents (quick) |
| 10 KB | <500 ms | Medium documents |
| 100 KB | <5 sec | Large documents |
| 1 MB | <30 sec | Very large documents |

Pattern matching:

| Operation | Target | Notes |
|-----------|--------|-------|
| Single email detection | <1 ms | Very fast |
| 100 mixed patterns | <100 ms | Acceptable overhead |
| Validation (Luhn/mod-97) | <50% overhead | Minimal impact |

## Continuous Integration

Tests run automatically on:
- Every commit (via Git hooks)
- Pull request validation
- Pre-deployment checks

### CI Configuration

```bash
# Run all tests with coverage
pytest tests/ --cov=anonymizer_engine --cov-fail-under=80

# Run only compliance-critical tests
pytest tests/ -m "compliance or high_priority"

# Run unit + integration (skip benchmarks)
pytest tests/ -m "not benchmark"
```

## Development Workflow

### Before Committing

```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=anonymizer_engine --cov-report=term-missing

# Run benchmarks to check for regressions
pytest tests/benchmarks/ -v
```

### Debugging Failed Tests

```bash
# Run with verbose output
pytest tests/unit/test_patterns.py::TestEmailDetection::test_detects_standard_email -vv

# Run with print statements
pytest tests/unit/test_patterns.py -vv -s

# Run with pdb on failure
pytest tests/unit/test_patterns.py --pdb

# Run with detailed assertion rewriting
pytest tests/unit/test_patterns.py -vv --tb=long
```

## Extending Tests

### Adding a New Test Pattern

1. Create test class in `tests/unit/test_patterns.py`
2. Add marker: `@pytest.mark.unit` and `@pytest.mark.pii_detection`
3. Use descriptive name: `test_detects_<entity_type>_<format>`
4. Include docstring explaining what's being tested
5. Use fixtures from `conftest.py` for common data

Example:
```python
@pytest.mark.unit
@pytest.mark.pii_detection
def test_detects_france_phone(self):
    """Phone: French format 06 12 34 56 78."""
    text = "Téléphone: 06 12 34 56 78"
    matches = detect_patterns(text)
    phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
    assert len(phone_matches) >= 1
```

### Adding Integration Test

1. Create test class in `tests/integration/test_end_to_end.py`
2. Add marker: `@pytest.mark.integration`
3. Test complete workflow (detect → redact → verify)
4. Use realistic document from `fixtures/test_documents.py`

## Troubleshooting

### spaCy Models Not Found

```bash
python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm
python -m spacy download de_core_news_sm
```

### Tests Requiring Large Downloads

Some tests require spaCy models (100+ MB). Skip them with:
```bash
pytest tests/ -m "not requires_models"
```

### Slow Tests

Exclude benchmark tests:
```bash
pytest tests/ -m "not slow"
```

### Memory Issues

Run tests in smaller batches:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Contributing Tests

When adding new functionality:

1. Add unit tests in `tests/unit/`
2. Add integration tests in `tests/integration/`
3. Add performance tests in `tests/benchmarks/` if relevant
4. Update this README if adding new test categories
5. Ensure all compliance tests pass
6. Achieve >80% coverage

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Legal Anonymizer Architecture](../../docs/architecture.md)
- [PII Detection Strategy](../../docs/pii-detection.md)
