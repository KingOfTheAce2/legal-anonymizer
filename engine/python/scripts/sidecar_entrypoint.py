#!/usr/bin/env python3
"""
Sidecar Entrypoint - Main interface between Tauri desktop app and Python engine.

Commands:
- analyze_text: Analyze text with specified layer (1/2/3)
- analyze_file: Analyze a single file (DOCX, PDF, PPTX, TXT) with specified layer
- get_supported_extensions: List supported file types
- get_model_status: Check installed spaCy/HF/Presidio models
- download_model: Download spaCy or HuggingFace model
- uninstall_model: Remove downloaded model
- get_disk_usage: Return cache disk usage

Input: JSON via --payload-file <path>
Output: JSON via stdout
"""

import json
import os
import sys

# When running as a PyInstaller frozen binary, add _MEIPASS to sys.path so
# that bundled spaCy models (and other packages) are importable.
if getattr(sys, "frozen", False):
    _meipass = getattr(sys, "_MEIPASS", "")
    if _meipass and _meipass not in sys.path:
        sys.path.insert(0, _meipass)

# Force UTF-8 I/O with surrogate replacement to prevent UnicodeEncodeError on
# Windows when documents contain unusual characters or spaCy emits surrogate bytes.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Redirect Python warnings to stderr so they never corrupt the stdout JSON stream.
import warnings
warnings.filterwarnings("default")
import logging
logging.getLogger("spacy").setLevel(logging.ERROR)
logging.getLogger("presidio_analyzer").setLevel(logging.ERROR)
logging.getLogger("presidio_anonymizer").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# Silence spaCy's wasabi Printer — it writes to stdout by default.
# Patch it to use stderr before any spaCy imports happen.
try:
    import wasabi
    _orig_wasabi_writer = wasabi.Printer.__init__
    def _wasabi_stderr_init(self, *args, **kwargs):
        kwargs.setdefault("file", sys.stderr)
        _orig_wasabi_writer(self, *args, **kwargs)
    wasabi.Printer.__init__ = _wasabi_stderr_init
except Exception:
    pass
from dataclasses import asdict
from typing import Any, Dict

from langdetect import detect, DetectorFactory

from anonymizer_engine.preset import Preset
from anonymizer_engine.layer1 import analyze_layer1_text
from anonymizer_engine.layer2_candle import analyze_layer2_text
from anonymizer_engine.layer3_presidio import analyze_layer3_text
from anonymizer_engine.docx_scrubber import scrub_docx
from anonymizer_engine.pdf_scrubber import scrub_pdf
from anonymizer_engine.pptx_scrubber import scrub_pptx
from anonymizer_engine.file_dispatcher import default_dispatcher, safe_basename
from anonymizer_engine.report import (
    build_model_inventory,
    build_run_report,
    make_run_folder,
    new_run_id,
    preset_to_json,
    sha256_text,
    sha256_file,
    write_findings_csv,
    write_json,
)

# Ensure reproducible language detection
DetectorFactory.seed = 0

# Base folder for run artifacts
RUNS_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs"))


# ---------------------------------------------------------------------------
# Audit logger
# ---------------------------------------------------------------------------
import datetime
import platform


def _get_log_dir() -> str:
    """Return (and create) the platform-appropriate log directory."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Logs")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    log_dir = os.path.join(base, "RedactlyLegal", "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _audit_log(event: str, fields: Dict[str, Any]) -> None:
    """Append one JSON-Lines audit record to the daily log file.

    Log file: <AppData>/RedactlyLegal/logs/audit-YYYY-MM-DD.jsonl
    Each line is a self-contained JSON object — easy to parse, grep, or
    ingest into a SIEM.  Text content is never written; only metadata.
    """
    try:
        now = datetime.datetime.utcnow()
        record = {
            "ts": now.isoformat(timespec="seconds") + "Z",
            "event": event,
            **fields,
        }
        log_dir = _get_log_dir()
        log_file = os.path.join(log_dir, f"audit-{now.strftime('%Y-%m-%d')}.jsonl")
        with open(log_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging must never break the main flow


def parse_preset(d: Dict[str, Any]) -> Preset:
    """Parse a preset dictionary into a Preset object, filtering unknown keys."""
    import dataclasses
    known = {f.name for f in dataclasses.fields(Preset)}
    filtered = {k: v for k, v in d.items() if k in known}
    return Preset(**filtered)


def detect_language(text: str) -> str:
    """Detect language of text, defaulting to English."""
    try:
        return detect(text)
    except Exception:
        return "en"


def analyze_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze text using the specified layer.

    Input payload:
        - text: The text to analyze
        - preset: Preset configuration
        - model_path: (optional) Path to model for Layer 2

    Returns:
        - run_id: Unique run identifier
        - run_folder: Path to run artifacts
        - redacted_text: Anonymized text
        - summary: Entity counts
        - findings_count: Total findings
    """
    preset = parse_preset(payload["preset"])
    text = payload["text"]
    model_path = payload.get("model_path", "")

    # Determine language
    if preset.language_mode == "fixed" and preset.language:
        language = preset.language
    else:
        language = detect_language(text)

    # Create run folder
    run_id = new_run_id()
    run_folder = make_run_folder(RUNS_BASE, run_id)

    _t0 = datetime.datetime.utcnow()

    # Select layer-specific analyzer
    if preset.layer == 1:
        redacted, findings, summary = analyze_layer1_text(text, preset, language)
    elif preset.layer == 2:
        redacted, findings, summary = analyze_layer2_text(text, preset, language, model_path)
    elif preset.layer == 3:
        redacted, findings, summary = analyze_layer3_text(text, preset, language)
    else:
        # Default to Layer 1
        redacted, findings, summary = analyze_layer1_text(text, preset, language)

    elapsed_ms = int((datetime.datetime.utcnow() - _t0).total_seconds() * 1000)

    # Write artifacts
    write_json(os.path.join(run_folder, "preset_used.json"), preset_to_json(preset))
    write_json(os.path.join(run_folder, "model_inventory.json"), build_model_inventory())
    write_json(os.path.join(run_folder, "run_report.json"),
               build_run_report(run_id, preset, summary, 1))

    write_findings_csv(
        os.path.join(run_folder, "findings.csv"),
        run_id,
        sha256_text(text),
        findings,
    )

    _audit_log("analyze_text", {
        "run_id": run_id,
        "layer": preset.layer,
        "preset_name": preset.name,
        "language": language,
        "input_chars": len(text),
        "input_sha256": sha256_text(text),
        "findings_count": len(findings),
        "summary": summary,
        "elapsed_ms": elapsed_ms,
        "uncertainty_policy": preset.uncertainty_policy,
        "minimum_confidence": preset.minimum_confidence,
    })

    # Write redacted output
    with open(os.path.join(run_folder, "output", "TEXT_0001_redacted.txt"), "w", encoding="utf-8") as f:
        f.write(redacted)

    # Build findings list for highlight feature
    findings_list = []
    for f in findings:
        findings_list.append({
            "entity_type": f.entity_type,
            "detected_text": f.detected_text,
            "start": f.start_pos,
            "end": f.end_pos,
            "confidence": f.confidence_score,
            "action": f.redaction_action,
            "pseudonym": f.pseudonym_value,
        })

    return {
        "run_id": run_id,
        "run_folder": run_folder,
        "redacted_text": redacted,
        "summary": summary,
        "findings_count": len(findings),
        "language": language,
        "findings": findings_list,
    }


def analyze_file(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single file.

    Input payload:
        - input_path: Path to input file
        - preset: Preset configuration

    Returns:
        - run_id: Unique run identifier
        - run_folder: Path to run artifacts
        - output_path: Path to redacted file
        - summary: Entity counts
    """
    preset = parse_preset(payload["preset"])
    input_path = payload["input_path"]

    # Determine language
    if preset.language_mode == "fixed" and preset.language:
        language = preset.language
    else:
        language = None  # resolved per file type below

    # Create run folder
    run_id = new_run_id()
    run_folder = make_run_folder(RUNS_BASE, run_id)
    output_folder = os.path.join(run_folder, "output")
    _t0 = datetime.datetime.utcnow()

    # Determine file type and process
    ext = os.path.splitext(input_path)[1].lower()
    filename = safe_basename(input_path)
    file_id = "FILE_00001"

    def _redacted_name(fname: str, ext: str) -> str:
        """Build output filename, stripping any existing _redacted suffix to avoid duplication."""
        stem = fname[:-len(ext)] if fname.lower().endswith(ext) else fname
        if stem.endswith("_redacted"):
            stem = stem[:-9]
        return stem + "_redacted" + ext

    if ext == ".docx":
        if language is None:
            # Auto-detect: preset.language_mode == "auto" and no user default was set.
            # Full text extraction + langdetect would work but is costly; default to "en".
            # Users can override this via the "Default document language" setting in the UI,
            # which sets language_mode="fixed" and language=<code> on the preset.
            language = "en"
        out_name = _redacted_name(filename, ".docx")
        output_path = os.path.join(output_folder, out_name)
        findings, summary = scrub_docx(input_path, output_path, preset, language, file_id)
    elif ext == ".pdf":
        if language is None:
            language = "en"
        out_name = _redacted_name(filename, ".pdf")
        output_path = os.path.join(output_folder, out_name)
        findings, summary = scrub_pdf(input_path, output_path, preset, language, file_id)
    elif ext == ".pptx":
        if language is None:
            language = "en"
        out_name = _redacted_name(filename, ".pptx")
        output_path = os.path.join(output_folder, out_name)
        findings, summary = scrub_pptx(input_path, output_path, preset, language, file_id)
    elif ext == ".txt":
        out_name = _redacted_name(filename, ".txt")
        output_path = os.path.join(output_folder, out_name)

        with open(input_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        if language is None:
            language = detect_language(text)

        if preset.layer == 2:
            from anonymizer_engine.layer2_candle import analyze_layer2_text
            redacted, findings, summary = analyze_layer2_text(text, preset, language)
        elif preset.layer == 3:
            from anonymizer_engine.layer3_presidio import analyze_layer3_text
            redacted, findings, summary = analyze_layer3_text(text, preset, language)
        else:
            redacted, findings, summary = analyze_layer1_text(text, preset, language)

        for fd in findings:
            fd.file_id = file_id
            fd.original_filename = filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(redacted)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Write artifacts
    write_json(os.path.join(run_folder, "preset_used.json"), preset_to_json(preset))
    write_json(os.path.join(run_folder, "model_inventory.json"), build_model_inventory())
    write_json(os.path.join(run_folder, "run_report.json"),
               build_run_report(run_id, preset, summary, 1))

    write_findings_csv(
        os.path.join(run_folder, "findings.csv"),
        run_id,
        sha256_file(input_path),
        findings,
    )

    elapsed_ms = int((datetime.datetime.utcnow() - _t0).total_seconds() * 1000)
    _audit_log("analyze_file", {
        "run_id": run_id,
        "layer": preset.layer,
        "preset_name": preset.name,
        "language": language,
        "file_type": ext,
        "input_sha256": sha256_file(input_path),
        "findings_count": len(findings),
        "summary": summary,
        "elapsed_ms": elapsed_ms,
        "uncertainty_policy": preset.uncertainty_policy,
        "minimum_confidence": preset.minimum_confidence,
    })

    return {
        "run_id": run_id,
        "run_folder": run_folder,
        "output_path": output_path,
        "summary": summary,
        "findings_count": len(findings),
    }


def analyze_docx(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy command for DOCX analysis. Delegates to analyze_file."""
    return analyze_file(payload)


def get_supported_extensions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return list of supported file extensions."""
    return {
        "extensions": default_dispatcher.supported_extensions(),
    }


def _get_user_models_dir() -> str:
    """Return (and create) the user-writable directory for downloaded spaCy models."""
    import platform
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    models_dir = os.path.join(base, "RedactlyLegal", "spacy_models")
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def _ensure_user_models_on_path() -> None:
    """Prepend the user models directory to sys.path so spaCy can find downloaded models."""
    models_dir = _get_user_models_dir()
    if models_dir not in sys.path:
        sys.path.insert(0, models_dir)


def _download_spacy_model_frozen(model_id: str) -> None:
    """
    Download a spaCy model .whl from GitHub releases and extract it to the
    user models directory.  Called when the app is a PyInstaller frozen binary.
    Progress is reported as JSON lines on stdout for the Rust streaming reader.
    """
    import urllib.request
    import zipfile
    import spacy

    models_dir = _get_user_models_dir()

    # Model version tracks spaCy major.minor (e.g. spaCy 3.8.4 → model 3.8.0)
    ver_parts = spacy.__version__.split(".")
    model_version = f"{ver_parts[0]}.{ver_parts[1]}.0"

    url = (
        f"https://github.com/explosion/spacy-models/releases/download/"
        f"{model_id}-{model_version}/"
        f"{model_id}-{model_version}-py3-none-any.whl"
    )

    whl_path = os.path.join(models_dir, f"{model_id}.whl")

    def _reporthook(block_num: int, block_size: int, total_size: int) -> None:
        if total_size > 0:
            percent = min(99, int(block_num * block_size * 100 / total_size))
            print(
                json.dumps({"__progress__": {"model_id": model_id, "percent": percent}}),
                flush=True,
            )

    try:
        urllib.request.urlretrieve(url, whl_path, reporthook=_reporthook)
    except Exception as exc:
        raise RuntimeError(f"Download failed for {model_id}: {exc}") from exc

    try:
        with zipfile.ZipFile(whl_path, "r") as zf:
            zf.extractall(models_dir)
    finally:
        try:
            os.remove(whl_path)
        except OSError:
            pass

    _ensure_user_models_on_path()


def get_model_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Check which models/packages are installed."""
    # Make sure any previously user-downloaded models are visible to spaCy
    _ensure_user_models_on_path()

    status: Dict[str, Any] = {
        "spacy_models": {},
        "presidio_available": False,
        "transformers_available": False,
    }

    # Check spaCy models — large where available (preferred for accuracy), small where no lg exists.
    # en_core_web_sm is always bundled; all other models are user-downloaded.
    try:
        import spacy
        for model_name in [
            # EU official languages — large preferred (downloaded via Setup)
            "bg_core_news_lg",   # Bulgarian
            "hr_core_news_sm",   # Croatian  (no lg released)
            "cs_core_news_lg",   # Czech
            "da_core_news_lg",   # Danish
            "nl_core_news_lg",   # Dutch
            "en_core_web_sm",    # English   (bundled in binary)
            "en_core_web_lg",    # English   (optional large download)
            "fi_core_news_lg",   # Finnish
            "fr_core_news_lg",   # French
            "de_core_news_lg",   # German
            "el_core_news_lg",   # Greek
            "it_core_news_lg",   # Italian
            "lt_core_news_lg",   # Lithuanian
            "pl_core_news_lg",   # Polish
            "pt_core_news_lg",   # Portuguese
            "ro_core_news_lg",   # Romanian
            "sk_core_news_lg",   # Slovak
            "sl_core_news_lg",   # Slovenian
            "es_core_news_lg",   # Spanish
            "sv_core_news_lg",   # Swedish
            # Additional languages
            "ru_core_news_lg",   # Russian
            "zh_core_web_lg",    # Chinese
            "ja_core_news_lg",   # Japanese
            "ko_core_news_sm",   # Korean    (no lg released)
        ]:
            try:
                spacy.load(model_name)
                status["spacy_models"][model_name] = "installed"
            except OSError:
                status["spacy_models"][model_name] = "not_installed"
    except ImportError:
        pass

    # Check Presidio
    try:
        import presidio_analyzer  # noqa: F401
        import presidio_anonymizer  # noqa: F401
        status["presidio_available"] = True
    except Exception as _presidio_err:
        # Log the actual error to help with debugging (written to stderr, not stdout)
        print(f"[presidio import error] {type(_presidio_err).__name__}: {_presidio_err}", file=sys.stderr)
        pass

    # Check Transformers
    try:
        import transformers  # noqa: F401
        status["transformers_available"] = True
    except ImportError:
        pass

    return status


def download_model(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Download a model or install a package.

    Input payload:
        - model_type: "spacy" | "huggingface" | "presidio"
        - model_id: model name (e.g. "en_core_web_sm", "dslim/bert-base-NER", "presidio-analyzer")
    """
    import subprocess

    model_type = payload.get("model_type", "")
    model_id = payload.get("model_id", "")

    if not model_type or not model_id:
        raise ValueError("model_type and model_id are required")

    # In a PyInstaller frozen binary sys.executable is the frozen .exe, NOT the
    # Python interpreter, so `sys.executable -m spacy download` would fail.
    is_frozen = getattr(sys, "frozen", False)

    def _progress(pct: int) -> None:
        """Emit a progress JSON line that the Rust streaming reader picks up."""
        print(json.dumps({"__progress__": {"model_id": model_id, "percent": pct}}), flush=True)

    if model_type == "spacy":
        if is_frozen:
            _download_spacy_model_frozen(model_id)  # reports its own fine-grained progress
        else:
            _progress(10)
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", model_id],
                check=True,
                capture_output=True,
            )
            _progress(99)
        _audit_log("model_download", {"model_type": "spacy", "model_id": model_id, "status": "installed"})
        return {"status": "installed", "model_id": model_id}

    elif model_type == "huggingface":
        # Download model files one-by-one so we can emit per-file progress.
        # snapshot_download gives no intermediate callbacks, so we enumerate
        # the repo file list first then call hf_hub_download per file.
        try:
            from huggingface_hub import HfApi, hf_hub_download
        except ImportError:
            raise RuntimeError(
                "huggingface_hub is not available in this build. "
                "Cannot download HuggingFace models."
            )

        SKIP_PATTERNS = ("*.msgpack", "flax_model*", "tf_model*", "rust_model*")

        def _should_skip(filename: str) -> bool:
            import fnmatch
            return any(fnmatch.fnmatch(filename, pat) for pat in SKIP_PATTERNS)

        _progress(2)

        # List repo files (fast metadata call) — list_repo_files returns plain strings
        api = HfApi()
        all_files = [
            f for f in api.list_repo_files(model_id, repo_type="model")
            if not _should_skip(f)
        ]

        total = max(len(all_files), 1)
        for i, filename in enumerate(all_files):
            hf_hub_download(repo_id=model_id, filename=filename)
            pct = max(3, min(98, int((i + 1) * 98 / total)))
            _progress(pct)

        _progress(99)
        _audit_log("model_download", {"model_type": "huggingface", "model_id": model_id, "status": "installed"})
        return {"status": "installed", "model_id": model_id}

    elif model_type == "presidio":
        if is_frozen:
            # Presidio is bundled inside the frozen binary via collect_all() in the spec.
            # Verify it's importable — if so, nothing to install.
            try:
                import presidio_analyzer  # noqa: F401
                import presidio_anonymizer  # noqa: F401
                return {"status": "installed", "model_id": model_id}
            except ImportError:
                raise RuntimeError(
                    "Presidio requires the full installer. "
                    "Download the 'all layers' build to enable Thorough mode."
                )
        _progress(10)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", model_id],
            check=True,
            capture_output=True,
        )
        _progress(99)
        return {"status": "installed", "model_id": model_id}

    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def _dir_size_bytes(path: str) -> int:
    """Return total byte size of a directory tree, or 0 if it doesn't exist."""
    total = 0
    if not os.path.isdir(path):
        return 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for fname in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, fname))
            except OSError:
                pass
    return total


def _hf_cache_dir() -> str:
    """Return the HuggingFace hub cache directory."""
    import pathlib
    # Respect HF_HOME / HUGGINGFACE_HUB_CACHE env vars if set
    hf_home = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if hf_home:
        return str(pathlib.Path(hf_home) / "hub")
    return str(pathlib.Path.home() / ".cache" / "huggingface" / "hub")


def get_disk_usage(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return disk usage (bytes) for each model store.

    Returns:
        {
          "spacy_models_bytes": int,
          "hf_cache_bytes": int,
          "spacy_models_path": str,
          "hf_cache_path": str,
        }
    """
    spacy_dir = _get_user_models_dir()
    hf_dir = _hf_cache_dir()
    return {
        "spacy_models_bytes": _dir_size_bytes(spacy_dir),
        "hf_cache_bytes": _dir_size_bytes(hf_dir),
        "spacy_models_path": spacy_dir,
        "hf_cache_path": hf_dir,
    }


def uninstall_model(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Remove a downloaded model from disk.

    Input payload:
        - model_type: "spacy" | "huggingface"
        - model_id: model name (e.g. "en_core_web_sm", "dslim/bert-base-NER")

    Presidio is bundled into the frozen binary and cannot be uninstalled.
    """
    import shutil

    model_type = payload.get("model_type", "")
    model_id = payload.get("model_id", "")

    if not model_type or not model_id:
        raise ValueError("model_type and model_id are required")

    if model_type == "spacy":
        models_dir = _get_user_models_dir()

        # The .whl extraction puts files like:
        #   <models_dir>/en_core_web_sm/
        #   <models_dir>/en_core_web_sm-3.x.x.dist-info/
        removed = []
        for entry in os.listdir(models_dir) if os.path.isdir(models_dir) else []:
            if entry == model_id or entry.startswith(model_id + "-"):
                target = os.path.join(models_dir, entry)
                try:
                    shutil.rmtree(target)
                    removed.append(entry)
                except OSError as e:
                    raise RuntimeError(f"Could not remove {target}: {e}") from e

        if not removed:
            # Also try the standard system spaCy install location (non-frozen)
            is_frozen = getattr(sys, "frozen", False)
            if not is_frozen:
                try:
                    import subprocess
                    subprocess.run(
                        [sys.executable, "-m", "pip", "uninstall", "-y", model_id],
                        check=True,
                        capture_output=True,
                    )
                    removed.append(model_id)
                except Exception as e:
                    raise RuntimeError(f"Model '{model_id}' not found in user model dir and pip uninstall failed: {e}") from e

        _audit_log("model_uninstall", {"model_type": "spacy", "model_id": model_id, "removed": removed})
        return {"status": "uninstalled", "model_id": model_id, "removed": removed}

    elif model_type == "huggingface":
        import shutil

        hf_dir = _hf_cache_dir()
        # HuggingFace stores models as: models--{org}--{repo}
        safe_id = model_id.replace("/", "--")
        model_cache_dir = os.path.join(hf_dir, f"models--{safe_id}")

        if not os.path.isdir(model_cache_dir):
            raise RuntimeError(
                f"HuggingFace model '{model_id}' not found in cache at {model_cache_dir}"
            )

        shutil.rmtree(model_cache_dir)
        _audit_log("model_uninstall", {"model_type": "huggingface", "model_id": model_id})
        return {"status": "uninstalled", "model_id": model_id}

    elif model_type == "presidio":
        raise RuntimeError(
            "Presidio is bundled into the application and cannot be uninstalled. "
            "It uses no additional disk space beyond the app itself."
        )

    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def main() -> None:
    """Main entry point - parse command and execute."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command specified"}))
        sys.exit(1)

    cmd = sys.argv[1]

    # Support --payload-file <path> (file-based IPC, avoids Windows stdin pipe issues).
    # Falls back to stdin for backward compatibility / dev use.
    payload_file: str | None = None
    if "--payload-file" in sys.argv:
        idx = sys.argv.index("--payload-file")
        if idx + 1 < len(sys.argv):
            payload_file = sys.argv[idx + 1]

    try:
        if payload_file:
            with open(payload_file, "r", encoding="utf-8") as fh:
                raw = fh.read()
            try:
                os.remove(payload_file)
            except OSError:
                pass
        else:
            if sys.stdin is None:
                print(json.dumps({"error": "stdin unavailable: use --payload-file or rebuild with console=True"}))
                sys.exit(1)
            raw = sys.stdin.read()
        payload = json.loads(raw)
    except Exception as exc:
        print(json.dumps({"error": f"failed to read/parse payload: {exc}"}))
        sys.exit(1)

    handlers = {
        "analyze_text": analyze_text,
        "analyze_file": analyze_file,
        "analyze_docx": analyze_docx,
        "get_supported_extensions": get_supported_extensions,
        "get_model_status": get_model_status,
        "download_model": download_model,
        "uninstall_model": uninstall_model,
        "get_disk_usage": get_disk_usage,
    }

    if cmd not in handlers:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    try:
        result = handlers[cmd](payload)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
