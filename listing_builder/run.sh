#!/bin/bash
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/run.sh
# Purpose: Production launcher for Amazon Listing Builder
# NOT for: Development or testing

# WHY: Simple launcher script for production use
# WHY: Handles errors and provides clear feedback

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "  🚀 Amazon Listing Builder - Production Mode"
echo "=================================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ ERROR: python3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION"

# Check if we're in the right directory
if [ ! -f "cli.py" ]; then
    echo -e "${RED}❌ ERROR: Must run from listing_builder directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo -e "${GREEN}✓${NC} Directory: $(pwd)"
echo ""

# Check arguments
if [ $# -lt 3 ]; then
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./run.sh <csv_path> <brand> <product_line> [mode] [options...]"
    echo ""
    echo -e "${YELLOW}Basic Example:${NC}"
    echo "  ./run.sh data.csv \"HAG EXPRESS\" \"Cutting Board\" aggressive"
    echo ""
    echo -e "${YELLOW}With Enhancements:${NC}"
    echo "  ./run.sh data.csv \"Brand\" \"Product\" aggressive \\"
    echo "    --cerebro competitors.csv \\"
    echo "    --magnet variations.csv \\"
    echo "    --min-volume 100"
    echo ""
    echo -e "${YELLOW}Modes:${NC}"
    echo "  aggressive  - 96-98% coverage, 7-9 EXACT phrases (default)"
    echo "  standard    - 82-85% coverage, 3-4 EXACT phrases"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --cerebro CSV       - Helium 10 Cerebro CSV (competitor gap analysis)"
    echo "  --magnet CSV        - Helium 10 Magnet CSV (keyword variations)"
    echo "  --additional CSV... - Additional Data Dive CSVs to merge"
    echo "  --min-volume N      - Minimum search volume filter"
    echo "  --merge-strategy    - union or intersection (for multiple Data Dive files)"
    echo "  --output FILE       - Custom output file path"
    echo ""
    echo "Run './run.sh --help' for full documentation"
    exit 1
fi

# WHY: Pass all arguments to Python CLI (argparse handles them)
CSV_PATH="$1"
BRAND="$2"
PRODUCT_LINE="$3"
shift 3  # WHY: Remove first 3 args, keep remaining for optional flags

# Check if CSV exists
if [ ! -f "$CSV_PATH" ]; then
    echo -e "${RED}❌ ERROR: CSV file not found: $CSV_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} CSV file: $CSV_PATH"
echo -e "${GREEN}✓${NC} Brand: $BRAND"
echo -e "${GREEN}✓${NC} Product: $PRODUCT_LINE"
echo ""

# Run the optimizer
echo "=================================================="
echo "  Starting optimization..."
echo "=================================================="
echo ""

# WHY: Pass all remaining arguments to Python CLI
python3 cli.py "$CSV_PATH" "$BRAND" "$PRODUCT_LINE" "$@"

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo -e "${GREEN}  ✅ SUCCESS! Listing optimized${NC}"
    echo "=================================================="
    echo ""
    echo "Output file: optimized_listing_${BRAND// /_}.txt"
    echo ""
    echo "Next steps:"
    echo "  1. Review the generated listing"
    echo "  2. Copy-paste to Amazon Seller Central"
    echo "  3. Profit! 🎉"
else
    echo ""
    echo "=================================================="
    echo -e "${RED}  ❌ ERROR: Optimization failed${NC}"
    echo "=================================================="
    exit 1
fi
