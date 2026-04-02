# Sidecar Binaries

This directory contains the bundled Python anonymizer engine.

## For Development

During development, the app uses the Python engine directly (if installed) or browser mock mode.

## For Distribution

The GitHub Actions workflow automatically builds the sidecar binary with bundled:
- Python runtime + all dependencies
- spaCy (en_core_web_sm + en_core_web_lg bundled; other languages downloadable in-app)
- HuggingFace Transformers + CPU PyTorch (Layer 2 / Accurate mode)
- Microsoft Presidio (Layer 3 / Thorough mode)

## Manual Build

**Python 3.11 required** (spaCy 3.8 is incompatible with Python 3.14+).

```bash
cd engine/python
py -3.11 -m pip install -e ".[layer1,layer2,layer3,pdf,docx,pptx]"
py -3.11 -m pip install pyinstaller
py -3.11 -m spacy download en_core_web_sm
py -3.11 -m spacy download en_core_web_lg
py -3.11 -m PyInstaller anonymizer_engine.spec --noconfirm
```

Then copy the executable from `engine/python/dist/` to this directory.

### Platform-specific naming

Tauri expects specific names:
- Windows: `anonymizer_engine-x86_64-pc-windows-msvc.exe`
- macOS Intel: `anonymizer_engine-x86_64-apple-darwin`
- macOS ARM: `anonymizer_engine-aarch64-apple-darwin`
- Linux: `anonymizer_engine-x86_64-unknown-linux-gnu`
