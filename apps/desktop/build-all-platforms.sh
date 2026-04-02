#!/bin/bash
# Build Legal Anonymizer for all platforms
# Run this on the respective platform or use GitHub Actions for cross-compilation

set -e

echo "🚀 Legal Anonymizer - Multi-Platform Build Script"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="Windows"
else
    PLATFORM="Linux"
fi

echo -e "${YELLOW}Detected platform: $PLATFORM${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install from https://nodejs.org"
    exit 1
fi
echo "✅ Node.js $(node --version)"

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found"
    exit 1
fi
echo "✅ npm $(npm --version)"

if ! command -v rustc &> /dev/null; then
    echo "❌ Rust not found. Install from https://rustup.rs"
    exit 1
fi
echo "✅ Rust $(rustc --version)"

if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python not found"
    exit 1
fi
PYTHON_CMD=$(command -v python3 || command -v python)
echo "✅ Python $($PYTHON_CMD --version)"

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
npm install
echo "✅ Dependencies installed"

# Build Python engine (optional - include if needed)
echo -e "\n${YELLOW}Building Python anonymizer engine...${NC}"
cd ../../engine/python
$PYTHON_CMD -m pip install build
$PYTHON_CMD -m build
echo "✅ Python engine built"
cd ../../apps/desktop

# Build Tauri app
echo -e "\n${YELLOW}Building Tauri application for $PLATFORM...${NC}"

if [[ "$PLATFORM" == "Windows" ]]; then
    echo "Building Windows installer (.msi and .exe)..."
    npm run tauri build

    echo -e "\n${GREEN}✅ Windows build complete!${NC}"
    echo "📦 Installers located at:"
    echo "   - src-tauri/target/release/Legal Anonymizer.exe (portable)"
    echo "   - src-tauri/target/release/bundle/msi/*.msi (installer)"

elif [[ "$PLATFORM" == "macOS" ]]; then
    echo "Building macOS app bundle and DMG..."
    npm run tauri build

    echo -e "\n${GREEN}✅ macOS build complete!${NC}"
    echo "📦 Installers located at:"
    echo "   - src-tauri/target/release/bundle/dmg/*.dmg"
    echo "   - src-tauri/target/release/bundle/macos/Legal Anonymizer.app"

else
    echo "Building Linux packages (.deb, .AppImage, .rpm)..."
    npm run tauri build

    echo -e "\n${GREEN}✅ Linux build complete!${NC}"
    echo "📦 Installers located at:"
    echo "   - src-tauri/target/release/bundle/deb/*.deb"
    echo "   - src-tauri/target/release/bundle/appimage/*.AppImage"
    echo "   - src-tauri/target/release/bundle/rpm/*.rpm"
fi

# Calculate sizes
echo -e "\n${YELLOW}Package sizes:${NC}"
du -h src-tauri/target/release/bundle/* 2>/dev/null || echo "Check src-tauri/target/release/bundle/"

echo -e "\n${GREEN}=================================================="
echo "🎊 Build successful!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Test the installer on a clean machine"
echo "2. Sign the installer (for production)"
echo "3. Upload to your distribution server"
echo "4. Share with lawyers!"
echo -e "${NC}"
