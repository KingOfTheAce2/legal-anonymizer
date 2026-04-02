# Legal Anonymizer

Offline-first legal anonymization tool for GDPR and AI Act compliant text and file scrubbing. Designed for lawyers and legal professionals with explainable, reproducible results.

## Features

- **Offline-First**: No automatic external API calls. All processing happens locally.
- **Three Detection Layers**: Choose the right balance of speed and accuracy.
- **GDPR Compliant**: Built for Article 5 (transparency, accountability) and Article 25 (privacy by design).
- **AI Act Ready**: Full audit trail and model governance.
- **Multi-Format Support**: DOCX, PDF, PPTX, and TXT files.
- **Desktop Application**: User-friendly Tauri-based interface.
- **Audit Logging**: Every run is recorded in a tamper-evident JSON-Lines audit log.

---

## Detection Layers

### Layer 3 — Thorough (Industry Standard) ✅ Recommended

**Technology: Microsoft Presidio** — the enterprise-grade PII detection framework used across regulated industries (banking, healthcare, legal). Presidio is maintained by Microsoft and is the de-facto standard for production-grade anonymization.

- Bundled directly in the installer — no internet connection required
- Multi-model pipeline: regex patterns + spaCy NER + custom recognizers
- Highest recall including legal document formats (ALL-CAPS names, court captions)
- Strictest defaults: high-priority entities are redacted, not pseudonymised
- Recommended for regulatory disclosure, court submissions, GDPR Article 17 requests

### Layer 1 — Fast

**Technology: spaCy NER + regex patterns**

Faster than Layer 3 but with lower recall. Suitable for first-pass review or large batch jobs where speed matters. Not the industry standard — use knowingly.

- English bundled in the installer; other languages downloadable from Setup
- Pattern-based detection for structured PII (emails, IBANs, phone numbers)
- Pseudonymises persons and organisations (consistent per run)
- Good for: internal review drafts, high-volume preprocessing

### Layer 2 — Accurate

**Technology: Transformer-based NER (BERT)**

Requires downloading a HuggingFace model (~420 MB). Contextual understanding improves recall over Layer 1 for ambiguous cases, but does not reach the regulatory completeness of Presidio (Layer 3).

- Model downloaded on first use to `AppData\Roaming\LegalAnonymizer\`
- Better for complex sentences where names appear without clear context
- Still not the recommended layer for regulatory submissions

### Choosing a Layer

| Layer | Technology | Accuracy | Speed | Use When |
|-------|-----------|----------|-------|----------|
| **Thorough (3)** | **Microsoft Presidio** | **Maximum** | Moderate | **Regulatory, compliance, court filings** |
| Accurate (2) | BERT transformer | High | Slow | Substantive legal review |
| Fast (1) | spaCy + regex | Good | Very fast | First pass, large batches |

> **Important:** Layers 1 and 2 are not the industry standard. Reducing accuracy from Presidio should be a conscious, documented decision — not the default.

---

## Quick Start

### Install (Windows)

Download `Legal Anonymizer_0.1.0_x64-setup.exe` and run it. No admin rights required. The installer includes:

- Microsoft Presidio (Layer 3) — bundled, no download needed
- English spaCy models (`en_core_web_sm` + `en_core_web_lg`) — bundled
- All other languages — downloadable from the Setup tab

### Build from Source

```bash
git clone https://github.com/your-org/legal-anonymizer.git
cd legal-anonymizer

# Python engine
cd engine/python
pip install -e ".[all]"

# Desktop app
cd apps/desktop
npm install
npm run tauri dev
```

### Command Line

```bash
echo '{"text":"John Smith, john@example.com","preset":{"name":"default","layer":3,"minimum_confidence":60,"uncertainty_policy":"mask","entities_enabled":{},"whitelist":[],"blacklist":[],"language_whitelists":{},"language_blacklists":{}}}' \
  | python scripts/sidecar_entrypoint.py analyze_text
```

---

## Redaction Output

Redacted entities are replaced with typed labels — no block characters that reveal text length:

| Method | Example input | Example output |
|--------|--------------|----------------|
| **Redact** | `John Smith` | `[PERSON]` |
| **Pseudonymise** | `John Smith` | `PERSON_001` (consistent per run) |
| **Mask** | `john@example.com` | `jo**@******.com` |

---

## Entity Taxonomy

| Priority | Entities | Default Action (Layer 3) |
|----------|----------|--------------------------|
| 100 | NATIONAL_ID, PASSPORT_NUMBER, MEDICAL_ID | Always Redact → `[NATIONAL_ID]` |
| 90 | BANK_ACCOUNT, CREDIT_CARD | Always Redact |
| 80 | PERSON, DATE_OF_BIRTH, EMAIL, PHONE_NUMBER | Redact (L3) / Pseudonymise (L1) |
| 70 | ADDRESS, IP_ADDRESS | Redact |
| 60 | ORGANIZATION, LOCATION, ACCOUNT_USERNAME | Pseudonymise |
| 40 | DATE | Optional |

---

## Audit Logging

Every run is recorded in a JSON-Lines audit log at:

```
Windows:  %APPDATA%\LegalAnonymizer\logs\audit-YYYY-MM-DD.jsonl
macOS:    ~/Library/Logs/LegalAnonymizer/logs/audit-YYYY-MM-DD.jsonl
Linux:    ~/.local/state/LegalAnonymizer/logs/audit-YYYY-MM-DD.jsonl
```

Each log entry is a self-contained JSON object:

```jsonc
// analyze_text event
{
  "ts": "2026-03-01T18:15:32Z",
  "event": "analyze_text",
  "run_id": "RUN_20260301T181532Z",
  "layer": 3,
  "preset_name": "GDPR Strict",
  "language": "en",
  "input_chars": 4821,
  "input_sha256": "a3f1...",   // hash of input — never the text itself
  "findings_count": 12,
  "summary": {"PERSON": 4, "EMAIL": 2, "NATIONAL_ID": 1, "ORGANIZATION": 5},
  "elapsed_ms": 843,
  "uncertainty_policy": "redact",
  "minimum_confidence": 60
}

// model_download event
{
  "ts": "2026-03-01T17:00:00Z",
  "event": "model_download",
  "model_type": "spacy",
  "model_id": "fr_core_news_sm",
  "status": "installed"
}

// model_uninstall event
{
  "ts": "2026-03-01T17:05:00Z",
  "event": "model_uninstall",
  "model_type": "huggingface",
  "model_id": "dslim/bert-base-NER"
}
```

**What is logged:** timestamp, run ID, layer used, preset name, language, character count, SHA-256 of input, entity counts, processing time, confidence settings, model changes.

**What is never logged:** the input text, the redacted text, file names, file paths, or any personal data.

Log files rotate daily. They are append-only and written locally — nothing is transmitted externally.

---

## Output Artifacts

Each anonymization run produces a folder under `runs/` (or `AppData\Local\runs\` in the installed build):

```
RUN_20260301T181532Z/
├── preset_used.json        # Exact configuration used
├── model_inventory.json    # Models and versions active during this run
├── run_report.json         # Summary statistics
├── findings.csv            # Detailed findings (entity, position, confidence, action)
└── output/
    └── document_redacted.docx
```

`findings.csv` contains the detected original values and is itself sensitive — restrict access and do not share externally.

---

## GDPR Compliance

### Article 5 — Principles
- **Transparency**: Every detection and action logged in `findings.csv` and audit log
- **Purpose Limitation**: No telemetry, no secondary use of data
- **Data Minimisation**: Entity priorities limit unnecessary processing
- **Accountability**: Immutable per-run artifacts + daily audit log

### Article 25 — Privacy by Design
- Strictest layer (Presidio) is the default recommendation
- Escalation-only model: users can increase protection, the system never silently weakens it
- Conservative uncertainty handling

### Article 32 — Security of Processing
- Local processing only — no external API calls
- Original input files are never overwritten
- File paths are excluded from audit logs

---

## Security

- No network connections by default
- Original files never modified
- File paths not written to findings or audit logs (only SHA-256 hashes)
- Model hashes recorded; no remote code execution
- Findings reports contain detected values — treat them as sensitive

---

## Architecture

```
Legal Anonymizer
├── UI Layer (React/TypeScript)        — input collection, results display
├── Tauri bridge (Rust)                — file-based IPC, no stdin/stdout pipe issues
└── Python engine (PyInstaller binary)
    ├── Layer 1: spaCy + patterns
    ├── Layer 2: BERT transformer
    ├── Layer 3: Microsoft Presidio    ← industry standard, bundled
    ├── File scrapers: DOCX, PDF, PPTX, TXT
    └── Audit logger                   → logs/audit-YYYY-MM-DD.jsonl
```

---

## Project Structure

```
legal-anonymizer/
├── apps/desktop/           # Tauri desktop application
│   ├── src/               # React/TypeScript frontend
│   └── src-tauri/         # Rust backend + IPC
└── engine/python/          # Python anonymization engine
    ├── anonymizer_engine/ # Core modules
    │   ├── layer1.py
    │   ├── layer2_candle.py
    │   ├── layer3_presidio.py
    │   ├── docx_scrubber.py
    │   ├── pdf_scrubber.py
    │   └── pptx_scrubber.py
    └── scripts/
        └── sidecar_entrypoint.py   # Tauri ↔ Python bridge + audit logger
```

---

## Development

```bash
cd engine/python
pip install -e ".[dev]"
py -3.11 -m pytest tests/ --ignore=tests/benchmarks -x
```

---

## License

[Elastic License 2.0 (ELv2)](LICENSE)

Source-available. You may use, copy, modify, and distribute for any purpose **except** offering it as a managed service to third parties.
