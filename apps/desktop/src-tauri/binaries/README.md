# Sidecar Binaries

This directory contains the bundled Python anonymizer engine.

## For Development

During development, the app uses the Python engine directly (if installed) or browser mock mode.

## For Distribution

The GitHub Actions workflow automatically builds the sidecar binary with bundled:
- Python runtime
- spaCy library
- Language models (EN, NL, DE, FR, ES, IT)
- All PII detection patterns

## Manual Build

To build the sidecar manually:

```bash
cd engine/python
pip install -e .
pip install pyinstaller
python build_standalone.py --layer1
```

Then copy the executable from `engine/python/dist/` to this directory.

### Platform-specific naming

Tauri expects specific names:
- Windows: `anonymizer_engine-x86_64-pc-windows-msvc.exe`
- macOS Intel: `anonymizer_engine-x86_64-apple-darwin`
- macOS ARM: `anonymizer_engine-aarch64-apple-darwin`
- Linux: `anonymizer_engine-x86_64-unknown-linux-gnu`
