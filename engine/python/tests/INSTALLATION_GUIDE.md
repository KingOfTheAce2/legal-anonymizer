# Test Suite Installation & Execution Guide

## System Requirements

- Python 3.10 or higher
- pip package manager
- Git (for version control)

## Installation Steps

### 1. Navigate to Project Directory

```bash
cd /g/GitHub/legal-anonymizer/engine/python
```

### 2. Install Test Dependencies

**Option A: Install with test dependencies only**
```bash
pip install -e ".[dev]"
```

**Option B: Install with all dependencies**
```bash
pip install -e ".[all,dev]"
```

**Option C: Manual installation**
```bash
pip install pytest>=7.4.0
pip install pytest-cov>=4.1.0
pip install python-dateutil>=2.9.0
pip install langdetect>=1.0.9
```

### 3. Install Optional spaCy Models (Recommended)

These enable NLP-based entity detection tests:

```bash
# English (most important)
python -m spacy download en_core_web_sm

# Additional languages (optional)
python -m spacy download nl_core_news_sm  # Dutch
python -m spacy download de_core_news_sm  # German
python -m spacy download es_core_news_sm  # Spanish
python -m spacy download fr_core_news_sm  # French
```

If spaCy models are not installed, tests will still run but will skip model-dependent tests.

## Verify Installation

### Check Python Version
```bash
python --version
# Should output Python 3.10.x or higher
```

### Check pytest Installation
```bash
pytest --version
# Should output pytest 7.x or higher
```

### Verify Test Discovery
```bash
pytest tests/ --collect-only
# Should list 170+ tests
```

## Running Tests

### Quick Start - Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=anonymizer_engine --cov-report=html
open htmlcov/index.html  # View in browser (macOS/Linux)
# or for Windows
start htmlcov/index.html
```

### Run Only Compliance Tests (Quick)
```bash
pytest tests/ -m "compliance or high_priority" -v
```

### Run by Category

**Unit Tests Only**
```bash
pytest tests/unit/ -v
```

**Integration Tests Only**
```bash
pytest tests/integration/ -v
```

**Performance Tests Only**
```bash
pytest tests/benchmarks/ -v
```

### Skip Slow/Benchmark Tests
```bash
pytest tests/ -m "not slow" -v
```

### Skip Tests Requiring spaCy Models
```bash
pytest tests/ -m "not requires_models" -v
```

### Run Specific Test Class
```bash
pytest tests/unit/test_patterns.py::TestEmailDetection -v
```

### Run Specific Test
```bash
pytest tests/unit/test_patterns.py::TestEmailDetection::test_detects_standard_email -vv
```

## Understanding Test Output

### Successful Test Run Example
```
tests/unit/test_patterns.py::TestEmailDetection::test_detects_standard_email PASSED [50%]
tests/unit/test_patterns.py::TestEmailDetection::test_detects_email_with_dots PASSED [100%]

========== 170 passed in 45.23s ==========
```

### With Coverage Example
```
========== Coverage Report ==========
Name                                 Stmts   Miss  Cover
------------------------------------------------------
anonymizer_engine/patterns.py         500     25    95%
anonymizer_engine/layer1.py           300     30    90%
anonymizer_engine/preset.py            50      8    85%
anonymizer_engine/findings.py          40      8    80%
anonymizer_engine/shared.py            80     16    80%
------------------------------------------------------
TOTAL                                 970    87    90%

========== 170 passed in 45.23s ==========
```

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'pytest'"

**Solution:** Install pytest
```bash
pip install pytest
```

### Problem: "No spaCy language models found"

**Solution:** Install spaCy models
```bash
python -m spacy download en_core_web_sm
```

**Or:** Skip model-dependent tests
```bash
pytest tests/ -m "not requires_models"
```

### Problem: Tests too slow

**Solution:** Skip benchmark tests
```bash
pytest tests/ -m "not slow"
```

Or run specific category:
```bash
pytest tests/unit/ -v
```

### Problem: ImportError for anonymizer_engine

**Solution:** Make sure you installed the package
```bash
pip install -e .
```

Or add to PYTHONPATH:
```bash
export PYTHONPATH="/g/GitHub/legal-anonymizer/engine/python:$PYTHONPATH"
```

### Problem: "coverage: Can't find a source for 'anonymizer_engine'"

**Solution:** Ensure package is installed in development mode
```bash
pip install -e .
```

### Problem: Coverage below 80%

**Solution:** Check which lines need coverage
```bash
pytest tests/ --cov=anonymizer_engine --cov-report=term-missing
```

This shows which lines don't have test coverage. Add tests for those lines.

## Test Structure

The test suite is organized as:

```
tests/
├── unit/                    # Fast unit tests (~5 min)
│   ├── test_patterns.py    # Pattern detection (100+ tests)
│   └── test_layer1.py      # Layer 1 anonymization (60+ tests)
├── integration/             # Complete workflows (~10 min)
│   └── test_end_to_end.py  # Real document tests (40+ tests)
└── benchmarks/              # Performance tests (~30 min)
    └── test_performance.py  # Speed & memory (30+ tests)
```

Total time: ~45 minutes for full suite

## Development Workflow

### Before Committing Code

```bash
# 1. Run all unit tests (fast)
pytest tests/unit/ -v

# 2. Check coverage
pytest tests/ --cov=anonymizer_engine --cov-report=term-missing

# 3. Run full suite before push
pytest tests/ -v
```

### Adding New Tests

1. Create test in appropriate directory
2. Use descriptive name: `test_<what_you_test>`
3. Add docstring explaining the test
4. Add appropriate markers: `@pytest.mark.unit` etc.
5. Run: `pytest tests/<new_test_file> -v`

## CI/CD Integration

For continuous integration pipelines:

```bash
# Install dependencies
pip install -e ".[all,dev]"

# Run tests with coverage enforcement
pytest tests/ \
    --cov=anonymizer_engine \
    --cov-fail-under=80 \
    --cov-report=html \
    --cov-report=json \
    -v

# Results saved to:
# - htmlcov/index.html (HTML report)
# - coverage.json (machine-readable)
```

## Test Configuration

### Configuration Files

- **`pytest.ini`** - Pytest settings (test discovery, markers, coverage)
- **`.coveragerc`** - Coverage settings (branches, exclusions)
- **`conftest.py`** - Shared fixtures (50+ fixtures available)

### Customizing Test Markers

To run specific marker combinations:

```bash
# Compliance tests
pytest -m compliance

# Compliance OR high priority
pytest -m "compliance or high_priority"

# NOT slow tests
pytest -m "not slow"

# PII detection but not slow
pytest -m "pii_detection and not slow"
```

## Performance Expectations

Time to run tests:

| Category | Count | Time |
|----------|-------|------|
| Unit tests | 160+ | ~10 min |
| Integration | 40+ | ~20 min |
| Benchmarks | 30+ | ~15 min |
| **Total** | **170+** | **~45 min** |

Can be reduced by skipping benchmarks:
```bash
pytest tests/ -m "not slow"  # ~25 min
```

## Getting Help

### View Available Markers
```bash
pytest --markers
```

### View Available Fixtures
```bash
pytest --fixtures tests/
```

### Run with Detailed Output
```bash
pytest tests/ -vv -s
```

### Show slowest tests
```bash
pytest tests/ --durations=10
```

### Run with Python debugger
```bash
pytest tests/unit/test_patterns.py --pdb
```

## Next Steps

1. **Install:** Run installation steps above
2. **Run tests:** `pytest tests/ -v`
3. **Check coverage:** `pytest tests/ --cov=anonymizer_engine --cov-report=html`
4. **Read docs:** See `tests/README.md` for detailed documentation
5. **Integrate:** Add to your CI/CD pipeline

## Support

For issues or questions:

1. Check `tests/README.md` - Comprehensive documentation
2. Check `tests/TEST_SUITE_SUMMARY.md` - Detailed overview
3. Check `conftest.py` - Fixture definitions
4. Check individual test files - Docstrings explain each test

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Legal Anonymizer README](../../README.md)

---

**Last Updated:** February 14, 2025
**Python Version:** 3.10+
**Pytest Version:** 7.4+
