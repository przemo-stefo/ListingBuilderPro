#!/usr/bin/env python3
"""
Quick test script for local Amazon Listing Builder setup
Tests imports and basic functionality
"""

import sys
import os

print("=" * 60)
print("🧪 TESTING AMAZON LISTING BUILDER LOCAL SETUP")
print("=" * 60)

# Test 1: Core imports
print("\n[1/5] Testing core imports...")
try:
    import gradio as gr
    import pandas as pd
    import openpyxl
    print("✅ Core packages: OK")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test 2: Listing optimizer
print("\n[2/5] Testing listing optimizer...")
try:
    from listing_optimizer import optimize_listing
    print("✅ Listing optimizer: OK")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test 3: AI Assistant
print("\n[3/5] Testing AI assistant...")
try:
    from ai_assistant import get_welcome_message
    print("✅ AI assistant: OK")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test 4: Excel generator
print("\n[4/5] Testing Excel generator...")
try:
    from beautiful_excel_generator import create_beautiful_analysis_excel
    print("✅ Excel generator: OK")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test 5: Gradio app
print("\n[5/5] Testing Gradio app structure...")
try:
    import gradio_app_pro
    print("✅ Gradio app: OK")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\n🚀 To run the app locally:")
print("   cd " + os.getcwd())
print("   ./venv/bin/python3 gradio_app_pro.py")
print("\n📝 To use CLI mode:")
print("   ./venv/bin/python3 cli.py [options]")
print("\n" + "=" * 60)
