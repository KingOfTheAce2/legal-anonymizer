#!/bin/bash
# Development Environment Setup Script for Legal Anonymizer

set -e  # Exit on error

echo "🚀 Legal Anonymizer - Development Environment Setup"
echo "======================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION (>= $REQUIRED_VERSION)${NC}"
else
    echo -e "${RED}✗ Python $PYTHON_VERSION is too old. Requires >= $REQUIRED_VERSION${NC}"
    exit 1
fi

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}! Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate || source .venv/Scripts/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip wheel setuptools
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install package with all dependencies
echo -e "\n${YELLOW}Installing legal-anonymizer with all dependencies...${NC}"
cd engine/python
pip install -e ".[all,dev]"
echo -e "${GREEN}✓ Package installed${NC}"
cd ../..

# Download spaCy models
echo -e "\n${YELLOW}Downloading spaCy models...${NC}"
python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm
python -m spacy download de_core_news_sm
echo -e "${GREEN}✓ spaCy models downloaded${NC}"

# Install pre-commit hooks
echo -e "\n${YELLOW}Installing pre-commit hooks...${NC}"
pre-commit install
echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"

# Run pre-commit on all files (initial check)
echo -e "\n${YELLOW}Running initial pre-commit checks...${NC}"
pre-commit run --all-files || echo -e "${YELLOW}! Some pre-commit checks failed (expected on first run)${NC}"

# Create necessary directories
echo -e "\n${YELLOW}Creating project directories...${NC}"
mkdir -p data/input data/output models .coverage_html
echo -e "${GREEN}✓ Directories created${NC}"

# Run quick test
echo -e "\n${YELLOW}Running quick validation...${NC}"
python scripts/quick_test.py
QUICK_TEST_STATUS=$?

echo -e "\n======================================================"
if [ $QUICK_TEST_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Development environment setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Activate virtual environment: source .venv/bin/activate"
    echo "  2. Run tests: make test"
    echo "  3. Run linters: make lint"
    echo "  4. Start developing!"
else
    echo -e "${YELLOW}⚠️  Setup complete but quick tests had issues${NC}"
    echo "Check errors above and verify installation."
fi
echo "======================================================"
