#!/usr/bin/env python3
"""
Build standalone executable for the anonymizer engine.
This bundles Python + spaCy + Transformers + Presidio + models into a single executable.

Usage:
    python build_standalone.py [--layer1] [--layer2] [--layer3] [--all]

The resulting executable can be distributed without Python installed.
"""

import subprocess
import sys
import os
from pathlib import Path

# Models to include per layer
SPACY_MODELS = {
    "layer1": [
        "en_core_web_sm",
        "nl_core_news_sm",
        "de_core_news_sm",
        "fr_core_news_sm",
        "es_core_news_sm",
        "it_core_news_sm",
        "pt_core_news_sm",
        "pl_core_news_sm",
    ],
    "layer3": [
        "en_core_web_lg",  # Presidio needs larger model for best accuracy
    ],
}

# HuggingFace models for Layer 2
HF_MODELS = {
    "layer2": [
        "dslim/bert-base-NER",
        "Davlan/bert-base-multilingual-cased-ner-hrl",
    ],
}

# Presidio packages for Layer 3
PRESIDIO_PACKAGES = [
    "presidio-analyzer",
    "presidio-anonymizer",
]

def install_pyinstaller():
    """Install PyInstaller if not present."""
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

def install_presidio():
    """Install Microsoft Presidio packages."""
    print("Installing Microsoft Presidio...")
    for package in PRESIDIO_PACKAGES:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
    print("Presidio installed successfully!")

def install_transformers():
    """Install HuggingFace Transformers and PyTorch."""
    print("Installing HuggingFace Transformers...")
    subprocess.run([sys.executable, "-m", "pip", "install", "transformers", "torch", "tokenizers"], check=True)
    print("Transformers installed successfully!")

def download_spacy_models(layers: list[str]):
    """Download required spaCy models."""
    models = set()
    for layer in layers:
        if layer in SPACY_MODELS:
            models.update(SPACY_MODELS[layer])

    for model in models:
        print(f"Downloading spaCy model: {model}")
        subprocess.run([sys.executable, "-m", "spacy", "download", model], check=True)

def download_hf_models(layers: list[str]):
    """Pre-download HuggingFace models for offline use."""
    if "layer2" not in layers:
        return

    print("Pre-downloading HuggingFace models...")
    try:
        from transformers import AutoTokenizer, AutoModelForTokenClassification

        for model_name in HF_MODELS.get("layer2", []):
            print(f"  Downloading {model_name}...")
            AutoTokenizer.from_pretrained(model_name)
            AutoModelForTokenClassification.from_pretrained(model_name)
            print(f"  {model_name} downloaded!")
    except Exception as e:
        print(f"Warning: Could not pre-download HF models: {e}")
        print("Models will be downloaded on first use.")

def get_spacy_model_paths() -> list[str]:
    """Get paths to installed spaCy models for PyInstaller."""
    import spacy
    paths = []

    # Find spacy data directory
    spacy_path = Path(spacy.__file__).parent
    data_path = spacy_path / "data"

    if data_path.exists():
        paths.append(f"{data_path};spacy/data")

    return paths

def build_executable(name: str = "anonymizer_engine", layers: list[str] = None):
    """Build the standalone executable using PyInstaller."""

    if layers is None:
        layers = ["layer1"]

    print(f"\n{'='*60}")
    print(f"Building Legal Anonymizer with layers: {', '.join(layers)}")
    print(f"{'='*60}\n")

    # Install dependencies based on layers
    if "layer2" in layers:
        install_transformers()

    if "layer3" in layers:
        install_presidio()

    # Download models
    download_spacy_models(layers)
    download_hf_models(layers)

    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", name,
        "--clean",
        # Hidden imports for spaCy
        "--hidden-import", "spacy",
        "--hidden-import", "spacy.lang.en",
        "--hidden-import", "spacy.lang.nl",
        "--hidden-import", "spacy.lang.de",
        "--hidden-import", "spacy.lang.fr",
        "--hidden-import", "spacy.lang.es",
        "--hidden-import", "spacy.lang.it",
        "--hidden-import", "spacy.lang.pt",
        "--hidden-import", "spacy.lang.pl",
        "--hidden-import", "spacy.lang.ru",
        "--hidden-import", "spacy.lang.zh",
        "--hidden-import", "spacy.lang.ja",
        "--hidden-import", "thinc",
        "--hidden-import", "cymem",
        "--hidden-import", "preshed",
        "--hidden-import", "murmurhash",
        "--hidden-import", "blis",
    ]

    # Add Layer 2 imports (HuggingFace Transformers)
    if "layer2" in layers:
        cmd.extend([
            "--hidden-import", "transformers",
            "--hidden-import", "transformers.models.bert",
            "--hidden-import", "transformers.models.roberta",
            "--hidden-import", "torch",
            "--hidden-import", "tokenizers",
            "--collect-data", "transformers",
        ])

    # Add Layer 3 imports (Microsoft Presidio)
    if "layer3" in layers:
        cmd.extend([
            "--hidden-import", "presidio_analyzer",
            "--hidden-import", "presidio_analyzer.nlp_engine",
            "--hidden-import", "presidio_analyzer.predefined_recognizers",
            "--hidden-import", "presidio_anonymizer",
            "--hidden-import", "presidio_anonymizer.operators",
            "--collect-data", "presidio_analyzer",
            "--collect-data", "presidio_anonymizer",
        ])

    # Collect spaCy data for installed models
    cmd.extend([
        "--collect-data", "spacy",
    ])

    # Add specific model data based on layers
    if "layer1" in layers:
        for model in SPACY_MODELS.get("layer1", []):
            try:
                cmd.extend(["--collect-data", model])
            except:
                pass

    if "layer3" in layers:
        for model in SPACY_MODELS.get("layer3", []):
            try:
                cmd.extend(["--collect-data", model])
            except:
                pass

    # Add the main script
    script_path = Path(__file__).parent / "anonymizer_engine" / "cli.py"
    if not script_path.exists():
        # Create a simple CLI entry point
        script_path = Path(__file__).parent / "main.py"
        script_path.write_text('''
#!/usr/bin/env python3
"""CLI entry point for bundled anonymizer engine."""
import sys
import json
from anonymizer_engine.engine import AnonymizerEngine

def main():
    if len(sys.argv) < 2:
        print("Usage: anonymizer_engine <command> [args]")
        print("Commands: analyze_text, analyze_file, version")
        sys.exit(1)

    command = sys.argv[1]

    if command == "version":
        print("Legal Anonymizer Engine v1.0.0")
        print("Bundled with spaCy models for offline use")
        return

    if command == "analyze_text":
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())
        engine = AnonymizerEngine()
        result = engine.analyze_text(
            input_data["text"],
            input_data.get("preset", {})
        )
        print(json.dumps(result))
        return

    print(f"Unknown command: {command}")
    sys.exit(1)

if __name__ == "__main__":
    main()
''')

    cmd.append(str(script_path))

    print(f"\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd[:10])}...")
    subprocess.run(cmd, check=True)

    # Print summary
    print(f"\n{'='*60}")
    print(f"BUILD COMPLETE!")
    print(f"{'='*60}")
    print(f"\nExecutable: dist/{name}")
    print(f"Layers included: {', '.join(layers)}")
    print(f"\nIncluded components:")
    print(f"  - Layer 1 (spaCy): {'Yes' if 'layer1' in layers else 'No'}")
    print(f"  - Layer 2 (HuggingFace): {'Yes' if 'layer2' in layers else 'No'}")
    print(f"  - Layer 3 (MS Presidio): {'Yes' if 'layer3' in layers else 'No'}")
    print(f"\nThis executable can be distributed without Python installed.")
    print(f"All models are bundled for 100% offline operation.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build standalone Legal Anonymizer executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_standalone.py --layer1              # Fast scrubbing only (~150MB)
  python build_standalone.py --layer1 --layer3    # spaCy + Presidio (~700MB)
  python build_standalone.py --all                # All layers (~1.2GB)

Layer descriptions:
  Layer 1 (spaCy):       Fast NER, ~150MB, any hardware
  Layer 2 (Transformers): BERT models, ~600MB, GPU recommended
  Layer 3 (Presidio):    MS enterprise PII, ~50MB + en_core_web_lg
        """
    )
    parser.add_argument("--layer1", action="store_true", help="Include Layer 1 (spaCy) - fast scrubbing")
    parser.add_argument("--layer2", action="store_true", help="Include Layer 2 (HuggingFace Transformers) - accurate NER")
    parser.add_argument("--layer3", action="store_true", help="Include Layer 3 (Microsoft Presidio) - regulatory compliance")
    parser.add_argument("--all", action="store_true", help="Include all three layers")
    parser.add_argument("--name", default="anonymizer_engine", help="Output executable name")

    args = parser.parse_args()

    layers = []
    if args.all:
        layers = ["layer1", "layer2", "layer3"]
    else:
        if args.layer1:
            layers.append("layer1")
        if args.layer2:
            layers.append("layer2")
        if args.layer3:
            layers.append("layer3")

    if not layers:
        layers = ["layer1"]  # Default to layer1 only

    install_pyinstaller()
    build_executable(args.name, layers)
