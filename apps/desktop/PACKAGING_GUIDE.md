# Legal Anonymizer - Desktop App Packaging Guide

## 🎯 Quick Answer: YES! Easy One-Click Installers for Lawyers

Your Tauri app can be packaged into:
- **Windows:** `.exe` (portable) or `.msi` (installer)
- **macOS:** `.dmg` (drag-to-install) or `.app` (application bundle)
- **Linux:** `.deb`, `.AppImage`, or `.rpm`

## 📦 What Lawyers Get

**Single file downloads:**
- `Legal-Anonymizer-Setup-0.1.0.exe` (Windows installer)
- `Legal-Anonymizer-0.1.0.dmg` (Mac installer)
- `legal-anonymizer_0.1.0_amd64.deb` (Linux)

**No technical knowledge required:**
1. Double-click installer
2. Follow simple wizard (Next → Next → Install)
3. Launch app from Desktop/Start Menu
4. Drag & drop legal documents
5. Click "Anonymize"
6. Done!

---

## 🚀 Build Installers (Developer Instructions)

### Prerequisites

**All Platforms:**
- Node.js 18+ (`node --version`)
- Rust (`rustc --version`)
- Python 3.10+ with anonymizer-engine installed

**Windows Specific:**
- Visual Studio Build Tools (for native modules)
- WiX Toolset 3.11+ (for `.msi` installers)

**macOS Specific:**
- Xcode Command Line Tools
- Apple Developer Certificate (for signing, optional)

**Linux Specific:**
- `build-essential`, `libgtk-3-dev`, `libwebkit2gtk-4.0-dev`

---

### 1. Install Dependencies

```bash
cd apps/desktop

# Install Node dependencies
npm install

# Verify Tauri CLI
npm run tauri -- --version
```

---

### 2. Build for Production

#### Windows (EXE + MSI)

```bash
# Build both EXE and MSI installers
npm run tauri build

# Output location:
# - src-tauri/target/release/Legal Anonymizer.exe (portable)
# - src-tauri/target/release/bundle/msi/Legal Anonymizer_0.1.0_x64_en-US.msi
```

**What lawyers get:**
- **Portable EXE:** No installation, just run
- **MSI Installer:** Professional Windows installer with Start Menu shortcuts

#### macOS (DMG + APP)

```bash
# Build DMG installer
npm run tauri build

# Output location:
# - src-tauri/target/release/bundle/dmg/Legal Anonymizer_0.1.0_x64.dmg
# - src-tauri/target/release/bundle/macos/Legal Anonymizer.app
```

**What lawyers get:**
- **DMG:** Drag app to Applications folder
- **APP Bundle:** Ready-to-use macOS application

#### Linux (DEB + AppImage + RPM)

```bash
# Build all Linux formats
npm run tauri build

# Output location:
# - src-tauri/target/release/bundle/deb/legal-anonymizer_0.1.0_amd64.deb
# - src-tauri/target/release/bundle/appimage/legal-anonymizer_0.1.0_amd64.AppImage
# - src-tauri/target/release/bundle/rpm/legal-anonymizer-0.1.0-1.x86_64.rpm
```

---

### 3. Cross-Platform Building (Advanced)

Build for multiple platforms from one machine using GitHub Actions:

```yaml
# .github/workflows/release.yml
name: Release Desktop App

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    strategy:
      matrix:
        platform: [windows-latest, macos-latest, ubuntu-latest]
    runs-on: ${{ matrix.platform }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install dependencies (Linux)
        if: matrix.platform == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y libgtk-3-dev libwebkit2gtk-4.0-dev

      - name: Install frontend dependencies
        run: cd apps/desktop && npm install

      - name: Build Tauri app
        run: cd apps/desktop && npm run tauri build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: legal-anonymizer-${{ matrix.platform }}
          path: apps/desktop/src-tauri/target/release/bundle/
```

Push a tag and get builds for all platforms automatically!

---

## 🎨 Customization for Lawyers

### 1. Add Professional Icons

```bash
# Generate icons from a single 1024x1024 PNG
cd apps/desktop/src-tauri

# Install icon generator
npm install -g @tauri-apps/tauricon

# Generate all sizes
tauricon path/to/your-logo.png
```

This creates:
- `icons/icon.icns` (macOS)
- `icons/icon.ico` (Windows)
- `icons/32x32.png`, `icons/128x128.png` (Linux)

### 2. Customize App Metadata

Edit `apps/desktop/src-tauri/tauri.conf.json`:

```json
{
  "productName": "Legal Anonymizer Pro",
  "version": "1.0.0",
  "identifier": "com.yourfirm.legalanonymizer",
  "bundle": {
    "shortDescription": "GDPR-compliant document anonymization",
    "longDescription": "Professional offline PII detection and redaction for legal documents. Supports 50+ countries, 3 detection layers, and full GDPR compliance.",
    "publisher": "Your Law Firm",
    "copyright": "Copyright © 2026 Your Firm",
    "category": "Office",
    "deb": {
      "depends": []
    },
    "macOS": {
      "minimumSystemVersion": "10.13"
    },
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": ""
    }
  }
}
```

### 3. Add Code Signing (Recommended for Distribution)

#### Windows Code Signing

```bash
# Get a code signing certificate
# Sign the MSI installer
signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com /td sha256 /fd sha256 "Legal Anonymizer.msi"
```

#### macOS Code Signing

```bash
# Requires Apple Developer account ($99/year)
# Sign the app bundle
codesign --sign "Developer ID Application: Your Name" --deep --force --options runtime "Legal Anonymizer.app"

# Notarize with Apple (required for macOS 10.15+)
xcrun altool --notarize-app --primary-bundle-id "com.yourfirm.legalanonymizer" --username "your@email.com" --password "@keychain:AC_PASSWORD" --file "Legal Anonymizer.dmg"
```

---

## 📋 Installer Features You Get

### Windows MSI Installer
- ✅ Start Menu shortcuts
- ✅ Desktop shortcut (optional)
- ✅ Add/Remove Programs entry
- ✅ Automatic updates support
- ✅ Per-user or system-wide install
- ✅ Custom install location

### macOS DMG
- ✅ Drag-to-Applications install
- ✅ Beautiful installer window
- ✅ Automatic code signing
- ✅ Notarization for Gatekeeper
- ✅ Native macOS look and feel

### Linux DEB/RPM
- ✅ System package manager integration
- ✅ Desktop launcher
- ✅ File associations
- ✅ Automatic dependency resolution

---

## 👩‍⚖️ Lawyer User Experience

### First-Time Setup

1. **Download** installer from your website
2. **Double-click** the installer
3. **Click "Next"** through wizard (2-3 clicks)
4. **Launch** from Desktop or Start Menu

### Daily Usage

```
1. Launch "Legal Anonymizer" from Desktop
2. Drag & drop Word/PDF files into window
3. Select anonymization level:
   □ Fast Legal Scrub (Layer 1)
   □ Accurate Legal Review (Layer 2)  ← Recommended
   □ Regulatory Standard (Layer 3)
4. Click "Anonymize Documents"
5. Review findings report
6. Export anonymized files
```

**No terminal. No Python. No technical knowledge required.**

---

## 🚀 Distribution Options

### Option 1: Direct Download (Simple)

Host installers on your website:
```
https://yoursite.com/downloads/
├── Legal-Anonymizer-Setup-Windows.msi
├── Legal-Anonymizer-Mac.dmg
└── legal-anonymizer-Linux.deb
```

### Option 2: Auto-Updates (Advanced)

Enable in `tauri.conf.json`:
```json
{
  "updater": {
    "active": true,
    "endpoints": [
      "https://yoursite.com/updates/{{target}}/{{current_version}}"
    ],
    "dialog": true,
    "pubkey": "YOUR_PUBLIC_KEY"
  }
}
```

App will check for updates on launch and prompt users to install.

### Option 3: App Stores (Professional)

- **Microsoft Store** (Windows)
- **Mac App Store** (macOS)
- **Snap Store** (Linux)

Requires store accounts but provides discoverability and trust.

---

## 📝 Build Checklist

Before distributing to lawyers:

- [ ] Update version in `tauri.conf.json`
- [ ] Add professional icons (1024x1024 source)
- [ ] Test on clean VM (no dev tools)
- [ ] Sign installers (Windows: Authenticode, macOS: Developer ID)
- [ ] Test installation on target OS
- [ ] Verify file associations work
- [ ] Test uninstall process
- [ ] Create user documentation (PDF guide)
- [ ] Set up support email/website
- [ ] Create video tutorial (optional but helpful)

---

## 🎯 Quick Start Commands

```bash
# Development build (test quickly)
cd apps/desktop
npm run tauri dev

# Production build (for distribution)
npm run tauri build

# Build specific format
npm run tauri build -- --target msi  # Windows MSI only
npm run tauri build -- --target dmg  # macOS DMG only
npm run tauri build -- --target deb  # Linux DEB only
```

---

## 📊 File Sizes (Approximate)

| Platform | Format | Size | Notes |
|----------|--------|------|-------|
| Windows | .exe | ~50-80 MB | Portable, no install |
| Windows | .msi | ~50-80 MB | Professional installer |
| macOS | .dmg | ~60-90 MB | Includes Python runtime |
| macOS | .app | ~60-90 MB | Application bundle |
| Linux | .deb | ~50-80 MB | Debian/Ubuntu |
| Linux | .AppImage | ~70-100 MB | Universal, no install |

Sizes include:
- Python runtime
- All dependencies (spaCy models optional)
- Anonymizer engine
- React frontend

---

## 🔐 Security Considerations

1. **Code Signing:** Prevents "Unknown Publisher" warnings
2. **HTTPS Downloads:** Protect installer integrity
3. **Checksums:** Provide SHA-256 hashes for verification
4. **Privacy:** No telemetry, fully offline by default
5. **Updates:** Optional auto-update with user consent

---

## 💡 Tips for Law Firms

1. **Internal Distribution:**
   - Host on firm intranet
   - Include in onboarding package
   - Add to IT-approved software list

2. **Client Distribution:**
   - Provide download link in client portal
   - Include quick-start PDF guide
   - Offer video walkthrough

3. **Branding:**
   - Use firm logo as app icon
   - Customize app name ("Smith & Co Anonymizer")
   - Add firm copyright

4. **Support:**
   - Create FAQ page
   - Provide email support address
   - Include changelog with each release

---

## ❓ Common Questions

**Q: Do lawyers need Python installed?**
A: No! Tauri bundles everything. Just double-click the installer.

**Q: Can they use it offline?**
A: Yes! Completely offline by default. No internet required.

**Q: What about updates?**
A: Optional auto-update or manual download of new versions.

**Q: macOS says "app is damaged"?**
A: Sign and notarize the app. See code signing section above.

**Q: Windows SmartScreen warning?**
A: Get an Extended Validation (EV) code signing certificate (~$400/year).

**Q: Can I white-label it?**
A: Yes! Change all branding in `tauri.conf.json` and icons.

---

## 🎊 Summary

**YES - You can absolutely create lawyer-friendly installers!**

**Lawyer gets:**
1. Single `.msi`/`.dmg`/`.deb` file
2. Double-click to install (2 minutes)
3. Desktop shortcut to launch
4. Drag & drop interface
5. One-click anonymization
6. No technical knowledge needed

**You provide:**
1. Professional installer
2. Quick-start PDF guide
3. Video tutorial (optional)
4. Support email
5. Update notifications

**Next step:** Run `npm run tauri build` and test the installer on a clean machine!
