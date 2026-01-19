#!/bin/bash
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/INSTALL.sh
# Purpose: Automated installation script for beta testers
# NOT for: Production deployment - use Docker/Cloud for that

echo "=============================================="
echo "  🚀 Amazon Listing Builder - Beta Setup"
echo "=============================================="
echo ""

# WHY: Check Python version
echo "📋 Sprawdzam Python..."
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "✅ Znaleziono Python 3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✅ Znaleziono Python $PYTHON_VERSION"
else
    echo "❌ Python 3 nie znaleziony!"
    echo "Zainstaluj Python 3.8+ z python.org"
    exit 1
fi

# WHY: Install dependencies
echo ""
echo "📦 Instaluję zależności..."
$PYTHON_CMD -m pip install --break-system-packages gradio pandas openpyxl 2>/dev/null || \
$PYTHON_CMD -m pip install gradio pandas openpyxl

if [ $? -eq 0 ]; then
    echo "✅ Wszystkie pakiety zainstalowane"
else
    echo "⚠️  Niektóre pakiety mogły nie zostać zainstalowane"
    echo "Spróbuj ręcznie: pip3 install gradio pandas openpyxl"
fi

# WHY: Check if knowledge base exists
echo ""
echo "📚 Sprawdzam bazę wiedzy..."
if [ -d "../.knowledge" ]; then
    echo "✅ Baza wiedzy znaleziona ($(find ../.knowledge/transcripts -name '*.md' 2>/dev/null | wc -l | tr -d ' ') transkryptów)"
else
    echo "⚠️  Baza wiedzy nie znaleziona"
    echo "Program będzie działał bez AI Assistant (pozostałe funkcje OK)"
fi

# WHY: Create launch script
echo ""
echo "🔧 Tworzę skrypt uruchomieniowy..."
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "=============================================="
echo "  🚀 Starting Amazon Listing Builder"
echo "=============================================="
echo ""

# Find Python
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Python not found!"
    exit 1
fi

echo "✅ Using: $PYTHON_CMD"
echo "🌐 Opening: http://127.0.0.1:7860"
echo ""
echo "Press Ctrl+C to stop"
echo ""

$PYTHON_CMD gradio_app_pro.py
EOF

chmod +x start.sh

echo "✅ Skrypt uruchomieniowy utworzony: start.sh"

# WHY: Success message
echo ""
echo "=============================================="
echo "  ✅ INSTALACJA ZAKOŃCZONA!"
echo "=============================================="
echo ""
echo "📖 JAK URUCHOMIĆ:"
echo ""
echo "   ./start.sh"
echo ""
echo "   lub:"
echo ""
echo "   python3 gradio_app_pro.py"
echo ""
echo "🌐 GUI otworzy się w przeglądarce: http://127.0.0.1:7860"
echo ""
echo "=============================================="
