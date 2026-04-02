# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_all

datas = []
hiddenimports_models = []
datas += collect_data_files('spacy')

# spaCy language models bundled at build time.
# Use collect_all() so both data files AND Python package metadata are included,
# which is required for spacy.load(model_name) to work in the frozen binary.
for _model in [
    'en_core_web_sm',
    'en_core_web_lg',
]:
    try:
        _d, _b, _h = collect_all(_model)
        datas += _d
        hiddenimports_models += _h
    except Exception:
        pass  # model not installed, skip silently

# HuggingFace / transformers data (only present if layer2 was installed)
try:
    datas += collect_data_files('transformers')
except Exception:
    pass

# Presidio — use collect_all() so the packages are importable inside the frozen binary.
# collect_data_files() only copies data files; collect_all() also includes Python package
# metadata which is required for `import presidio_analyzer` to succeed at runtime.
for _pkg in ('presidio_analyzer', 'presidio_anonymizer'):
    try:
        _d, _b, _h = collect_all(_pkg)
        datas += _d
        hiddenimports_models += _h
    except Exception:
        pass

# cryptography — required by presidio as a transitive dependency (e.g. via jwcrypto).
# Must NOT be in excludes; collect_all to bundle C extensions + metadata.
try:
    _d, _b, _h = collect_all('cryptography')
    datas += _d
    hiddenimports_models += _h
except Exception:
    pass

# huggingface_hub — needed for snapshot_download (HF model downloads without full transformers).
try:
    _d, _b, _h = collect_all('huggingface_hub')
    datas += _d
    hiddenimports_models += _h
except Exception:
    pass

# torch + transformers — required for Layer 2 (Accurate mode) inference
try:
    _d, _b, _h = collect_all('torch')
    datas += _d
    hiddenimports_models += _h
except Exception:
    pass

try:
    _d, _b, _h = collect_all('transformers')
    datas += _d
    hiddenimports_models += _h
except Exception:
    pass

try:
    _d, _b, _h = collect_all('tokenizers')
    datas += _d
    hiddenimports_models += _h
except Exception:
    pass

_script = os.path.join(
    os.path.dirname(os.path.abspath(SPEC)),  # noqa: F821  (SPEC is a PyInstaller built-in)
    'scripts',
    'sidecar_entrypoint.py',
)

a = Analysis(
    [_script],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports_models + [
        # spaCy core
        'spacy', 'spacy.lang.en', 'spacy.lang.nl', 'spacy.lang.de',
        'spacy.lang.fr', 'spacy.lang.es', 'spacy.lang.it', 'spacy.lang.pt',
        'spacy.lang.pl', 'spacy.lang.ru', 'spacy.lang.zh', 'spacy.lang.ja',
        'thinc', 'cymem', 'preshed', 'murmurhash', 'blis',
        # Layer 2 — transformer inference (Accurate mode)
        'transformers', 'transformers.models.auto', 'transformers.models.bert',
        'transformers.pipelines', 'transformers.pipelines.token_classification',
        'torch', 'tokenizers',
        # Layer 3
        'presidio_analyzer', 'presidio_analyzer.nlp_engine',
        'presidio_analyzer.predefined_recognizers',
        'presidio_anonymizer', 'presidio_anonymizer.operators',
        # Document scraping
        'docx', 'docx.oxml', 'docx.oxml.ns', 'docx.shared',
        'pptx', 'pptx.util',
        'pdfminer', 'pdfminer.high_level', 'pdfminer.layout',
        'pdfminer.pdfpage', 'pdfminer.pdfinterp', 'pdfminer.converter',
        # Utilities
        'langdetect', 'dateutil', 'dateutil.parser',
        'lxml', 'lxml.etree',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy ML deps — layer2 (transformers/torch) loads lazily at runtime
        'torchvision', 'torchaudio',
        'tensorflow', 'keras',
        'numpy.distutils',
        'matplotlib', 'PIL', 'Pillow',
        'scipy', 'sklearn', 'pandas',
        'IPython', 'notebook', 'jupyter',
        'pytest', 'setuptools', 'pip',
        'yt_dlp', 'youtube_dl',
        # 'cryptography',  # do NOT exclude: presidio requires it
        'Cryptodome',
        'websockets', 'aiohttp',
        'brotli', 'curl_cffi',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='anonymizer_engine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
