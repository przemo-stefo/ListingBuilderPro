# 🎨 GUI Instructions - Amazon Listing Builder

**Web-based GUI for easy testing and usage!**

---

## 🚀 Quick Start

### Option 1: Auto-Install & Launch (Recommended)
```bash
./run_gui.sh
```

The launcher will:
- Check Python version
- Install Gradio automatically (if needed)
- Launch the web interface
- Open your browser automatically

---

### Option 2: Manual Installation (If Auto-Install Fails)

**If you have Python 3.14 (too new for current Gradio):**

```bash
# Create a virtual environment with Python 3.10-3.13
python3.12 -m venv venv
source venv/bin/activate
pip install gradio
python3 gradio_app.py
```

**If you have Python 3.10-3.13:**

```bash
# Install Gradio
pip3 install gradio --break-system-packages

# Launch GUI
python3 gradio_app.py
```

---

## 📋 GUI Interface

### Required Fields:
1. **Data Dive CSV** - Upload your Helium 10 Data Dive export
2. **Brand Name** - Your brand (e.g., "HAG EXPRESS")
3. **Product Line** - Your product (e.g., "Bamboo Cutting Board Set")
4. **Mode** - Aggressive or Standard

### Optional Enhancements:
5. **Cerebro CSV** - Competitor gap analysis
6. **Magnet CSV** - Keyword variations
7. **Additional Data Dive CSVs** - Multi-file merging
8. **Min Search Volume** - Filter low-volume keywords
9. **Merge Strategy** - Union or Intersection

### Output:
- View optimized listing in browser
- Download `.txt` file with complete listing
- See stats (coverage %, EXACT matches, etc.)

---

## 🌐 Accessing the GUI

After running `./run_gui.sh`, the GUI will be available at:

**URL:** http://127.0.0.1:7860

If browser doesn't open automatically, navigate to this URL manually.

---

## 📸 GUI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Amazon Listing Builder v2.0                             │
├─────────────────────┬───────────────────────────────────────┤
│                     │                                       │
│  📁 REQUIRED        │  📊 RESULTS                           │
│                     │                                       │
│  [Data Dive CSV]    │  ┌─────────────────────────────────┐ │
│  [Brand Name]       │  │ Optimized Listing Output        │ │
│  [Product Line]     │  │                                 │ │
│  [Mode: Aggressive] │  │ Your listing will appear here   │ │
│                     │  │                                 │ │
│  ✨ OPTIONAL        │  │ • Title                         │ │
│                     │  │ • Bullets                       │ │
│  [Cerebro CSV]      │  │ • Description                   │ │
│  [Magnet CSV]       │  │ • Backend                       │ │
│  [Additional CSVs]  │  │ • Statistics                    │ │
│  [Min Volume: 0]    │  │                                 │ │
│  [Merge: Union]     │  └─────────────────────────────────┘ │
│                     │                                       │
│  [🚀 Generate]      │  [Download Listing File]             │
│                     │                                       │
└─────────────────────┴───────────────────────────────────────┘
```

---

## 🎯 Usage Examples

### Example 1: Basic (Data Dive Only)
1. Upload Data Dive CSV
2. Enter "HAG EXPRESS" as brand
3. Enter "Bamboo Cutting Board Set" as product
4. Select "Aggressive" mode
5. Click "🚀 Generate Optimized Listing"
6. View results and download file

---

### Example 2: With Competitor Analysis
1. Upload Data Dive CSV
2. Upload Cerebro CSV (3-5 competitor ASINs)
3. Enter brand and product
4. Click "Generate"
5. System will show:
   - Competitive overlap %
   - Gap keywords found
   - Gap keywords added to listing

---

### Example 3: Full Feature Stack
1. Upload Data Dive CSV
2. Upload Cerebro CSV
3. Upload Magnet CSV
4. Upload 1-2 additional Data Dive CSVs
5. Set "Min Search Volume" to 100
6. Select "Union" merge strategy
7. Click "Generate"
8. System applies all enhancements automatically

---

## 💡 Tips

### File Preparation:
- **Data Dive**: Export as "Listing Builder" format from Helium 10
- **Cerebro**: Include top 3-5 competitors (not 10+)
- **Magnet**: Filter by Smart Score ≥50 before exporting
- **Volume**: Use 50-100 for standard, 100+ for aggressive filtering

### Best Practices:
- Test with Data Dive only first (baseline)
- Add Cerebro to find gaps
- Add Magnet for variations
- Use volume filter last (refinement)

### Troubleshooting:
- **CSV error**: Check file format (must be CSV, not XLSX)
- **Missing columns**: Re-export from Helium 10
- **Timeout**: Try with fewer keywords or smaller CSV
- **Output too short**: Check if volume filter is too high

---

## 🛑 Stopping the GUI

Press **Ctrl+C** in the terminal to stop the web server.

---

## 🔧 Advanced: Custom Port

If port 7860 is in use, edit `gradio_app.py` line 348:

```python
app.launch(
    server_name="127.0.0.1",
    server_port=7861,  # Change to any available port
    share=False,
    inbrowser=True
)
```

---

## 📚 Documentation

**Full Documentation:**
- `PRODUCTION_README.md` - Production guide
- `V2_ENHANCEMENTS.md` - What's new in v2.0
- `GUI_INSTRUCTIONS.md` - This file

**Command-Line Alternative:**
If you prefer command-line, use:
```bash
./run.sh data.csv "Brand" "Product" aggressive
```

---

## ✅ GUI Features

**Advantages:**
- ✅ Visual file upload (no typing paths)
- ✅ Dropdown selections (no typos)
- ✅ Live output display
- ✅ One-click download
- ✅ No command-line knowledge needed

**When to use CLI instead:**
- Batch processing
- Automation/scripts
- Remote servers
- Preferences for terminal

---

## 🎉 Enjoy the GUI!

The web interface makes it super easy to test different configurations and see results instantly.

**Happy optimizing! 🚀**
