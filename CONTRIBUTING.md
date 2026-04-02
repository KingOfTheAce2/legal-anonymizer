# Contributing to Legal Anonymizer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/legal-anonymizer.git
cd legal-anonymizer

# Install dependencies
make install

# Run tests
make test

# Run linters
make lint
```

## 📋 Development Workflow

### 1. **Set Up Development Environment**

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
cd engine/python
pip install -e ".[all,dev]"

# Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm
python -m spacy download de_core_news_sm

# Install pre-commit hooks
pre-commit install
```

### 2. **Create a Feature Branch**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 3. **Make Changes**

Follow these guidelines:

#### Code Style
- Use `ruff format` for formatting
- Follow PEP 8 guidelines
- Add type hints (mypy compliant)
- Keep line length ≤ 100 characters

#### Testing
- Add tests for new features
- Maintain >85% code coverage
- Use pytest markers:
  - `@pytest.mark.slow` for slow tests
  - `@pytest.mark.benchmark` for benchmarks
  - `@pytest.mark.integration` for integration tests

#### Documentation
- Add docstrings (Google style)
- Update README if needed
- Add inline comments for complex logic

### 4. **Run Quality Checks**

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Run benchmarks
make benchmark

# Or run everything
make all
```

### 5. **Commit Changes**

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add entity validation layer"
# or
git commit -m "fix: correct SSN false positive detection"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `perf:` Performance improvement
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance

### 6. **Push and Create PR**

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 🧪 Testing Guidelines

### Unit Tests

```python
# tests/unit/test_validators.py
import pytest
from anonymizer_engine.validators import EntityValidator

def test_ssn_validation_fake_numbers():
    """Test SSN validator rejects fake numbers."""
    is_valid, confidence = EntityValidator.validate_ssn("000-00-0000")
    assert not is_valid
    assert confidence == 0

def test_ssn_validation_real_format():
    """Test SSN validator accepts valid format."""
    is_valid, confidence = EntityValidator.validate_ssn("123-45-6789")
    assert is_valid
    assert confidence == 95
```

### Integration Tests

```python
# tests/integration/test_end_to_end.py
def test_full_anonymization_pipeline():
    """Test complete anonymization workflow."""
    text = "John Smith lives at 123 Main St. SSN: 123-45-6789"
    preset = Preset(layer=1, minimum_confidence=60)

    output, findings, summary = analyze_layer1_text(text, preset, "en")

    assert "PERSON_001" in output
    assert "███████" in output  # Redacted SSN
    assert len(findings) >= 2  # PERSON + NATIONAL_ID
```

### Benchmark Tests

```python
# tests/benchmarks/test_performance.py
def test_layer1_performance_50_pages(benchmark):
    """Benchmark Layer 1 on 50-page document."""
    text = load_test_document("50_pages.txt")
    preset = Preset(layer=1)

    result = benchmark(analyze_layer1_text, text, preset, "en")

    assert benchmark.stats["mean"] < 2.0  # <2 seconds
```

## 🔒 Security Guidelines

### Before Committing
- **Never** commit secrets (API keys, passwords, private keys)
- Run `git diff` to review changes
- Check for sensitive information in test files
- Pre-commit hooks will catch some issues, but review manually

### Pattern Contributions
When adding new PII detection patterns:

1. **Test thoroughly** - Ensure high precision (>95%)
2. **Document** - Explain what the pattern detects
3. **Priority** - Assign correct priority (40-100)
4. **Compliance** - Consider GDPR/AI Act implications

Example:
```python
# Good pattern contribution
PATTERNS = [
    # EU VAT Number: 2 letters + 8-12 digits
    (r"\b[A-Z]{2}\d{8,12}\b", "VAT_NUMBER", 80, "vat_eu"),
]

# Include tests
def test_vat_number_detection():
    assert detects("DE123456789")
    assert not detects("AB123")  # Too short
```

## 📚 Documentation Standards

### Docstrings (Google Style)

```python
def validate_email(value: str) -> Tuple[bool, int]:
    """
    Validate email address and detect test/disposable domains.

    Args:
        value: Email address to validate

    Returns:
        Tuple of (is_valid, adjusted_confidence)
            - is_valid: True if email format is valid
            - adjusted_confidence: 0-100, lower for test emails

    Examples:
        >>> validate_email("user@example.com")
        (False, 20)  # Test domain

        >>> validate_email("user@company.com")
        (True, 95)  # Valid
    """
    ...
```

### README Updates

When adding features:
1. Update main README.md
2. Add to CHANGELOG.md
3. Update docs/ if architectural
4. Add examples/notebooks if applicable

## 🎯 Priority Areas for Contribution

### High Priority
- [ ] Additional test coverage (current: needs baseline)
- [ ] Performance optimizations (target: <2s for 50-page docs)
- [ ] Additional language support (French, Spanish, Italian)
- [ ] OCR support with confidence scoring

### Medium Priority
- [ ] Additional PII patterns (healthcare, finance)
- [ ] UI/UX improvements for desktop app
- [ ] Batch processing optimization
- [ ] Advanced legal entity preservation

### Low Priority
- [ ] Additional export formats
- [ ] Visualization improvements
- [ ] Example notebooks
- [ ] Integration guides

## 🐛 Reporting Bugs

### Before Reporting
1. Check existing issues
2. Verify it's reproducible
3. Test on latest version

### Bug Report Template
```markdown
**Description:**
Brief description of the bug

**Steps to Reproduce:**
1. Step one
2. Step two
3. ...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.5]
- Version: [e.g., 0.1.0]

**Sample Data:**
(If applicable, provide anonymized sample)
```

## 💬 Getting Help

- **Questions:** Open a GitHub Discussion
- **Bugs:** Open an Issue
- **Security:** Email security@example.com (do not open public issue)

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Legal Anonymizer!** 🎉
