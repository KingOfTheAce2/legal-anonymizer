# Testing Guide - Legal Anonymizer

Quick reference for running tests.

## Quick Start

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=anonymizer_engine --cov-report=html

# Run only compliance tests
pytest tests/ -m "compliance or high_priority"
```

## Common Commands

### All Tests
```bash
pytest tests/                              # Basic
pytest tests/ -v                           # Verbose
pytest tests/ --cov=anonymizer_engine      # With coverage
```

### By Category
```bash
pytest tests/unit/                         # Unit tests only
pytest tests/integration/                  # Integration tests
pytest tests/benchmarks/                   # Performance tests
```

### By Marker
```bash
pytest -m compliance                       # Legal compliance only
pytest -m "compliance or high_priority"    # Critical tests
pytest -m "not slow"                       # Skip slow tests
pytest -m "not requires_models"            # Skip spaCy dependency tests
```

### Specific Test
```bash
pytest tests/unit/test_patterns.py::TestEmailDetection
pytest tests/unit/test_patterns.py::TestEmailDetection::test_detects_standard_email -vv
```

### Coverage Reports
```bash
pytest tests/ --cov=anonymizer_engine --cov-report=html
open htmlcov/index.html

pytest tests/ --cov=anonymizer_engine --cov-report=term-missing
```

## Test Structure

**170+ tests** organized as:

| Category | Count | File |
|----------|-------|------|
| Unit: Patterns | 100+ | `tests/unit/test_patterns.py` |
| Unit: Layer 1 | 60+ | `tests/unit/test_layer1.py` |
| Integration | 40+ | `tests/integration/test_end_to_end.py` |
| Benchmarks | 30+ | `tests/benchmarks/test_performance.py` |

## Key Test Coverage

### Pattern Detection
- Emails (6 tests)
- Phones (17 tests, 40+ countries)
- National IDs (15+ tests, 20+ countries)
- Credit cards (5 tests)
- IBANs (3 tests)
- IP addresses (2 tests)

### Anonymization
- Text redaction
- Pseudonymization
- Masking
- Overlap resolution
- Confidence thresholds

### Compliance
- No false negatives on SSNs/IDs
- No false positives (versions, dates)
- Complete PII redaction
- Output readability

### Performance
- <100ms for small docs (1KB)
- <500ms for medium docs (10KB)
- <30s for large docs (100KB+)
- Linear scaling

## Configuration Files

- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage configuration
- `conftest.py` - Shared fixtures (50+)
- `fixtures/test_documents.py` - Real-world test data

## Documentation

- `tests/README.md` - Comprehensive documentation
- `tests/TEST_SUITE_SUMMARY.md` - Detailed summary
- This file - Quick reference

## Troubleshooting

### Missing spaCy models
```bash
python -m spacy download en_core_web_sm
# Or skip those tests
pytest -m "not requires_models"
```

### Too slow?
```bash
pytest -m "not slow"          # Skip benchmarks
pytest tests/unit/            # Unit tests only
```

### Coverage below 80%?
Check which lines need coverage:
```bash
pytest --cov=anonymizer_engine --cov-report=term-missing
```

## CI/CD Integration

```bash
# Run in CI pipeline
pytest tests/ \
    --cov=anonymizer_engine \
    --cov-fail-under=80 \
    --cov-report=html \
    -v
```

## Next Steps

1. Run tests: `pytest tests/ -v`
2. Check coverage: `pytest tests/ --cov=anonymizer_engine --cov-report=html`
3. Read details: `tests/README.md`
4. Check results: `htmlcov/index.html`

For more details, see:
- `tests/README.md` - Full documentation
- `tests/TEST_SUITE_SUMMARY.md` - Detailed overview
