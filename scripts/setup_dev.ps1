# Development Environment Setup Script for Legal Anonymizer (PowerShell)

Write-Host "`n🚀 Legal Anonymizer - Development Environment Setup" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# Check Python version
Write-Host "`nChecking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1 | Select-String -Pattern "(\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches[0].Value }
$requiredVersion = [version]"3.10.0"

if ([version]$pythonVersion -ge $requiredVersion) {
    Write-Host "✓ Python $pythonVersion (>= 3.10)" -ForegroundColor Green
} else {
    Write-Host "✗ Python $pythonVersion is too old. Requires >= 3.10" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "! Virtual environment already exists" -ForegroundColor Yellow
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip wheel setuptools
Write-Host "✓ pip upgraded" -ForegroundColor Green

# Install package with all dependencies
Write-Host "`nInstalling legal-anonymizer with all dependencies..." -ForegroundColor Yellow
Set-Location engine\python
pip install -e ".[all,dev]"
Write-Host "✓ Package installed" -ForegroundColor Green
Set-Location ..\..

# Download spaCy models
Write-Host "`nDownloading spaCy models..." -ForegroundColor Yellow
python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm
python -m spacy download de_core_news_sm
Write-Host "✓ spaCy models downloaded" -ForegroundColor Green

# Install pre-commit hooks
Write-Host "`nInstalling pre-commit hooks..." -ForegroundColor Yellow
pre-commit install
Write-Host "✓ Pre-commit hooks installed" -ForegroundColor Green

# Run pre-commit on all files (initial check)
Write-Host "`nRunning initial pre-commit checks..." -ForegroundColor Yellow
pre-commit run --all-files
if ($LASTEXITCODE -ne 0) {
    Write-Host "! Some pre-commit checks failed (expected on first run)" -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "`nCreating project directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path data\input | Out-Null
New-Item -ItemType Directory -Force -Path data\output | Out-Null
New-Item -ItemType Directory -Force -Path models | Out-Null
New-Item -ItemType Directory -Force -Path .coverage_html | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

# Run quick test
Write-Host "`nRunning quick validation..." -ForegroundColor Yellow
python scripts\quick_test.py
$quickTestStatus = $LASTEXITCODE

Write-Host "`n======================================================" -ForegroundColor Cyan
if ($quickTestStatus -eq 0) {
    Write-Host "✅ Development environment setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Activate virtual environment: .\.venv\Scripts\Activate.ps1"
    Write-Host "  2. Run tests: make test (or pytest directly)"
    Write-Host "  3. Run linters: make lint (or ruff/mypy directly)"
    Write-Host "  4. Start developing!"
} else {
    Write-Host "⚠️  Setup complete but quick tests had issues" -ForegroundColor Yellow
    Write-Host "Check errors above and verify installation."
}
Write-Host "======================================================" -ForegroundColor Cyan
