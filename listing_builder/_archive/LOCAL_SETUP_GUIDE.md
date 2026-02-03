# 🏠 Local Setup Guide - Amazon Listing Builder Pro

**Updated:** 2025-11-20
**Status:** ✅ Fully Configured & Tested

---

## ✅ Setup Complete!

Your local environment is **ready to use**. Everything is installed and tested.

---

## 🚀 Quick Start (3 Ways to Run)

### Option 1: Web Interface (Recommended)

```bash
cd /Users/shawn/💼_BIZNES/Amazon/🎯_LISTING_BUILDER_MASTER/01_LISTING_BUILDER_PRO/listing_builder/

./run_local.sh
```

Then open: **http://127.0.0.1:7860**

### Option 2: Direct Python

```bash
cd /Users/shawn/💼_BIZNES/Amazon/🎯_LISTING_BUILDER_MASTER/01_LISTING_BUILDER_PRO/listing_builder/

./venv/bin/python3 gradio_app_pro.py
```

### Option 3: CLI Mode

```bash
cd /Users/shawn/💼_BIZNES/Amazon/🎯_LISTING_BUILDER_MASTER/01_LISTING_BUILDER_PRO/listing_builder/

./venv/bin/python3 cli.py \
  --csv "/path/to/datadive.csv" \
  --brand "YOUR BRAND" \
  --product "Product Line" \
  --mode aggressive
```

---

## 📦 What's Installed

**Python Version:** 3.13.7
**Virtual Environment:** `/venv/` (activated automatically by scripts)

**Core Packages:**
- ✅ gradio==5.49.1 (Web interface)
- ✅ pandas==2.3.3 (Data processing)
- ✅ openpyxl==3.1.5 (Excel export)
- ✅ fastapi==0.121.3 (API framework)
- ✅ pydantic==2.11.10 (Data validation)
- ✅ pillow (Image processing)
- ✅ httpx (HTTP client)

**Full list:** See `requirements_full.txt`

---

## 🧪 Testing Your Setup

Run the test script to verify everything works:

```bash
cd /Users/shawn/💼_BIZNES/Amazon/🎯_LISTING_BUILDER_MASTER/01_LISTING_BUILDER_PRO/listing_builder/

./venv/bin/python3 test_local.py
```

**Expected output:**
```
✅ Core packages: OK
✅ Listing optimizer: OK
✅ AI assistant: OK
✅ Excel generator: OK
✅ Gradio app: OK
```

---

## 📁 File Structure

```
listing_builder/
├── venv/                          ✅ Virtual environment (Python 3.13)
├── gradio_app_pro.py              🎨 Main web interface
├── listing_optimizer.py           🔧 Core optimizer
├── ai_assistant.py                🤖 AI chat assistant
├── beautiful_excel_generator.py   📊 Excel export
├── requirements_full.txt          📦 All dependencies
├── run_local.sh                   🚀 Quick launcher
├── test_local.py                  🧪 Test script
└── LOCAL_SETUP_GUIDE.md           📖 This file
```

---

## 🌐 Live vs Local

**Live Production:**
- URL: https://social.amzniche.online
- Server: Mikrus VPS (izabela166.mikrus.xyz)
- Process: PM2 (process ID: 14)
- Uptime: 24/7

**Local Development:**
- URL: http://127.0.0.1:7860
- Server: Your Mac
- Process: Manual start/stop
- Uptime: When you run it

**Use local when:**
- Testing new features
- Debugging issues
- Working offline
- Privacy-sensitive data

**Use live when:**
- Production work
- Sharing with team
- Need 24/7 access
- Working remotely

---

## 🔧 Troubleshooting

### Problem: "venv not found"

```bash
python3.13 -m venv venv
./venv/bin/pip install -r requirements_full.txt
```

### Problem: "Module not found"

```bash
./venv/bin/pip install -r requirements_full.txt --force-reinstall
```

### Problem: "Port 7860 already in use"

Kill existing process:
```bash
lsof -ti:7860 | xargs kill -9
```

Or use different port:
```bash
./venv/bin/python3 gradio_app_pro.py --server-port 7861
```

### Problem: "Permission denied"

```bash
chmod +x run_local.sh
chmod +x test_local.py
```

---

## 📚 Documentation

**Main docs:**
- `PRODUCTION_README.md` - Full production guide
- `README.md` - General overview
- `GUI_SHOWCASE.md` - UI documentation

**Master folder:**
- `/Users/shawn/💼_BIZNES/Amazon/🎯_LISTING_BUILDER_MASTER/README.md`

---

## 🔄 Updating Dependencies

If you need to update packages:

```bash
cd /Users/shawn/💼_BIZNES/Amazon/🎯_LISTING_BUILDER_MASTER/01_LISTING_BUILDER_PRO/listing_builder/

./venv/bin/pip install --upgrade gradio pandas openpyxl
```

**IMPORTANT:** Test after updating:
```bash
./venv/bin/python3 test_local.py
```

---

## ⚙️ Environment Variables (Optional)

For AI features (chat assistant), create `.env` file:

```bash
# Optional: For AI Assistant features
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

**Note:** Core listing optimization works WITHOUT API keys.
AI chat assistant requires API keys.

---

## 🎯 Next Steps

1. **Test the setup:**
   ```bash
   ./venv/bin/python3 test_local.py
   ```

2. **Run the app:**
   ```bash
   ./run_local.sh
   ```

3. **Open browser:**
   http://127.0.0.1:7860

4. **Upload Data Dive CSV and optimize!**

---

## 📞 Support

**If something doesn't work:**
1. Run test script: `./venv/bin/python3 test_local.py`
2. Check error message
3. See troubleshooting section above
4. Compare with live version: https://social.amzniche.online

**Live app works = your reference point!**

---

## ✅ Setup Summary

- ✅ Python 3.13.7 installed
- ✅ Virtual environment created
- ✅ All dependencies installed (50+ packages)
- ✅ Imports tested & working
- ✅ Run scripts created
- ✅ Documentation complete

**You're ready to go!** 🚀

---

**Last Updated:** 2025-11-20
**Maintained by:** Claude Code + Shawn
**Status:** ✅ Production Ready
