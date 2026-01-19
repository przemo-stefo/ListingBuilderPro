#!/bin/bash
# /Users/shawn/💼_BIZNES/Amazon/🎯_LISTING_BUILDER_MASTER/01_LISTING_BUILDER_PRO/listing_builder/run_local.sh
# Purpose: Quick launcher for Amazon Listing Builder Pro (local)
# NOT for: Production deployment (use Mikrus/PM2 for that)

echo "============================================================"
echo "🚀 Amazon Listing Builder Pro - Local Mode"
echo "============================================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3.13 -m venv venv"
    echo "   Then: ./venv/bin/pip install -r requirements_full.txt"
    exit 1
fi

# Activate venv and run
echo "📦 Using virtual environment..."
echo "🌐 Starting Gradio interface..."
echo ""
echo "   Local URL: http://127.0.0.1:7860"
echo "   Network URL: Will be shown below"
echo ""
echo "   Press Ctrl+C to stop"
echo ""
echo "============================================================"
echo ""

./venv/bin/python3 gradio_app_pro.py
