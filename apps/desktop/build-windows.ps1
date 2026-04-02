# Build Legal Anonymizer for Windows
# Creates both portable EXE and MSI installer

Write-Host "`n Legal Anonymizer - Windows Build Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check Node.js
Write-Host "`nChecking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "OK Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "FAIL Node.js not found. Install from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Check Rust
Write-Host "Checking Rust..." -ForegroundColor Yellow
try {
    $rustVersion = rustc --version
    Write-Host "OK Rust $rustVersion" -ForegroundColor Green
} catch {
    Write-Host "FAIL Rust not found. Install from https://rustup.rs" -ForegroundColor Red
    exit 1
}

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "OK Python $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "FAIL Python not found" -ForegroundColor Red
    exit 1
}

# ── Step 1: Build the Python sidecar ──────────────────────────────────────────
Write-Host "`nStep 1/3 — Building Python sidecar (this takes a few minutes)..." -ForegroundColor Cyan

Push-Location "$PSScriptRoot\..\engine\python"

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -e ".[layer1,layer2,layer3,pdf,docx,pptx]"
pip install pyinstaller

Write-Host "Downloading spaCy language models..." -ForegroundColor Yellow
python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm
python -m spacy download de_core_news_sm
python -m spacy download fr_core_news_sm
python -m spacy download es_core_news_sm
python -m spacy download it_core_news_sm
python -m spacy download pt_core_news_sm
python -m spacy download pl_core_news_sm
python -m spacy download en_core_web_lg

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
python build_standalone.py --layer1 --layer2 --layer3 --name anonymizer_engine

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL Sidecar build failed." -ForegroundColor Red
    Pop-Location
    exit 1
}

# ── Step 2: Copy sidecar to Tauri binaries folder ─────────────────────────────
Write-Host "`nStep 2/3 — Copying sidecar into Tauri binaries folder..." -ForegroundColor Cyan

$sidecarSrc = "dist\anonymizer_engine.exe"
$sidecarDst = "$PSScriptRoot\src-tauri\binaries\anonymizer_engine-x86_64-pc-windows-msvc.exe"

Copy-Item -Force $sidecarSrc $sidecarDst
Write-Host "OK Sidecar copied: $(Get-Item $sidecarDst | Select-Object -ExpandProperty Length | ForEach-Object { [math]::Round($_ / 1MB, 1) }) MB" -ForegroundColor Green

Pop-Location

# ── Step 3: Build Tauri installer ─────────────────────────────────────────────
Write-Host "`nStep 3/3 — Building Tauri installer..." -ForegroundColor Cyan

Push-Location $PSScriptRoot

npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL npm install failed." -ForegroundColor Red
    Pop-Location
    exit 1
}

npm run tauri build

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nOK Windows build complete!" -ForegroundColor Green
    Write-Host "`nInstallers created:" -ForegroundColor Cyan
    Write-Host "   MSI:  src-tauri\target\release\bundle\msi\*.msi"
    Write-Host "   NSIS: src-tauri\target\release\bundle\nsis\*-setup.exe"

    Write-Host "`nFile sizes:" -ForegroundColor Cyan
    Get-ChildItem "src-tauri\target\release\bundle\msi\*.msi" -ErrorAction SilentlyContinue |
        Select-Object Name, @{Name="Size (MB)"; Expression={[math]::Round($_.Length / 1MB, 1)}}
    Get-ChildItem "src-tauri\target\release\bundle\nsis\*.exe" -ErrorAction SilentlyContinue |
        Select-Object Name, @{Name="Size (MB)"; Expression={[math]::Round($_.Length / 1MB, 1)}}

    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "1. Test the MSI on a clean Windows VM (no dev tools installed)"
    Write-Host "2. Sign the installer (optional but removes SmartScreen warning)"
    Write-Host "3. Distribute!"
} else {
    Write-Host "`nFAIL Tauri build failed. Check errors above." -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
