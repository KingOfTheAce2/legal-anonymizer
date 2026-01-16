# Legal Anonymizer

Offline-first legal anonymization tool for GDPR and AI Act compliant text and file scrubbing. Designed for lawyers and legal professionals with explainable, reproducible results.

## Features

- **Offline-First**: No automatic external API calls. All processing happens locally.
- **Three Detection Layers**: Choose the right balance of speed and accuracy.
- **GDPR Compliant**: Built for Article 5 (transparency, accountability) and Article 25 (privacy by design).
- **AI Act Ready**: Full audit trail and model governance.
- **Multi-Format Support**: DOCX, PDF, and TXT files.
- **Desktop Application**: User-friendly Tauri-based interface.
- **Batch Processing**: Handle thousands of files efficiently.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for desktop app)
- Rust (for desktop app)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/legal-anonymizer.git
cd legal-anonymizer

# Install Python dependencies
cd engine/python
pip install -e ".[all]"

# Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm  # Optional: Dutch
python -m spacy download de_core_news_sm  # Optional: German
```

### Running the Desktop App

```bash
cd apps/desktop

# Install Node dependencies
npm install

# Run in development mode
npm run tauri dev
```

### Command Line Usage

```bash
# Analyze text (Layer 1)
echo '{"text": "John Smith at john@example.com", "preset": {"preset_id": "layer1", "name": "Fast", "layer": 1, "minimum_confidence": 60, "uncertainty_policy": "mask", "pseudonym_style": "neutral", "language_mode": "auto", "entities_enabled": {}}}' | python scripts/sidecar_entrypoint.py analyze_text

# Analyze a file
echo '{"input_path": "/path/to/document.docx", "preset": {...}}' | python scripts/sidecar_entrypoint.py analyze_file
```

## Detection Layers

### Layer 1: Fast Legal Scrub
- **Technology**: Regex patterns + spaCy NER
- **Speed**: Fast and predictable
- **Use Case**: First-pass review, large batches
- **Languages**: English, Dutch, German

### Layer 2: Accurate Legal Review
- **Technology**: Regex patterns + Transformer-based NER (BERT)
- **Speed**: Higher accuracy, moderate speed
- **Use Case**: Substantive legal work requiring contextual understanding
- **Model**: `dslim/bert-base-NER` (downloaded on first use)

### Layer 3: Regulatory and Market Standard
- **Technology**: Regex patterns + Microsoft Presidio
- **Speed**: Conservative, enterprise-grade
- **Use Case**: Regulatory disclosure, compliance contexts
- **Strictness**: Higher - more entities redacted by default

## Entity Taxonomy

| Priority | Entities | Default Action |
|----------|----------|----------------|
| 100 | NATIONAL_ID, PASSPORT_NUMBER, MEDICAL_ID | Always Redact |
| 90 | BANK_ACCOUNT, CREDIT_CARD | Always Redact |
| 80 | PERSON, DATE_OF_BIRTH, EMAIL, PHONE_NUMBER | Pseudonymise |
| 70 | ADDRESS, IP_ADDRESS | Redact |
| 60 | ORGANIZATION, LOCATION, ACCOUNT_USERNAME | Configurable |
| 40 | DATE | Optional |

## Redaction Methods

- **Redact**: `John Smith` → `██████████` (irreversible)
- **Pseudonymise**: `John Smith` → `PERSON_001` (consistent per run)
- **Mask**: `john@example.com` → `jo**********om` (partial visibility)

## Output Artifacts

Each anonymization run produces a folder containing:

```
RUN_20250113T120000Z/
├── preset_used.json        # Exact configuration used
├── model_inventory.json    # Models and versions
├── run_report.json         # Summary statistics
├── findings.csv            # Detailed findings (21 columns)
├── input_manifest.json     # Input file hashes
├── output/                 # Redacted files
│   └── document_redacted.docx
└── logs/                   # Reserved for future use
```

## GDPR Compliance

### Article 5 Principles
- **Transparency**: Every detection and action is logged in findings.csv
- **Data Minimisation**: Entity priorities ensure only necessary data is processed
- **Accuracy**: Multiple detection methods with confidence scoring
- **Accountability**: Immutable run artifacts for audit trails

### Article 25: Privacy by Design
- **Safe Defaults**: High-priority entities always redacted
- **Escalation Only**: Users can only increase protection, not weaken it
- **OCR Disabled**: Optional and explicitly enabled

## Project Structure

```
legal-anonymizer/
├── apps/desktop/           # Tauri desktop application
│   ├── src/               # React/TypeScript frontend
│   └── src-tauri/         # Rust backend
├── engine/python/          # Python anonymization engine
│   ├── anonymizer_engine/ # Core modules
│   │   ├── layer1.py      # spaCy-based detection
│   │   ├── layer2_candle.py # Transformer-based detection
│   │   ├── layer3_presidio.py # Presidio-based detection
│   │   ├── docx_scrubber.py
│   │   ├── pdf_scrubber.py
│   │   └── ...
│   └── scripts/           # Entry points
└── docs/                  # Additional documentation
```

## Configuration

### Presets

Presets define the anonymization behavior:

```json
{
  "preset_id": "layer1_fast_legal_scrub",
  "name": "Fast Legal Scrub",
  "layer": 1,
  "minimum_confidence": 60,
  "uncertainty_policy": "mask",
  "pseudonym_style": "neutral",
  "language_mode": "auto",
  "entities_enabled": {
    "PERSON": true,
    "EMAIL": true,
    "PHONE_NUMBER": true,
    "BANK_ACCOUNT": true
  }
}
```

### Uncertainty Policies

- `mask`: Partially hide uncertain detections
- `redact`: Fully redact uncertain detections
- `leave_intact`: Don't modify uncertain detections
- `flag_only`: Log but don't modify

## Development

### Running Tests

```bash
cd engine/python
pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
ruff check .
mypy anonymizer_engine
```

## Security Considerations

- **No Cloud Connectivity**: All processing is local
- **No Path Leakage**: File paths are never stored in findings
- **Model Verification**: SHA-256 hashes for all downloaded models
- **Audit Trail**: Complete reproducibility from run artifacts

## License

MIT License - See LICENSE file for details.

## Documentation

All detailed documentation is in the [docs/](docs/) folder:

- [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md) - System architecture and components
- [Anonymization Design](docs/ANONYMIZATION_DESIGN.md) - Normative design specification
- [GDPR Compliance](docs/GDPR_COMPLIANCE.md) - GDPR article mapping
- [AI Model Governance](docs/AI_MODEL_GOVERNANCE.md) - Model management and verification
- [Preset Schema](docs/PRESET_SCHEMA.md) - Complete preset specification
- [Findings Report](docs/FINDINGS_REPORT.md) - Findings CSV format
- [Run Artifacts](docs/RUN_ARTIFACTS.md) - Output folder structure
- [User Guide](docs/USER_GUIDE.md) - End-user documentation
- [Security Considerations](docs/SECURITY_CONSIDERATIONS.md) - Security guidelines
- [Threat Model](docs/THREAT_MODEL.md) - Security threat analysis
- [Limitations](docs/LIMITATIONS_AND_NON_GOALS.md) - Known limitations
- [Changelog](docs/CHANGELOG.md) - Version history
