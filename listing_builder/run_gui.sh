#!/bin/bash
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/run_gui.sh
# Purpose: Launch Gradio web GUI for Amazon Listing Builder
# NOT for: Command-line usage (use run.sh for that)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================"
echo -e "  ${BLUE}🚀 Amazon Listing Builder v2.0 - Professional Edition${NC}"
echo "======================================================================"
echo ""

# Check Python version - prefer 3.12 for compatibility
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}❌ ERROR: python3 not found${NC}"
    echo "Please install Python 3.10-3.13"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION (using $PYTHON_CMD)"

# Check if we're in the right directory
if [ ! -f "gradio_app_pro.py" ]; then
    echo -e "${RED}❌ ERROR: Must run from listing_builder directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo -e "${GREEN}✓${NC} Directory: $(pwd)"
echo ""

# Check if gradio is installed
if ! $PYTHON_CMD -c "import gradio" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Gradio not installed. Installing...${NC}"
    echo ""
    echo "Note: Using --break-system-packages flag (safe for this use case)"
    $PYTHON_CMD -m pip install gradio --break-system-packages
    echo ""
fi

echo -e "${GREEN}✓${NC} Gradio installed"
echo ""

# Launch GUI
echo "=================================================="
echo -e "  ${BLUE}Starting Web Interface...${NC}"
echo "=================================================="
echo ""
echo -e "${YELLOW}The GUI will open in your browser automatically.${NC}"
echo -e "${YELLOW}If not, navigate to: http://127.0.0.1:7860${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

$PYTHON_CMD gradio_app_pro.py
