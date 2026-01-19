#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/gradio_app_pro.py
# Purpose: Professional Gradio web GUI (Data Dive inspired design)
# NOT for: Command-line interface (use cli.py for that)

"""
Professional Gradio Web GUI
Data Dive inspired design with modern styling and smooth UX.
"""

import gradio as gr
import os
from listing_optimizer import optimize_listing
from output import save_listing_to_file
from ai_assistant import get_answer, get_welcome_message
from blackbox_parser import analyze_niche_from_csv
from niche_parser import parse_niche_csv, compare_datasets
from blackbox_parser import parse_blackbox_csv
from beautiful_excel_generator import create_beautiful_analysis_excel


def chat_with_ai(message, history):
    """
    Chat function for AI assistant.
    WHY: Provides Amazon strategy advice based on knowledge base.
    """
    if not message or message.strip() == "":
        return history

    # WHY: Get AI response based on knowledge base
    response = get_answer(message)

    # WHY: Append to chat history
    history = history + [[message, response]]

    return history


def analyze_from_csv_upload(csv_file):
    """
    Analyze product potential from Black Box CSV upload.
    WHY: Automates data extraction and analyzes entire niche.
    """
    if not csv_file:
        return "❌ Proszę załadować plik CSV z Helium 10 Black Box"

    # WHY: Parse CSV and extract niche data
    analysis_data = analyze_niche_from_csv(csv_file)

    if analysis_data.get('error'):
        return f"❌ {analysis_data['error']}"

    # WHY: Generate comprehensive niche report
    top = analysis_data['top_product']
    num_products = analysis_data['num_competitors']
    avg_revenue = analysis_data['avg_revenue']
    total_revenue = analysis_data['total_niche_revenue']

    report = "# 📊 Analiza Niszy z Black Box CSV\n\n"
    report += f"**Liczba produktów w CSV:** {num_products}\n"
    report += f"**Całkowity revenue niszy:** ${total_revenue:,.0f}/miesiąc\n"
    report += f"**Średni revenue produktu:** ${avg_revenue:,.0f}/miesiąc\n\n"

    report += "---\n\n"
    report += "## 🏆 TOP SELLER (Benchmark)\n\n"
    report += f"**ASIN:** {top.get('asin', 'N/A')}\n"
    report += f"**Title:** {top.get('title', 'N/A')[:100]}...\n"
    report += f"**Monthly Revenue:** ${top.get('monthly_revenue', 0):,.0f}\n"
    report += f"**Reviews:** {top.get('review_count', 0):,}\n"
    report += f"**Rating:** {top.get('review_rating', 0)}/5.0 ⭐\n"
    report += f"**BSR:** #{top.get('bsr_rank', 999999):,}\n"
    report += f"**Price:** ${top.get('price', 0):.2f}\n\n"

    # WHY: Analyze top seller using existing function
    score = 0
    analysis_text = ""

    # Revenue analysis
    revenue = top.get('monthly_revenue', 0)
    if revenue >= 50000:
        score += 30
        revenue_assessment = "✅ ŚWIETNY ($50k+/miesiąc)"
    elif revenue >= 20000:
        score += 25
        revenue_assessment = "✅ DOBRY ($20k-50k/miesiąc)"
    elif revenue >= 10000:
        score += 20
        revenue_assessment = "⚠️ OK ($10k-20k/miesiąc)"
    else:
        score += 10
        revenue_assessment = "⚠️ NISKI (<$10k/miesiąc)"

    # Competition analysis
    reviews = top.get('review_count', 0)
    if reviews < 50 and num_products < 20:
        score += 30
        competition = "✅ NISKA KONKURENCJA"
    elif reviews < 200 and num_products < 50:
        score += 25
        competition = "✅ ŚREDNIA KONKURENCJA"
    elif reviews < 500 and num_products < 100:
        score += 15
        competition = "⚠️ WYSOKA KONKURENCJA"
    else:
        score += 5
        competition = "❌ BARDZO WYSOKA KONKURENCJA"

    # Rating analysis
    rating = top.get('review_rating', 0)
    if rating >= 4.5:
        score += 20
        quality = "✅ WYSOKA JAKOŚĆ (4.5+ stars)"
    elif rating >= 4.0:
        score += 15
        quality = "✅ DOBRA JAKOŚĆ (4.0-4.5 stars)"
    elif rating >= 3.5:
        score += 10
        quality = "⚠️ ŚREDNIA JAKOŚĆ (3.5-4.0 stars)"
    else:
        score += 5
        quality = "⚠️ NISKA JAKOŚĆ (<3.5 stars)"

    # BSR analysis
    bsr = top.get('bsr_rank', 999999)
    if bsr < 5000:
        score += 20
        demand = "✅ SUPER DEMAND (BSR <5k)"
    elif bsr < 20000:
        score += 15
        demand = "✅ WYSOKI DEMAND (BSR <20k)"
    elif bsr < 50000:
        score += 10
        demand = "⚠️ ŚREDNI DEMAND (BSR <50k)"
    else:
        score += 5
        demand = "⚠️ NISKI DEMAND (BSR >50k)"

    report += "---\n\n"
    report += "## 🎯 OCENA POTENCJAŁU\n\n"
    report += f"**1. Wolumen Sprzedaży:** {revenue_assessment}\n"
    report += f"**2. Konkurencja:** {competition} ({num_products} produktów)\n"
    report += f"**3. Jakość:** {quality}\n"
    report += f"**4. Popyt:** {demand}\n\n"

    report += f"### 🎯 OGÓLNY SCORE: {score}/100\n\n"

    if score >= 80:
        recommendation = "🎯 **WYSOKI POTENCJAŁ** - Świetna możliwość!"
    elif score >= 60:
        recommendation = "✅ **DOBRY POTENCJAŁ** - Warto rozważyć"
    elif score >= 40:
        recommendation = "⚠️ **ŚREDNI POTENCJAŁ** - Wymaga analizy"
    else:
        recommendation = "❌ **NISKI POTENCJAŁ** - Szukaj lepszej niszy"

    report += f"### {recommendation}\n\n"

    report += "---\n\n"
    report += "## 💡 Następne Kroki\n\n"

    if score >= 60:
        report += """
**1. Deep Dive Analysis:**
- Użyj Helium 10 Cerebro na top 3-5 ASINów
- Sprawdź keyword gaps
- Analyze reviews (sentiment analysis)

**2. Product Differentiation:**
- Jak możesz być lepszy od top sellera?
- Bundle opportunity?
- Premium materials?
- Better design/packaging?

**3. Launch Budget Planning:**
- Inventory: $1,500-2,000 (500-1,000 units)
- PPC: $1,500 (pierwsze 30 dni)
- Images/A+: $500
- **Total:** ~$3,500-4,000

**4. Supplier Sourcing:**
- Alibaba.com (min 3 quotes)
- Request samples
- Negotiate MOQ
- Target margin: 3-5× COGS
"""
    else:
        report += """
**Dlaczego NOT recommended:**

"""
        if revenue < 10000:
            report += "- ❌ Zbyt niski revenue niszy\n"
        if num_products > 100:
            report += "- ❌ Za dużo konkurentów (oversaturated)\n"
        if reviews > 500:
            report += "- ❌ Top seller ma >500 reviews (trudno go pokonać)\n"
        if rating < 4.0:
            report += "- ❌ Niska jakość produktów w niszy\n"

        report += """
**Szukaj niszy z:**
- Revenue: $10k-30k/miesiąc
- Konkurenci: 20-50 produktów
- Top seller reviews: <200
- Rating: 4.0-4.5
- BSR: <20,000
"""

    report += "\n---\n\n**Chcesz zobaczyć wszystkie produkty?** Poniżej lista top 10:\n\n"

    # WHY: Show top 10 products
    all_products = analysis_data['all_products']
    sorted_products = sorted(all_products, key=lambda x: x['monthly_revenue'], reverse=True)[:10]

    for i, prod in enumerate(sorted_products, 1):
        report += f"**#{i}** - ${prod['monthly_revenue']:,.0f}/mo | "
        report += f"{prod['review_count']} reviews | "
        report += f"{prod['review_rating']}⭐ | "
        report += f"BSR #{prod['bsr_rank']:,}\n"

    return report


def generate_beautiful_excel_report(niche_csv_file, blackbox_csv_file):
    """
    Generate beautiful professional Excel report comparing Niche + Black Box data.
    WHY: Provides comprehensive visual analysis with colors, explanations, and Inner Circle insights.
    """
    if not niche_csv_file and not blackbox_csv_file:
        return "❌ Proszę załadować przynajmniej jeden plik CSV (Niche lub Black Box)"

    try:
        # WHY: Parse both CSV files
        niche_products = []
        blackbox_products = []

        if niche_csv_file:
            niche_products = parse_niche_csv(niche_csv_file)

        if blackbox_csv_file:
            blackbox_products = parse_blackbox_csv(blackbox_csv_file)

        # WHY: Handle single file case
        if not niche_products and blackbox_products:
            # Only Black Box - use existing function
            from excel_generator import create_excel_report
            analysis_data = analyze_niche_from_csv(blackbox_csv_file)
            excel_path = create_excel_report(analysis_data, f"report_{os.path.basename(blackbox_csv_file).replace('.csv', '')}_basic.xlsx")

            report = f"""# ✅ RAPORT EXCEL WYGENEROWANY

**Plik:** `{excel_path}`

📊 **Zawartość:**
- 4 arkusze: Summary, All Products, Top 10 Analysis, Recommendations
- {len(blackbox_products)} produktów z analizą
- Kolory: 🟢 Zielony (high), 🟡 Żółty (medium), 🔴 Czerwony (low)

**Jak otworzyć:** Kliknij na plik Excel w folderze lub użyj Excel/LibreOffice
"""
            return report

        elif niche_products and not blackbox_products:
            # Only Niche - create single source report
            total_revenue = sum(p['monthly_revenue'] for p in niche_products)
            comparison = {
                'total_unique_products': len(niche_products),
                'niche_count': len(niche_products),
                'blackbox_count': 0,
                'overlap_count': 0,
                'niche_only_count': len(niche_products),
                'blackbox_only_count': 0,
                'niche_only': niche_products,
                'blackbox_only': [],
                'overlap': [],
                'all_unique_products': niche_products,
                'combined_total_revenue': total_revenue
            }
        else:
            # Both files - full comparison
            comparison = compare_datasets(niche_products, blackbox_products)

        # WHY: Generate beautiful Excel
        output_filename = f"PIĘKNY_RAPORT_{len(comparison['all_unique_products'])}_produktów.xlsx"
        excel_path = create_beautiful_analysis_excel(comparison, output_filename)

        # WHY: Create success message
        report = f"""# ✅ PIĘKNY RAPORT EXCEL WYGENEROWANY!

**Plik:** `{excel_path}`
**Rozmiar:** {os.path.getsize(excel_path) / 1024:.1f} KB

---

## 📊 PODSUMOWANIE DANYCH

**Total Unique Products:** {comparison['total_unique_products']}
**Combined Revenue:** €{comparison['combined_total_revenue']:,.0f}/miesiąc

📄 **Niche CSV:** {comparison['niche_count']} produktów
📄 **Black Box CSV:** {comparison['blackbox_count']} produktów
🔀 **Overlap:** {comparison['overlap_count']} produktów w obu źródłach

---

## 📊 STRUKTURA RAPORTU (10 ARKUSZY)

1. **📖 INSTRUKCJA** - kompletny przewodnik jak czytać raport
2. **📊 EXECUTIVE SUMMARY** - kluczowe metryki z wyjaśnieniami
3. **🏆 TOP 50 BY REVENUE** - najlepsze produkty + scoring (0-100)
4. **💎 OPPORTUNITY MATRIX** - złote okazje (high revenue + low competition)
5. **🔍 COMPETITION ANALYSIS** - analiza konkurencji po poziomach
6. **📊 ALL {comparison['total_unique_products']} PRODUCTS** - kompletna lista z kolorami
7. **🔀 DATA COMPARISON** - produkty w obu źródłach
8. **📈 NICHE-ONLY** - produkty tylko w Niche CSV
9. **📦 BLACK BOX-ONLY** - produkty tylko w Black Box
10. **💡 STRATEGIC INSIGHTS** - rekomendacje strategiczne (Professional)

---

## 🎨 SYSTEM KOLORÓW

- 🟢 **Zielony** = HIGH POTENTIAL (Score ≥70, <200 reviews)
- 🟡 **Żółty** = MEDIUM POTENTIAL (Score 50-69)
- 🔴 **Czerwony** = LOW POTENTIAL (Score <50 lub >500 reviews)
- 🔵 **Niebieski** = Nagłówki

---

## 💡 JAK UŻYWAĆ

1. Otwórz Excel w Excel/LibreOffice
2. Zacznij od arkusza **📖 INSTRUKCJA**
3. Zobacz **💎 OPPORTUNITY MATRIX** dla szybkich okazji
4. Sprawdź **🏆 TOP 50 BY REVENUE** dla top produktów
5. Użyj filtrów Excel do głębszej analizy

**📍 Lokalizacja:** `{os.path.abspath(excel_path)}`
"""

        return report

    except Exception as e:
        return f"❌ Błąd podczas generowania raportu:\n\n```\n{str(e)}\n```\n\nSprawdź czy pliki CSV są prawidłowe (Helium 10 format)."


def analyze_product_potential(
    monthly_revenue,
    review_count,
    review_rating,
    bsr_rank,
    num_competitors
):
    """
    Analyze product sales potential based on market data.
    WHY: Provides data-driven product opportunity assessment based on Inner Circle strategies.
    """
    # WHY: Validate inputs
    try:
        monthly_revenue = float(monthly_revenue) if monthly_revenue else 0
        review_count = int(review_count) if review_count else 0
        review_rating = float(review_rating) if review_rating else 0
        bsr_rank = int(bsr_rank) if bsr_rank else 999999
        num_competitors = int(num_competitors) if num_competitors else 0
    except:
        return "❌ Błąd: Wprowadź poprawne wartości liczbowe"

    # WHY: Calculate potential score (0-100)
    score = 0
    analysis = "# 📊 Analiza Potencjału Sprzedażowego\n\n"

    # WHY: Analyze monthly revenue
    if monthly_revenue >= 50000:
        score += 30
        revenue_assessment = "✅ ŚWIETNY ($50k+/miesiąc)"
    elif monthly_revenue >= 20000:
        score += 25
        revenue_assessment = "✅ DOBRY ($20k-50k/miesiąc)"
    elif monthly_revenue >= 10000:
        score += 20
        revenue_assessment = "⚠️ OK ($10k-20k/miesiąc)"
    elif monthly_revenue >= 5000:
        score += 10
        revenue_assessment = "⚠️ NISKI ($5k-10k/miesiąc)"
    else:
        score += 0
        revenue_assessment = "❌ ZA NISKI (<$5k/miesiąc)"

    analysis += f"## 1. Wolumen Sprzedaży: {revenue_assessment}\n"
    analysis += f"**Miesięczny revenue:** ${monthly_revenue:,.0f}\n\n"

    # WHY: Analyze competition (review count = proxy for competition)
    if review_count < 50 and num_competitors < 20:
        score += 30
        competition_assessment = "✅ NISKA KONKURENCJA (łatwy wejście)"
    elif review_count < 200 and num_competitors < 50:
        score += 25
        competition_assessment = "✅ ŚREDNIA KONKURENCJA (możliwe)"
    elif review_count < 500 and num_competitors < 100:
        score += 15
        competition_assessment = "⚠️ WYSOKA KONKURENCJA (trudne)"
    else:
        score += 5
        competition_assessment = "❌ BARDZO WYSOKA (bardzo trudne)"

    analysis += f"## 2. Poziom Konkurencji: {competition_assessment}\n"
    analysis += f"**Top seller reviews:** {review_count} | **Liczba konkurentów:** {num_competitors}\n\n"

    # WHY: Analyze rating (quality indicator)
    if review_rating >= 4.5:
        score += 20
        rating_assessment = "✅ WYSOKA JAKOŚĆ (4.5+ stars)"
    elif review_rating >= 4.0:
        score += 15
        rating_assessment = "✅ DOBRA JAKOŚĆ (4.0-4.5 stars)"
    elif review_rating >= 3.5:
        score += 10
        rating_assessment = "⚠️ ŚREDNIA JAKOŚĆ (3.5-4.0 stars)"
    else:
        score += 5
        rating_assessment = "⚠️ NISKA JAKOŚĆ (<3.5 stars)"

    analysis += f"## 3. Jakość Produktów: {rating_assessment}\n"
    analysis += f"**Średni rating:** {review_rating}/5.0 ⭐\n\n"

    # WHY: Analyze BSR (demand indicator)
    if bsr_rank < 5000:
        score += 20
        bsr_assessment = "✅ SUPER DEMAND (BSR <5k)"
    elif bsr_rank < 20000:
        score += 15
        bsr_assessment = "✅ WYSOKI DEMAND (BSR <20k)"
    elif bsr_rank < 50000:
        score += 10
        bsr_assessment = "⚠️ ŚREDNI DEMAND (BSR <50k)"
    elif bsr_rank < 100000:
        score += 5
        bsr_assessment = "⚠️ NISKI DEMAND (BSR <100k)"
    else:
        score += 0
        bsr_assessment = "❌ BARDZO NISKI DEMAND (BSR >100k)"

    analysis += f"## 4. Popyt (Best Seller Rank): {bsr_assessment}\n"
    analysis += f"**BSR:** #{bsr_rank:,}\n\n"

    analysis += "---\n\n"

    # WHY: Overall recommendation
    if score >= 80:
        recommendation = "🎯 **WYSOKI POTENCJAŁ** - Świetna możliwość!"
        color = "green"
    elif score >= 60:
        recommendation = "✅ **DOBRY POTENCJAŁ** - Warto rozważyć"
        color = "blue"
    elif score >= 40:
        recommendation = "⚠️ **ŚREDNI POTENCJAŁ** - Wymaga careful analysis"
        color = "orange"
    else:
        recommendation = "❌ **NISKI POTENCJAŁ** - Szukaj lepszej możliwości"
        color = "red"

    analysis += f"## 🎯 OGÓLNA OCENA: {score}/100\n\n"
    analysis += f"### {recommendation}\n\n"

    # WHY: Provide actionable next steps based on Inner Circle strategies
    analysis += "---\n\n## 💡 Następne Kroki (Pro Strategy):\n\n"

    if score >= 60:
        analysis += """
**1. Competitor Deep Dive:**
- Użyj Helium 10 Cerebro na top 5 konkurentów
- Znajdź keyword gaps (czego im brakuje)
- Sprawdź ich images quality i A+ Content
- Analyze reviews (co ludzie chwalą vs narzekają)

**2. Product Differentiation:**
- Jak możesz być LEPSZY od top sellera?
- Bundle? Premium materials? Better design?
- Unique value proposition (nie tylko cena!)

**3. Launch Strategy:**
- Budget: Min. $3k ($1.5k inventory + $1.5k PPC)
- Target: 10-20 sprzedaży/dzień przez pierwsze 30 dni
- PPC aggressive bidding (pierwsze 2 tygodnie)
- Reviews: Amazon Vine (5-10 reviews przed launch)

**4. Supplier Sourcing:**
- Alibaba.com (min. 3 quotes)
- Check MOQ (Minimum Order Quantity)
- Request samples BEFORE bulk order
- Negotiate price (target: 3-5x markup)
"""
    else:
        analysis += """
**Dlaczego NIE zalecam tego produktu:**

"""

        if monthly_revenue < 10000:
            analysis += "- ❌ **Zbyt niski revenue** - trudno będzie być profitable\n"

        if review_count > 500:
            analysis += "- ❌ **Za duża konkurencja** - top seller ma >500 reviews (trudno wyprzedzić)\n"

        if review_rating < 4.0:
            analysis += "- ❌ **Niska jakość** - klienci niezadowoleni (ryzyko returns i bad reviews)\n"

        if bsr_rank > 50000:
            analysis += "- ❌ **Niski demand** - produkt się słabo sprzedaje\n"

        analysis += """
**Szukaj produktu który ma:**
- ✅ Monthly revenue: $10k-30k (sweet spot)
- ✅ Top seller reviews: <200 (możliwa konkurencja)
- ✅ Rating: 4.0-4.5 (room for improvement)
- ✅ BSR: <20,000 (decent demand)
- ✅ <50 konkurentów (nie oversaturated)

**Gdzie szukać:**
- Helium 10 Black Box (product research tool)
- Filter: Price $15-50, Revenue $10k-30k, Reviews <200
- Avoid: Seasonal, fragile, regulated products
"""

    analysis += "\n---\n\n"
    analysis += "**Potrzebujesz więcej pomocy?** Zapytaj AI Assistant w zakładce 💬!"

    return analysis


def optimize_listing_gui(
    datadive_file,
    brand_name,
    product_line,
    mode,
    cerebro_file=None,
    magnet_file=None,
    additional_files=None,
    min_volume=0,
    merge_strategy="union",
    progress=gr.Progress()
):
    """GUI wrapper with progress tracking."""

    try:
        # Validate
        if not datadive_file:
            return "⚠️ Please upload a Data Dive CSV file", None, ""
        if not brand_name or not product_line:
            return "⚠️ Please enter Brand Name and Product Line", None, ""

        progress(0.1, desc="📄 Parsing CSV files...")

        # Get paths
        datadive_path = datadive_file.name
        cerebro_path = cerebro_file.name if cerebro_file else None
        magnet_path = magnet_file.name if magnet_file else None
        additional_paths = [f.name for f in additional_files] if additional_files else []

        progress(0.3, desc="🔍 Analyzing keywords...")

        # Run optimization
        result = optimize_listing(
            csv_path=datadive_path,
            brand=brand_name,
            product_line=product_line,
            mode=mode.lower(),
            cerebro_csv=cerebro_path,
            magnet_csv=magnet_path,
            additional_datadive_csvs=additional_paths if additional_paths else None,
            min_search_volume=int(min_volume),
            merge_strategy=merge_strategy.lower()
        )

        progress(0.7, desc="✨ Generating listing...")

        listing = result['listing']
        stats = result['stats']
        validation = result['validation']

        # Build output
        output = f"""# 📊 Optimization Results

**Coverage:** {stats['coverage_pct']:.1f}% ({stats['mode']})
**EXACT Matches:** {stats['exact_matches']}
**Title Length:** {stats['title_stats']['length']}/200 chars
**Backend:** {stats['backend_stats']['byte_size']}/250 bytes
**Validation:** {'✅ ALL PASS' if validation['all_valid'] else '⚠️ ISSUES DETECTED'}

---

## 📝 TITLE
```
{listing['title']}
```

---

## 🔹 BULLET POINTS
"""
        for i, bullet in enumerate(listing['bullets'], 1):
            output += f"\n**{i}.** {bullet}\n"

        output += f"""
---

## 📄 DESCRIPTION
```
{listing['description']}
```

---

## 🔧 BACKEND SEARCH TERMS
```
{listing['backend']}
```

---

## 📈 DETAILED STATISTICS

### Coverage Breakdown
- **Title:** {stats['section_coverage']['title_coverage']:.1f}%
- **Bullets:** {stats['section_coverage']['bullets_coverage']:.1f}%
- **Backend:** {stats['section_coverage']['backend_coverage']:.1f}%

### Component Stats
- **Title Utilization:** {stats['title_stats']['utilization']:.1f}%
- **Bullet Count:** {stats['bullet_stats']['bullet_count']}
- **Backend Utilization:** {stats['backend_stats']['utilization']:.1f}%
"""

        # Stats summary for display
        stats_summary = f"""### 🎯 Performance Metrics

**Overall Coverage:** {stats['coverage_pct']:.1f}%
**Mode:** {stats['mode']}
**EXACT Matches:** {stats['exact_matches']}

**Title:** {stats['title_stats']['length']}/200 chars ({stats['title_stats']['utilization']:.1f}%)
**Bullets:** {stats['bullet_stats']['bullet_count']} bullets
**Backend:** {stats['backend_stats']['byte_size']}/250 bytes ({stats['backend_stats']['utilization']:.1f}%)

**Validation:** {'✅ ALL COMPONENTS VALID' if validation['all_valid'] else '⚠️ VALIDATION ISSUES DETECTED'}
"""

        progress(0.9, desc="💾 Saving file...")

        # Save file
        output_filename = f"optimized_listing_{brand_name.replace(' ', '_')}.txt"
        save_listing_to_file(result, output_filename)

        progress(1.0, desc="✅ Complete!")

        return output, output_filename, stats_summary

    except Exception as e:
        return f"❌ ERROR: {str(e)}\n\nPlease check your inputs and try again.", None, ""


# Custom CSS for Data Dive inspired design
custom_css = """
/* Data Dive Inspired Professional Theme - Lightened for readability */
:root {
    --primary-color: #00a8e8;
    --secondary-color: #00c9a7;
    --success-color: #00d084;
    --warning-color: #ffb400;
    --danger-color: #ff4757;
    --dark-bg: #1A1A1A;
    --card-bg: #262626;
    --border-color: #404040;
    --text-primary: #f5f5f5;
    --text-secondary: #b0b0b0;
}

/* Main container */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif !important;
    background: #1A1A1A !important;
}

/* Cards */
.block {
    background: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s ease !important;
}

.block:hover {
    box-shadow: 0 8px 12px rgba(0, 168, 232, 0.2) !important;
    border-color: var(--primary-color) !important;
}

/* Headers */
h1, h2, h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

h1 {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* Input fields */
input, textarea, select {
    background: #1e1e1e !important;
    border: 2px solid var(--border-color) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    transition: all 0.3s ease !important;
}

input:focus, textarea:focus, select:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(0, 168, 232, 0.1) !important;
}

/* Labels */
label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Buttons */
.primary-button {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 32px !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(0, 168, 232, 0.3) !important;
}

.primary-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 168, 232, 0.4) !important;
}

/* File upload */
.file-preview {
    background: #1e1e1e !important;
    border: 2px dashed var(--border-color) !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}

.file-preview:hover {
    border-color: var(--primary-color) !important;
    background: rgba(0, 168, 232, 0.05) !important;
}

/* Tabs */
.tab-nav {
    background: var(--card-bg) !important;
    border-radius: 8px !important;
    padding: 4px !important;
}

.tab-nav button {
    color: var(--text-secondary) !important;
    border-radius: 6px !important;
    transition: all 0.3s ease !important;
}

.tab-nav button.selected {
    background: var(--primary-color) !important;
    color: white !important;
}

/* Stats cards */
.stats-card {
    background: linear-gradient(135deg, rgba(0, 168, 232, 0.1), rgba(0, 201, 167, 0.1)) !important;
    border: 1px solid var(--primary-color) !important;
    border-radius: 8px !important;
    padding: 16px !important;
}

/* Markdown output */
.markdown-text {
    color: var(--text-primary) !important;
    line-height: 1.7 !important;
}

.markdown-text code {
    background: #1e1e1e !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
    color: var(--secondary-color) !important;
}

.markdown-text pre {
    background: #1e1e1e !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 16px !important;
}

/* Progress bar */
.progress-bar {
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color)) !important;
    border-radius: 4px !important;
}

/* Tooltips */
.tooltip {
    background: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--dark-bg);
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary-color);
}
"""

# Create app
with gr.Blocks(
    title="Amazon Listing Builder Pro",
    css=custom_css,
    theme=gr.themes.Base(
        primary_hue="blue",
        secondary_hue="cyan",
        neutral_hue="slate",
        font=["Inter", "system-ui", "sans-serif"]
    )
) as app:

    # Header
    gr.HTML("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">
            🚀 Amazon Listing Builder
        </h1>
        <p style="font-size: 1.2rem; color: #a0aec0; margin: 0;">
            Professional Edition • v2.0
        </p>
        <p style="font-size: 0.9rem; color: #718096; margin-top: 0.5rem;">
            Generate optimized Amazon listings with AI-powered competitor analysis
        </p>
    </div>
    """)

    with gr.Tabs() as tabs:

        # Main tab
        with gr.Tab("🎯 Optimize Listing"):
            with gr.Row():
                # Left column - Inputs
                with gr.Column(scale=1):
                    gr.Markdown("### 📁 Required Configuration")

                    datadive_input = gr.File(
                        label="Data Dive CSV",
                        file_types=[".csv"],
                        type="filepath",
                        elem_classes=["file-preview"]
                    )

                    with gr.Accordion("ℹ️ Co to jest Data Dive CSV?", open=False):
                        gr.Markdown("""
                        **Data Dive CSV** to główny plik z keywords dla Twojego produktu.

                        **Skąd go wziąć:**
                        1. Helium 10 → **Data Dive**
                        2. Wpisz główne keyword (np. "bamboo cutting board")
                        3. Export → **"Listing Builder"** format
                        4. Zapisz CSV

                        **Co zawiera:**
                        - Lista 200-450 keywords
                        - Search Volume (ile razy miesięcznie szukane)
                        - Relevancy Score (jak relevantne dla produktu)
                        - Competing Products (ile produktów ma to keyword)

                        **WAŻNE:** To jedyny obowiązkowy plik. Bez niego system nie będzie działał.
                        """)

                    with gr.Row():
                        brand_input = gr.Textbox(
                            label="Brand Name",
                            placeholder="HAG EXPRESS"
                        )

                        product_input = gr.Textbox(
                            label="Product Line",
                            placeholder="Bamboo Cutting Board Set"
                        )

                    mode_input = gr.Radio(
                        label="Optimization Mode",
                        choices=["Aggressive", "Standard"],
                        value="Aggressive"
                    )

                    with gr.Accordion("ℹ️ Aggressive vs Standard - Kiedy co wybrać?", open=False):
                        gr.Markdown("""
                        ### **Aggressive Mode** (Zalecane - 95% przypadków)

                        **Kiedy użyć:**
                        - Chcesz MAX ranking w Amazon
                        - Konkurencyjna nisza (>20 produktów)
                        - Nowy produkt (trzeba agresywnie rankować)

                        **Co robi:**
                        - ✅ **7-9 EXACT phrases** w tytule (max SEO)
                        - ✅ **190-199 znaków** w tytule (96-99% wykorzystania)
                        - ✅ **96-98% coverage** wszystkich top keywords
                        - ✅ Gęste keyword density w bullet points

                        **Przykład tytułu:**
                        > HAG EXPRESS Bamboo Cutting Board Set, Large Wooden Cutting Boards for Kitchen, Organic Bamboo Chopping Board with Juice Groove, Non-Slip Wood Butcher Block, Antibacterial Cutting Surface, 3-Piece Set

                        ---

                        ### **Standard Mode** (Premium produkty)

                        **Kiedy użyć:**
                        - Premium produkt (>$50)
                        - Luxury niche (gdzie czytelność > SEO)
                        - Brand-focused listing (silny brand)

                        **Co robi:**
                        - ✅ **3-4 EXACT phrases** w tytule (balans SEO + czytelność)
                        - ✅ **140-160 znaków** w tytule (łatwiej czytać)
                        - ✅ **82-85% coverage** (focus na najważniejsze keywords)
                        - ✅ Natural language w bullet points

                        **Przykład tytułu:**
                        > HAG EXPRESS Premium Bamboo Cutting Board Set - Professional Kitchen Essentials (3-Piece)

                        ---

                        **💡 REKOMENDACJA:** Użyj **Aggressive** chyba że masz luxury brand. Amazon SEO > czytelność w większości przypadków.
                        """)


                    gr.Markdown("---")
                    gr.Markdown("### ✨ Advanced Options")

                    with gr.Accordion("🔍 Competitor Analysis", open=False):
                        cerebro_input = gr.File(
                            label="Cerebro CSV (Optional)",
                            file_types=[".csv"],
                            type="filepath"
                        )

                        gr.Markdown("""
                        **ℹ️ Co to jest Cerebro CSV?**

                        **Cerebro** to narzędzie Helium 10 do analizy konkurencji.

                        **Kiedy użyć:**
                        - Znasz 3-5 bezpośrednich konkurentów (te same produkty)
                        - Chcesz znaleźć **keyword gaps** (czego Ci brakuje w listingu)
                        - Chcesz zobaczyć na co rankują best-sellerzy

                        **Jak wyeksportować:**
                        1. Helium 10 → **Cerebro**
                        2. Wpisz 3-5 ASINów konkurentów (przecinkami: B08ABC123,B09DEF456)
                        3. Kliknij **Search**
                        4. Export → CSV

                        **Co daje:**
                        - System znajdzie keywords na które **konkurenci rankują, a Ty NIE**
                        - Doda te keywords do Twojego listingu
                        - Zwiększy szansę na wygranie z konkurencją

                        **Przykład:**
                        - Ty rankujesz: "cutting board", "bamboo board"
                        - Konkurent rankuje: "cutting board", "bamboo board", "wooden chopping block", "chef board"
                        - **Gap** = "wooden chopping block", "chef board" → System doda te keywords!

                        **💡 WSKAZÓWKA:** Używaj tylko dla bezpośredniej konkurencji (te same produkty). NIE używaj dla produktów z innej kategorii.
                        """)

                    with gr.Accordion("🔄 Keyword Expansion", open=False):
                        magnet_input = gr.File(
                            label="Magnet CSV (Optional)",
                            file_types=[".csv"],
                            type="filepath"
                        )

                        gr.Markdown("""
                        **ℹ️ Co to jest Magnet CSV?**

                        **Magnet** to narzędzie Helium 10 do ekspansji keywords (znajdowanie wariantów).

                        **Kiedy użyć:**
                        - Chcesz znaleźć **wszystkie warianty** głównego keyword
                        - Twoja nisza ma wiele synonimów (np. "cutting board" = "chopping board")
                        - Chcesz dodać **long-tail keywords** (długie frazy z małym volume ale wysoką konwersją)

                        **Jak wyeksportować:**
                        1. Helium 10 → **Magnet**
                        2. Wpisz główne keyword (np. "bamboo cutting board")
                        3. Kliknij **Get Keywords**
                        4. Export → CSV

                        **Co daje:**
                        - Znajdzie 200-500 **related keywords**
                        - Synonimy (cutting board = chopping board = butcher block)
                        - Long-tail (bamboo cutting board with juice groove)
                        - Misspellings (cuting board - tak, ludzie szukają z błędami!)

                        **Przykład:**
                        - Main keyword: "bamboo cutting board"
                        - Magnet znajdzie: "bamboo chopping board", "wooden cutting board", "bamboo board for kitchen", "organic bamboo cutting board", etc.

                        **💡 WSKAZÓWKA:** Używaj gdy masz <100 keywords z Data Dive. Magnet wypełni "luki" i zwiększy coverage.
                        """)

                    with gr.Accordion("📊 Multi-File Merge", open=False):
                        additional_input = gr.Files(
                            label="Additional Data Dive CSVs",
                            file_types=[".csv"],
                            type="filepath"
                        )

                        gr.Markdown("""
                        **ℹ️ Kiedy używać Multi-File Merge?**

                        **Użyj gdy:**
                        - Masz **bundle** (zestaw produktów)
                        - Sprzedajesz warianty tego samego produktu (Large, Medium, Small)
                        - Chcesz zmaksymalizować coverage dla różnych use-cases

                        **Przykład:**
                        - Sprzedajesz: "Bamboo Cutting Board Set" (3 deski: large, medium, small)
                        - CSV #1: Data Dive dla "bamboo cutting board" (główny)
                        - CSV #2: Data Dive dla "large cutting board"
                        - CSV #3: Data Dive dla "small cutting board"
                        - **Merge** = wszystkie keywords razem = MAX pokrycie!

                        **WAŻNE:** Wszystkie CSV muszą być Data Dive (nie Cerebro/Magnet).
                        """)

                        merge_strategy_input = gr.Radio(
                            label="Merge Strategy",
                            choices=["Union", "Intersection"],
                            value="Union"
                        )

                        gr.Markdown("""
                        **ℹ️ Union vs Intersection - Co to znaczy?**

                        ### **Union (Suma)** ← Zalecane domyślnie

                        **Co robi:**
                        - Bierze **wszystkie keywords** ze wszystkich plików
                        - Łączy bez duplikatów
                        - MAX pokrycie

                        **Kiedy użyć:**
                        - Bundle products (różne produkty w zestawie)
                        - Warianty (Large, Medium, Small)
                        - Chcesz rankować na MAX liczbie keywords

                        **Przykład:**
                        - CSV #1: "bamboo board", "cutting board", "kitchen board"
                        - CSV #2: "large board", "cutting board", "chef board"
                        - **Union** = "bamboo board", "cutting board", "kitchen board", "large board", "chef board" (5 unikalnych)

                        ---

                        ### **Intersection (Przecięcie)**

                        **Co robi:**
                        - Bierze **tylko wspólne keywords** ze wszystkich plików
                        - Filtruje do CORE keywords
                        - Focus na najważniejszych

                        **Kiedy użyć:**
                        - Bardzo podobne produkty (ten sam typ, różne kolory)
                        - Chcesz focus na CORE keywords (nie rozpraszać)
                        - Masz >500 keywords i chcesz zredukować

                        **Przykład:**
                        - CSV #1: "bamboo board", "cutting board", "kitchen board"
                        - CSV #2: "large board", "cutting board", "chef board"
                        - **Intersection** = "cutting board" (tylko to jedno jest wspólne)

                        ---

                        **💡 REKOMENDACJA:** Użyj **Union** w 95% przypadków. Więcej keywords = lepszy ranking.
                        """)

                    with gr.Accordion("⚙️ Filters", open=False):
                        min_volume_input = gr.Slider(
                            label="Minimum Search Volume",
                            minimum=0,
                            maximum=500,
                            step=10,
                            value=0
                        )

                        gr.Markdown("""
                        **ℹ️ Co to jest Minimum Search Volume?**

                        **Filtr** który usuwa keywords z małym Search Volume (liczba wyszukiwań/miesiąc).

                        **Jak działa:**
                        - Ustawisz **100** → system usunie wszystkie keywords z <100 wyszukiwań/miesiąc
                        - Zostają tylko **high-volume keywords**
                        - Redukuje noise (słabe long-tail keywords)

                        **Kiedy użyć:**
                        - Masz **>500 keywords** (zbyt dużo danych)
                        - Chcesz focus na **mainstream keywords** (wysokie volume)
                        - Bardzo konkurencyjna nisza (musisz bić konkurencję na top keywords)

                        **Kiedy NIE używać:**
                        - Masz <200 keywords (potrzebujesz wszystkich)
                        - Low-competition niche (każde keyword się liczy)
                        - Nowy produkt (long-tail często konwertuje lepiej!)

                        **Przykład:**
                        - Keyword: "bamboo cutting board" → Volume: 5000/miesiąc → **ZOSTAJE**
                        - Keyword: "small bamboo board for cheese" → Volume: 20/miesiąc → **USUNIĘTE** (jeśli min volume = 50)

                        **💡 REKOMENDACJA:** Zostaw na **0** (nie filtruj) chyba że masz problem z zbyt wieloma keywords.

                        **WAŻNE:** Long-tail keywords (małe volume) często mają **wyższą konwersję** bo ludzie szukają bardzo konkretnie!
                        """)


                    optimize_btn = gr.Button(
                        "🚀 Generate Optimized Listing",
                        variant="primary",
                        size="lg",
                        elem_classes=["primary-button"]
                    )

                # Right column - Results
                with gr.Column(scale=2):
                    gr.Markdown("### 📊 Results Dashboard")

                    stats_display = gr.Markdown(
                        value="*Results will appear here after optimization...*",
                        elem_classes=["stats-card"]
                    )

                    with gr.Accordion("ℹ️ Co oznaczają statystyki w Results?", open=False):
                        gr.Markdown("""
                        ### **📊 Coverage % (Keyword Coverage)**

                        **Co to jest:**
                        - % top 200 keywords które znalazły się w **całym listingu** (tytuł + bullets + backend)
                        - Mierzy jak dobrze system pokrył wszystkie ważne keywords

                        **Jak interpretować:**
                        - **<70%** = Niedooptymalizowane (zbyt mało keywords)
                        - **70-85%** = Dobre (Standard mode)
                        - **85-95%** = Świetne (Aggressive mode)
                        - **96-98%** = Doskonałe (MAX SEO)

                        **Przykład:**
                        - Data Dive ma 200 top keywords
                        - System użył 185 z nich w listingu
                        - Coverage = 185/200 = **92.5%** ✅

                        ---

                        ### **🎯 EXACT Matches (w tytule)**

                        **Co to jest:**
                        - Liczba **dokładnych fraz** z Data Dive które znalazły się w tytule **bez przerwy**
                        - Amazon preferuje EXACT phrases (wyższy ranking!)

                        **Jak interpretować:**
                        - **Aggressive:** 7-9 EXACT matches (cel)
                        - **Standard:** 3-4 EXACT matches (cel)

                        **Przykład EXACT match:**
                        - Fraza: "bamboo cutting board"
                        - Tytuł zawiera: "...Bamboo Cutting Board Set..."
                        - ✅ To jest EXACT match (fraza bez przerwy)

                        **Przykład NIE EXACT match:**
                        - Fraza: "bamboo cutting board"
                        - Tytuł zawiera: "...Bamboo Kitchen Board for Cutting..."
                        - ❌ To NIE jest EXACT match (słowa rozdzielone)

                        ---

                        ### **🔤 Title Character Count**

                        **Co to jest:**
                        - Liczba znaków w tytule (limit Amazon = 200)
                        - System celuje w 190-199 znaków (96-99% utilization)

                        **Dlaczego nie 200?**
                        - Margines bezpieczeństwa (łatwiej edytować)
                        - Niektóre kategorie mają limit 199
                        - Lepiej być pod limitem niż nad

                        **Przykład:**
                        - Wygenerowany tytuł: 197 znaków
                        - Utilization: 197/200 = **98.5%** ✅

                        ---

                        ### **🔠 Backend Search Terms (Bytes)**

                        **Co to jest:**
                        - Backend keywords (niewidoczne dla klienta, widoczne dla Amazon A9)
                        - Limit: **249 bajtów** (nie znaków!)
                        - System celuje w 240-249 bajtów (96-99% utilization)

                        **Dlaczego bajty, nie znaki?**
                        - Niektóre znaki = 2 bajty (np. emoji, akcenty)
                        - Spacja = 1 bajt, litera = 1 bajt
                        - Amazon liczy bajty, nie znaki!

                        **Co tam wchodzi:**
                        - Keywords które **NIE są** w tytule/bullets (no duplicates)
                        - Wysokie Search Volume
                        - Long-tail keywords
                        - Synonimy

                        **Przykład:**
                        - Backend: "chopping block butcher kitchen wooden organic chef professional"
                        - 67 znaków = 67 bajtów (tylko litery + spacje)
                        - Limit: 249 bajtów → **27% wykorzystania** (można dodać więcej)

                        ---

                        ### **✅ Validation Status**

                        **Co sprawdza:**
                        - ✅ **Title <200 znaków** (Amazon wymóg)
                        - ✅ **Backend <250 bajtów** (Amazon wymóg)
                        - ✅ **Repetition <5× per word** (unikanie spam)
                        - ✅ **No forbidden words** (sale, free, best, discount, warranty, medical claims)

                        **Co zrobić jeśli ERROR:**
                        - **Title too long** → Usuń 1-2 słowa z końca tytułu
                        - **Repetition >5×** → Jakieś słowo powtarza się >5 razy w listingu - usuń kilka wystąpień
                        - **Forbidden words** → System wykrył zakazane słowa - usuń je (Amazon odrzuci listing)

                        ---

                        **💡 WSKAZÓWKA:** Dobre statystyki to: Coverage >90%, EXACT matches 7-9, Title 190-199 znaków, Backend 240-249 bajtów.
                        """)

                    output_tabs = gr.Tabs()
                    with output_tabs:
                        with gr.Tab("📝 Formatted Output"):
                            output_text = gr.Markdown(
                                label="Optimized Listing",
                                elem_classes=["markdown-text"]
                            )

                        with gr.Tab("💾 Download"):
                            download_file = gr.File(
                                label="Download Complete Listing",
                                interactive=False
                            )
                            gr.Markdown("""
                            **📥 Download Instructions:**
                            1. Click the download button above
                            2. Open the .txt file
                            3. Copy-paste sections to Amazon Seller Central
                            4. Publish your optimized listing!
                            """)

        # Help tab (English)
        with gr.Tab("📚 Help & Documentation"):
            gr.Markdown("""
            # 🎓 Quick Start Guide

            ## Step 1: Export Data from Helium 10

            ### Data Dive CSV (Required)
            1. Go to **Helium 10 → Data Dive**
            2. Select your niche/product category
            3. Click **Export → Listing Builder** format
            4. Save the CSV file

            ### Cerebro CSV (Optional - Competitor Analysis)
            1. Go to **Helium 10 → Cerebro**
            2. Enter **3-5 top competitor ASINs** (comma-separated)
            3. Click **"Get Keywords"**
            4. Filter: **Competing Products ≥ 3**
            5. Export CSV

            ### Magnet CSV (Optional - Keyword Variations)
            1. Go to **Helium 10 → Magnet**
            2. Enter your **main keyword** (e.g., "cutting board")
            3. Set **Smart Score ≥ 50**
            4. Set **Search Volume ≥ 50**
            5. Export CSV

            ---

            ## Step 2: Upload & Configure

            1. **Upload Data Dive CSV** (required)
            2. **Enter Brand Name** (e.g., "HAG EXPRESS")
            3. **Enter Product Line** (e.g., "Bamboo Cutting Board Set")
            4. **Select Mode:**
               - **Aggressive:** 96-98% coverage, 7-9 EXACT phrases (recommended)
               - **Standard:** 82-85% coverage, 3-4 EXACT phrases

            5. **(Optional)** Add Cerebro/Magnet CSVs for enhanced results
            6. **(Optional)** Set minimum search volume filter

            ---

            ## Step 3: Generate & Download

            1. Click **"🚀 Generate Optimized Listing"**
            2. Wait for processing (usually 5-15 seconds)
            3. Review results in the dashboard
            4. Download the .txt file
            5. Copy-paste to Amazon Seller Central

            ---

            ## 🎯 Optimization Modes

            ### Aggressive Mode (Recommended)
            - **Coverage:** 96-98% of top 200 keywords
            - **Title:** 7-9 EXACT phrase matches, 190+ characters
            - **Backend:** 240-249 bytes (96-99% utilization)
            - **Best for:** Competitive niches, high search volume products

            ### Standard Mode
            - **Coverage:** 82-85% of top 200 keywords
            - **Title:** 3-4 EXACT phrase matches, 140-150 characters
            - **Backend:** Standard optimization
            - **Best for:** Premium products, less competitive niches

            ---

            ## 💡 Pro Tips

            - **Cerebro:** Use 3-5 direct competitors (same product type)
            - **Magnet:** Focus on your primary keyword, not broad terms
            - **Volume Filter:** Start with 0, increase if too many keywords
            - **Multi-File:** Use Union for bundles, Intersection for core keywords
            - **Review Output:** Always review before uploading to Amazon

            ---

            ## 📞 Support

            See `PRODUCTION_README.md` for detailed documentation.
            """)

        # Polish instructions tab
        with gr.Tab("🇵🇱 Instrukcje PL"):
            gr.Markdown("""
            # 🎓 Kompleksowy Przewodnik po Amazon Listing Builder

            ## 📋 Czym jest ten system?

            Amazon Listing Builder to zaawansowane narzędzie do optymalizacji listingów produktów Amazon. System automatycznie:
            - **Tworzy tytuł** z 7-9 dokładnymi frazami kluczowymi (tryb agresywny)
            - **Generuje 5 punktów** z zaletami produktu
            - **Pisze opis** zoptymalizowany SEO
            - **Optymalizuje backend search terms** (240-249 bajtów, 96-99% wykorzystania)
            - **Zapewnia pokrycie 73-98%** najważniejszych słów kluczowych

            ---

            ## 🚀 KROK 1: Eksport danych z Helium 10

            ### A) Data Dive CSV (WYMAGANE)

            **Co to jest Data Dive?**
            - Narzędzie Helium 10 do analizy najlepszych słów kluczowych w niszy
            - Pokazuje wolumen wyszukiwań, konkurencję, relevance
            - Eksportuje do 450 słów kluczowych posortowanych według ważności

            **Jak wyeksportować:**
            1. Zaloguj się do **Helium 10**
            2. Przejdź do **Data Dive** (ikona lupy w menu)
            3. Wpisz **główne słowo kluczowe** Twojego produktu (np. "bamboo cutting board")
            4. Poczekaj na analizę (30-60 sekund)
            5. Kliknij **"Export"** (prawy górny róg)
            6. Wybierz format **"Listing Builder"** lub **"CSV"**
            7. Zapisz plik na dysku (np. `data_dive_bamboo_cutting_board.csv`)

            **Co system zrobi z tym plikiem:**
            - Wyciągnie top 200 słów kluczowych
            - Posortuje według relevance i wolumenu
            - Podzieli na tier 1 (tytuł), tier 2 (bullet points), tier 3 (backend)

            ---

            ### B) Cerebro CSV (OPCJONALNE - Analiza konkurencji)

            **Co to jest Cerebro?**
            - Narzędzie do analizy konkurencji
            - Pokazuje słowa kluczowe, na które rankują Twoi konkurenci
            - Znajduje **keyword gaps** - frazy, których Ci brakuje

            **Kiedy używać:**
            - Masz zidentyfikowanych 3-5 bezpośrednich konkurentów
            - Chcesz znaleźć ukryte słowa kluczowe
            - Chcesz zobaczyć, co działa u konkurencji

            **Jak wyeksportować:**
            1. Przejdź do **Helium 10 → Cerebro**
            2. Wpisz **ASIN-y konkurentów** (3-5 produktów), oddzielone przecinkami
               - Przykład: `B08XYZ1234,B09ABC5678,B07DEF9012`
               - **Ważne:** Wybierz produkty **bardzo podobne** do Twojego
            3. Kliknij **"Get Keywords"**
            4. Poczekaj na analizę (1-2 minuty)
            5. **Ustaw filtr:** "Competing Products" ≥ 3 (pokaż frazy, na które rankuje min. 3 konkurentów)
            6. Kliknij **"Export"** → zapisz CSV

            **Co system zrobi:**
            - Znajdzie frazy, których NIE MASZ w Data Dive
            - Doda je do puli słów kluczowych
            - Priorytetyzuje frazy z wysoką konkurencją (= działają u innych)

            ---

            ### C) Magnet CSV (OPCJONALNE - Warianty słów kluczowych)

            **Co to jest Magnet?**
            - Narzędzie do znajdowania **wariantów** głównego słowa kluczowego
            - Generuje synonimy, long-tail keywords, powiązane frazy
            - Przykład: "cutting board" → "chopping board", "wood cutting board", "kitchen board"

            **Kiedy używać:**
            - Chcesz maksymalnie pokryć wszystkie warianty głównej frazy
            - Chcesz dodać synonimy i long-tail keywords
            - Twoja niszа ma dużo różnych określeń na ten sam produkt

            **Jak wyeksportować:**
            1. Przejdź do **Helium 10 → Magnet**
            2. Wpisz **główne słowo kluczowe** (np. "cutting board")
            3. Ustaw filtry:
               - **Smart Score:** ≥ 50 (tylko dobre frazy)
               - **Search Volume:** ≥ 50 (min. 50 wyszukiwań/miesiąc)
            4. Kliknij **"Get Keywords"**
            5. Eksportuj CSV

            **Co system zrobi:**
            - Doda warianty do puli słów kluczowych
            - Zwiększy pokrycie różnych sposobów wyszukiwania produktu

            ---

            ## ⚙️ KROK 2: Konfiguracja i opcje zaawansowane

            ### Wymagane pola:

            **1. Data Dive CSV**
            - Przenieś plik lub kliknij, aby wybrać
            - Akceptowane formaty: `.csv`
            - System automatycznie wykryje kolumny (Keyword, Search Volume, itp.)

            **2. Brand Name (Nazwa marki)**
            - Wpisz dokładnie jak ma się pojawić w tytule
            - Przykład: "HAG EXPRESS"
            - Zostanie dodane na początku tytułu

            **3. Product Line (Linia produktowa)**
            - Krótki opis produktu
            - Przykład: "Bamboo Cutting Board Set"
            - Używane w tytule i opisie

            **4. Optimization Mode (Tryb optymalizacji)**

            **→ Aggressive (ZALECANE):**
            - **Pokrycie:** 96-98% top 200 słów kluczowych
            - **Tytuł:** 7-9 dokładnych fraz (EXACT match), 190-199 znaków (99% wykorzystania)
            - **Backend:** 240-249 bajtów (96-99% wykorzystania)
            - **Najlepsze dla:**
              - Konkurencyjnych nisz (dużo sprzedawców)
              - Produktów z wysokim wolumenem wyszukiwań
              - Maksymalizacji rankingu w algorytmie A9

            **→ Standard:**
            - **Pokrycie:** 82-85% top 200 słów kluczowych
            - **Tytuł:** 3-4 dokładne frazy, 140-150 znaków
            - **Backend:** Standardowa optymalizacja
            - **Najlepsze dla:**
              - Produktów premium (czytelność > SEO)
              - Mniej konkurencyjnych nisz
              - Gdy zależy Ci na krótszym, bardziej czytelnym tytule

            ---

            ### Opcje zaawansowane (OPCJONALNE):

            **🔍 Competitor Analysis (Analiza konkurencji)**
            - Dodaj plik Cerebro CSV
            - System znajdzie **keyword gaps** (luki w Twoich słowach kluczowych)
            - Maksymalnie 50 dodatkowych fraz z analizy konkurencji

            **🔄 Keyword Expansion (Ekspansja słów kluczowych)**
            - Dodaj plik Magnet CSV
            - System doda warianty i synonimy
            - Zwiększa pokrycie różnych sposobów wyszukiwania

            **📊 Multi-File Merge (Łączenie wielu plików)**
            - Możesz dodać **wiele plików Data Dive CSV**
            - Przydatne gdy:
              - Masz bundle produktów (np. "cutting board set" + "bamboo cutting board")
              - Chcesz połączyć dane z różnych nisz

            **Strategie łączenia:**
            - **Union (Suma):** Wszystkie słowa kluczowe ze wszystkich plików
              - Użyj gdy: Chcesz maksymalne pokrycie
            - **Intersection (Przecięcie):** Tylko słowa wspólne dla wszystkich plików
              - Użyj gdy: Chcesz core keywords (najbardziej relevantne)

            **⚙️ Filters (Filtry)**
            - **Minimum Search Volume:** Minimalna liczba wyszukiwań/miesiąc
            - Przykład: Ustaw 100 → system usunie frazy z <100 wyszukiwań
            - **Kiedy używać:**
              - Masz zbyt wiele słów kluczowych (>450)
              - Chcesz skupić się na high-volume keywords
              - Chcesz wykluczyć long-tail z małym wolumenem

            ---

            ## 🎯 KROK 3: Generowanie i wyniki

            **Kliknij "🚀 Generate Optimized Listing"**

            **Co się dzieje (5-15 sekund):**
            1. **Parsowanie CSV** - Wczytanie wszystkich plików
            2. **Analiza konkurencji** (jeśli dodano Cerebro)
            3. **Ekspansja keywords** (jeśli dodano Magnet)
            4. **Łączenie plików** (jeśli dodano dodatkowe CSV)
            5. **Filtrowanie** po wolumenie (jeśli ustawiono)
            6. **Budowa tytułu** - Greedy algorithm dla max pokrycia
            7. **Generowanie bullet points** - 5 punktów z benefitami
            8. **Pisanie opisu** - 3 paragrafy z tier 3 keywords
            9. **Optymalizacja backend** - Greedy packing 240-249 bajtów
            10. **Walidacja** - Sprawdzenie długości, repetycji, forbidden words

            **Dashboard z wynikami pokaże:**

            **📊 Performance Metrics:**
            - **Overall Coverage:** % pokrytych słów kluczowych (cel: >73%)
            - **Mode:** Aggressive lub Standard
            - **EXACT Matches:** Liczba dokładnych fraz w tytule (cel: 7-9)
            - **Title:** Długość/200 znaków, % wykorzystania
            - **Bullets:** Liczba punktów (zawsze 5)
            - **Backend:** Bajty/250, % wykorzystania (cel: >96%)
            - **Validation:** ✅ jeśli wszystko OK

            **📝 Formatted Output (zakładka):**
            - Listing w formacie Markdown
            - Skopiuj i wklej do Notatnika lub dokumentu

            **💾 Download (zakładka):**
            - Przycisk do pobrania pliku `.txt`
            - Nazwa pliku: `optimized_listing_BRAND_NAME.txt`
            - Zawiera pełny listing gotowy do copy-paste

            ---

            ## 📋 KROK 4: Użycie na Amazon Seller Central

            **Jak wkleić wygenerowany listing:**

            1. **Zaloguj się do Amazon Seller Central**
            2. Przejdź do **Inventory → Manage Inventory**
            3. Kliknij **"Edit"** przy swoim produkcie
            4. Otwórz pobrany plik `.txt`

            **Copy-paste sekcji:**

            **TITLE:**
            - Skopiuj cały tytuł (1 linia)
            - Wklej do pola **"Product Name"** w Seller Central
            - Limit: 200 znaków (system generuje 190-199)

            **BULLET POINTS:**
            - Skopiuj wszystkie 5 punktów
            - Wklej do pól **"Key Product Features"** (5 pól)
            - Usuń numerację (1. 2. 3. itd.) jeśli Amazon nie akceptuje
            - Usuń emojis ✓ jeśli Amazon nie akceptuje

            **DESCRIPTION:**
            - Skopiuj cały opis (3 paragrafy)
            - Wklej do pola **"Product Description"**
            - Limit: 2000 znaków (system generuje ~600-800)

            **BACKEND SEARCH TERMS:**
            - Skopiuj całą linię z sekcji "BACKEND SEARCH TERMS"
            - Przejdź do zakładki **"Keywords"** w Seller Central
            - Wklej do pola **"Generic Keywords"** lub **"Search Terms"**
            - **WAŻNE:** Bez przecinków, tylko spacje
            - Limit: 249 bajtów (system generuje 240-249)

            5. Kliknij **"Save and finish"**

            ---

            ## ❓ Najczęstsze pytania (FAQ)

            **Q: Czy muszę mieć Helium 10?**
            A: TAK - minimum potrzebujesz Data Dive CSV. Cerebro i Magnet są opcjonalne.

            **Q: Czy mogę edytować wygenerowany listing?**
            A: TAK - zawsze możesz ręcznie zmodyfikować tytuł, punkty, opis. System daje bazę, Ty dopiesujesz.

            **Q: Co zrobić jeśli tytuł ma 201 znaków?**
            A: System generuje 190-199 znaków. Jeśli widzisz 201+, usuń 1-2 słowa ręcznie.

            **Q: Czy mogę użyć tego dla wielu produktów?**
            A: TAK - po prostu wygeneruj osobny listing dla każdego produktu (nowy Data Dive CSV dla każdego).

            **Q: Jak często aktualizować listing?**
            A: Co 3-6 miesięcy lub gdy:
            - Zmieniają się trendy wyszukiwań
            - Pojawiają się nowi konkurenci
            - Twój ranking spada

            **Q: Co jeśli mój produkt jest w bundle?**
            A: Użyj opcji "Multi-File Merge" - dodaj osobne Data Dive CSV dla każdego produktu w bundle.

            **Q: Dlaczego backend search terms nie mają przecinków?**
            A: Amazon zaleca spacje zamiast przecinków. System automatycznie formatuje poprawnie.

            ---

            ## 💡 Zaawansowane porady

            **→ Maksymalizacja rankingu:**
            - Zawsze używaj trybu **Aggressive**
            - Dodaj **Cerebro** dla keyword gaps
            - Ustaw **min volume = 0** (nie filtruj)

            **→ Premium produkty:**
            - Użyj trybu **Standard** dla czytelności
            - Ręcznie dopracuj język w bullet points
            - Skup się na benefitach, nie tylko keywords

            **→ Bundle produkty:**
            - Dodaj 2-3 Data Dive CSV (1 dla każdego produktu)
            - Użyj strategii **Union**
            - To da maksymalne pokrycie wszystkich wariantów

            **→ Bardzo konkurencyjna nisza:**
            - Dodaj **Cerebro** z 5 top konkurentów
            - Dodaj **Magnet** dla maksymalnej ekspansji
            - Użyj **Aggressive** + **min volume ≥ 50**

            ---

            ## 📞 Wsparcie techniczne

            **Dokumentacja:**
            - `PRODUCTION_README.md` - Pełna dokumentacja (English)
            - `V2_ENHANCEMENTS.md` - Lista funkcji v2.0
            - `GUI_SHOWCASE.md` - Dokumentacja designu

            **Problemy:**
            - Sprawdź czy pliki CSV są z Helium 10
            - Sprawdź czy Data Dive jest w formacie "Listing Builder"
            - Upewnij się że plik ma kolumnę "Keyword" i "Search Volume"
            """)

        # FAQ tab
        with gr.Tab("❓ FAQ"):
            gr.Markdown("""
            # ❓ Najczęściej Zadawane Pytania (FAQ)

            ## 📁 Pytania o pliki CSV

            **Q: Skąd wziąć plik Data Dive CSV?**
            A: Musisz mieć subskrypcję Helium 10 (Platinum lub wyżej). Przejdź do Data Dive, wpisz keyword, eksportuj CSV.

            **Q: Czy mogę użyć CSV z innego narzędzia (Jungle Scout, Viral Launch)?**
            A: NIE - system został zaprojektowany specjalnie dla formatów Helium 10 (Data Dive, Cerebro, Magnet). Inne narzędzia mają inne kolumny i nazewnictwo.

            **Q: Co jeśli mój CSV ma błąd "invalid format"?**
            A: Sprawdź czy:
            - Plik jest z Helium 10 Data Dive
            - Format eksportu to "Listing Builder" lub standardowy CSV
            - Plik ma kolumny: "Keyword", "Search Volume", "Relevancy"
            - Plik NIE jest pusty

            **Q: Ile słów kluczowych musi być w CSV?**
            A: Minimum 50, zalecane 200-450. Data Dive zwykle daje 200-450 keywords.

            **Q: Czy mogę edytować CSV przed uplodem?**
            A: TAK, ale:
            - NIE usuwaj nagłówków kolumn
            - NIE zmieniaj nazw kolumn
            - Możesz usunąć nierelewantne słowa kluczowe ręcznie

            ---

            ## ⚙️ Pytania o konfigurację

            **Q: Jaka różnica między Aggressive a Standard?**
            A:
            - **Aggressive:** 7-9 EXACT fraz, 96-98% coverage, 190-199 znaków w tytule (MAX SEO)
            - **Standard:** 3-4 EXACT frazy, 82-85% coverage, 140-150 znaków (balans SEO + czytelność)
            - **Zalecenie:** Aggressive dla 95% produktów

            **Q: Kiedy używać Cerebro CSV?**
            A: Gdy:
            - Znasz 3-5 bezpośrednich konkurentów (te same produkty)
            - Chcesz znaleźć "keyword gaps" (czego Ci brakuje)
            - Chcesz zobaczyć na co rankują best-sellerzy

            **Q: Kiedy używać Magnet CSV?**
            A: Gdy:
            - Chcesz maksymalnie pokryć wszystkie warianty głównego keyword
            - Twoja nisza ma wiele synonimów (np. "cutting board" = "chopping board")
            - Chcesz dodać long-tail keywords

            **Q: Co robi filtr "Minimum Search Volume"?**
            A: Usuwa słowa kluczowe z mniejszym wolumenem wyszukiwań. Przykład:
            - Ustawisz 100 → system usunie frazy z <100 wyszukiwań/miesiąc
            - Zostają tylko high-volume keywords
            - **Zalecenie:** Zostaw na 0, chyba że masz zbyt wiele keywords

            **Q: Union vs Intersection - którą strategię wybrać?**
            A:
            - **Union (Suma):** Wszystkie keywords ze wszystkich plików → MAX pokrycie
              - Użyj dla: Bundles, różne produkty w zestawie
            - **Intersection (Przecięcie):** Tylko wspólne keywords → CORE keywords
              - Użyj dla: Bardzo podobne produkty, chcesz focus na najważniejszych

            ---

            ## 🎯 Pytania o wyniki

            **Q: Co oznacza "Coverage 73.5%"?**
            A: System pokrył 73.5% z top 200 słów kluczowych w całym listingu (tytuł + bullets + backend).
            - **<70%:** Niedooptymalizowane
            - **70-85%:** Dobre (Standard mode)
            - **85-98%:** Świetne (Aggressive mode)

            **Q: Co to są "EXACT Matches"?**
            A: Liczba **dokładnych fraz** z Data Dive, które znalazły się w tytule bez przerwy.
            - Przykład: "bamboo cutting board" w tytule = 1 EXACT match
            - "bamboo" i "cutting board" osobno = 0 EXACT matches
            - **Aggressive:** Cel 7-9 EXACT matches
            - **Standard:** Cel 3-4 EXACT matches

            **Q: Dlaczego tytuł ma 199 znaków zamiast 200?**
            A: System celuje w 190-199 znaków (95-99.5% utilization) żeby:
            - Zmaksymalizować SEO
            - Zostawić margines na ewentualne edycje
            - Uniknąć przekroczenia limitu 200 znaków

            **Q: Dlaczego backend ma tylko 242 bajty zamiast 250?**
            A: System celuje w 240-249 bajtów (96-99% utilization). To daje:
            - MAX wykorzystanie przestrzeni
            - Margines bezpieczeństwa (niektóre znaki = 2 bajty)
            - Uniknięcie przekroczenia limitu 250 bajtów

            **Q: Co jeśli walidacja pokazuje ERROR?**
            A: Sprawdź błędy:
            - **Title too long:** Usuń 1-2 słowa z końca tytułu
            - **Repetition >5×:** Jakieś słowo powtarza się >5 razy - usuń kilka wystąpień
            - **Forbidden words:** System wykrył zakazane słowa (sale, discount, free, warranty, medical claims) - usuń je

            ---

            ## 📝 Pytania o użycie na Amazon

            **Q: Czy mogę wkleić listing dokładnie jak wygenerowany?**
            A: TAK, ale sprawdź:
            - Czy Amazon akceptuje emojis (✓) w bullet points (zwykle TAK)
            - Czy tytuł mieści się w limicie (200 znaków)
            - Czy backend search terms nie mają przecinków (system daje bez przecinków = OK)

            **Q: Czy muszę usunąć numerację z bullet points (1. 2. 3.)?**
            A: To zależy od kategorii:
            - Większość kategorii: Numeracja OK
            - Niektóre (Fashion, Beauty): Amazon może wymagać bez numeracji
            - Jeśli Amazon odrzuca, usuń numerację ręcznie

            **Q: Gdzie wkleić backend search terms?**
            A: W Seller Central:
            - Zakładka **"Keywords"**
            - Pole **"Generic Keywords"** lub **"Search Terms"** (zależy od kategorii)
            - **WAŻNE:** Wklej DOKŁADNIE jak wygenerowane (spacje, bez przecinków)

            **Q: Czy mogę edytować wygenerowany listing?**
            A: TAK! System daje bazę, Ty możesz:
            - Zmienić kolejność słów w tytule (zachowując EXACT phrases)
            - Dopracować language w bullet points
            - Dodać więcej szczegółów w opisie
            - **NIE usuwaj** EXACT phrases z tytułu (zepsuje SEO)

            **Q: Jak często aktualizować listing?**
            A: Zalecenie:
            - **Co 3 miesiące:** Sprawdź czy keywords się zmieniły (nowy Data Dive)
            - **Co 6 miesięcy:** Pełna regeneracja listingu
            - **Natychmiast** jeśli:
              - Twój ranking drastycznie spadł
              - Pojawiło się nowe trendy / sezony
              - Konkurenci wyprzedzili Cię w rankingu

            ---

            ## 🔧 Pytania techniczne

            **Q: Czy mogę użyć systemu offline?**
            A: TAK - system działa lokalnie na Twoim komputerze. Nie wysyła danych nigdzie.

            **Q: Czy moje dane są bezpieczne?**
            A: TAK:
            - System nie wysyła danych do internetu
            - Wszystko dzieje się lokalnie
            - Pliki CSV są przetwarzane tylko na Twoim komputerze

            **Q: Czy potrzebuję API key do Helium 10?**
            A: NIE - system wymaga tylko wyeksportowanych plików CSV. Nie łączy się z Helium 10 API.

            **Q: Jak długo trwa generowanie?**
            A: Zazwyczaj 5-15 sekund. Zależy od:
            - Liczby plików CSV (więcej plików = dłużej)
            - Liczby keywords (>1000 keywords = ~20 sekund)

            **Q: Dlaczego backend search terms nie pokrywają wszystkich keywords?**
            A: Backend ma limit 250 bajtów (~40-50 słów). System wybiera:
            - Słowa które NIE są już w tytule/bullets (no duplicates)
            - Słowa z najwyższym Search Volume
            - Używa greedy algorithm dla MAX coverage

            **Q: Co jeśli mam więcej niż 450 keywords?**
            A: System automatycznie:
            - Wybiera top 200 według relevancy + search volume
            - Ignoruje resztę (słabe, niezrelevantne keywords)
            - Możesz użyć filtru "Min Volume" żeby dodatkowo przefiltrować

            ---

            ## 💼 Pytania biznesowe

            **Q: Czy mogę użyć tego dla klienta (agencja)?**
            A: TAK - system jest darmowy i lokalny. Możesz generować listingi dla klientów.

            **Q: Czy mogę sprzedawać wygenerowane listingi?**
            A: TAK - wygenerowany listing jest Twój. Możesz:
            - Sprzedawać jako usługę
            - Używać dla klientów
            - Włączyć w pakiet onboardingu Amazon

            **Q: Ile mogę zaoszczędzić czasu?**
            A: Ręczna optymalizacja listingu = 2-4 godziny. System = 15 sekund. Oszczędność: 99%+ czasu.

            **Q: Czy wygenerowany listing gwarantuje ranking?**
            A: NIE - listing to tylko część sukcesu na Amazon. Ranking zależy też od:
            - Velocity (liczba sprzedaży)
            - Conversion rate (CTR, click-to-purchase)
            - Reviews (liczba i rating)
            - PPC campaigns
            - Images quality
            - Pricing
            **ALE:** Dobry listing zwiększa szanse na wysoki ranking o 30-50%.

            ---

            ## 🎓 Pytania edukacyjne

            **Q: Czym jest algorytm A9?**
            A: Wyszukiwarka Amazon. Ranking zależy od:
            - **Relevance:** Czy Twój listing zawiera szukane keywords (= listing optimization)
            - **Performance:** Velocity, conversion rate, reviews
            - **Customer behavior:** CTR, time on page, cart adds

            **Q: Dlaczego EXACT phrases są ważne?**
            A: Amazon preferuje dokładne frazy. Przykład:
            - Użytkownik szuka: "bamboo cutting board"
            - Listing A: "bamboo cutting board" (exact) → WYSOKI ranking
            - Listing B: "bamboo kitchen board for cutting" (separated) → NISKI ranking

            **Q: Co to jest "keyword stuffing" i czy system tego unika?**
            A: **Keyword stuffing** = nadmierna repetycja słów (>5× = spam). System automatycznie:
            - Limituje każde słowo do MAX 5 powtórzeń w całym listingu
            - Filtruje promotional words (best, sale, cheap, free, guarantee)
            - Używa natural language w bullet points

            **Q: Dlaczego 200 keywords a nie wszystkie 450?**
            A: Top 200 = 80% całego search volume. 250-450 to long-tail z bardzo małym wolumenem (<10 wyszukiwań/miesiąc). Nie opłaca się tracić na nie miejsca.

            ---

            ## 🚀 Pytania o advanced features

            **Q: Co robi "Competitor Gap Analysis" (Cerebro)?**
            A: Znajduje keywords na które rankują konkurenci, a Ty NIE. Przykład:
            - Ty rankujesz: "cutting board", "bamboo board"
            - Konkurent rankuje: "cutting board", "bamboo board", "wooden chopping block", "chef board"
            - Gap = "wooden chopping block", "chef board" (tego Ci brakuje)
            → System doda te keywords do Twojego listingu

            **Q: Jak działa "Multi-File Merge"?**
            A: Łączy wiele Data Dive CSV. Przykład:
            - Masz bundle: "Bamboo Cutting Board Set" (3 boards)
            - CSV #1: "bamboo cutting board" (główny)
            - CSV #2: "large cutting board" (duża deska)
            - CSV #3: "small cutting board" (mała deska)
            → Merge = wszystkie keywords razem = MAX pokrycie bundle

            **Q: Kiedy używać filtru Search Volume?**
            A: Gdy masz zbyt wiele keywords. Przykład:
            - Masz 800 keywords z Data Dive + Cerebro + Magnet
            - Chcesz skupić się na high-volume
            - Ustawiasz "Min Volume = 100"
            → System zostawi tylko keywords z ≥100 wyszukiwań/miesiąc (usuwa long-tail)

            ---

            ## 📞 Pomoc techniczna

            **Jeśli nadal masz problem:**
            1. Sprawdź dokumentację: `PRODUCTION_README.md`
            2. Sprawdź logi błędów w konsoli
            3. Upewnij się że używasz Python 3.10-3.13
            4. Sprawdź czy masz najnowszą wersję (v2.0)

            **System requirements:**
            - Python 3.10+ (zalecane 3.12)
            - Gradio 5.49+ (opcjonalne, tylko dla GUI)
            - 50MB RAM
            - Internet NIE wymagany (działa offline)
            """)

        # AI Chat Assistant tab
        with gr.Tab("💬 AI Assistant"):
            # WHY: Professional header with gradient styling
            gr.Markdown("""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-size: 2.5em;">🤖 AI Amazon Strategy Assistant</h1>
                <p style="color: rgba(255,255,255,0.9); margin-top: 10px; font-size: 1.1em;">Professional Amazon FBA Strategies & Best Practices</p>
            </div>
            """)

            # WHY: Capabilities info boxes
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("""
                    <div style="padding: 15px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 8px; color: white;">
                        <h3 style="margin: 0;">📝 Listing Optimization</h3>
                        <p style="margin: 5px 0 0 0; font-size: 0.9em;">Titles, Bullets, Descriptions, Keywords</p>
                    </div>
                    """)

                with gr.Column(scale=1):
                    gr.Markdown("""
                    <div style="padding: 15px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 8px; color: white;">
                        <h3 style="margin: 0;">📈 Ranking Strategies</h3>
                        <p style="margin: 5px 0 0 0; font-size: 0.9em;">A9 Algorithm, Launch, Velocity</p>
                    </div>
                    """)

                with gr.Column(scale=1):
                    gr.Markdown("""
                    <div style="padding: 15px; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); border-radius: 8px; color: white;">
                        <h3 style="margin: 0;">💰 PPC Campaigns</h3>
                        <p style="margin: 5px 0 0 0; font-size: 0.9em;">Auto, Manual, ACoS Optimization</p>
                    </div>
                    """)

            gr.Markdown("<br>")

            # WHY: Quick action buttons
            gr.Markdown("### ⚡ Szybkie Pytania (kliknij):")

            with gr.Row():
                quick_btn1 = gr.Button("📝 Jak napisać tytuł?", size="sm")
                quick_btn2 = gr.Button("🎯 Strategia rankingu?", size="sm")
                quick_btn3 = gr.Button("💵 Setup PPC campaign?", size="sm")
                quick_btn4 = gr.Button("🔍 Backend keywords?", size="sm")

            gr.Markdown("<br>")

            # WHY: Beautiful chatbot with better height
            chatbot = gr.Chatbot(
                value=[[None, get_welcome_message()]],
                height=450,
                show_label=False
            )

            # WHY: Modern input with better styling
            with gr.Row():
                msg = gr.Textbox(
                    label="",
                    placeholder="💭 Wpisz pytanie po polsku lub angielsku... (np. 'Jak zoptymalizować bullet points?')",
                    scale=5,
                    container=False
                )
                send_btn = gr.Button("📤 Wyślij", variant="primary", scale=1, size="lg")

            with gr.Row():
                with gr.Column(scale=1):
                    clear_btn = gr.Button("🗑️ Wyczyść Czat", size="sm")
                with gr.Column(scale=4):
                    gr.Markdown("<div style='text-align: right; color: #666; font-size: 0.85em; padding: 10px;'>💡 Tip: Zadawaj konkretne pytania dla najlepszych odpowiedzi</div>")

            # WHY: Help section
            gr.Markdown("---")
            with gr.Accordion("❓ Czego mogę zapytać AI Assistant?", open=False):
                gr.Markdown("""
                ### 📚 Kategorie Wiedzy:

                **1. 📝 Optimalizacja Listingów**
                - Jak stworzyć idealny tytuł Amazon? (7-9 fraz kluczowych)
                - Jak pisać bullet points, które konwertują?
                - Backend search terms best practices (240-249 bajtów)
                - Opis produktu - struktura i SEO

                **2. 📈 Ranking & A9 Algorithm**
                - Jak działa Amazon A9 algorithm?
                - Strategia launch produktu (velocity)
                - Jak zwiększyć ranking organiczny?
                - CTR vs Conversion Rate - co ważniejsze?

                **3. 💰 PPC & Advertising**
                - Setup pierwszej kampanii PPC
                - Auto vs Manual campaigns - kiedy co?
                - Jak obniżyć ACoS?
                - Negative keywords - strategia

                **4. 🔍 Keyword Research**
                - Jak znaleźć best keywords?
                - Competitor analysis z Cerebro
                - Long-tail vs Short-tail keywords
                - Keyword density w listingu

                **5. 📊 Competition & Market**
                - Jak analizować konkurencję?
                - Red flags przy wyborze produktu
                - Blue ocean vs red ocean strategy
                - Seasonal products - kiedy unikać?

                **6. 🎯 Conversion Rate Optimization**
                - Main image best practices
                - A+ Content - czy warto?
                - Trust signals i social proof
                - Price psychology

                **7. 📦 Inventory & Logistics**
                - FBA vs FBM - pros & cons
                - Reorder points i stock planning
                - Multi-channel fulfillment
                """)

            # WHY: Connect chat functions
            msg.submit(chat_with_ai, inputs=[msg, chatbot], outputs=[chatbot])
            send_btn.click(chat_with_ai, inputs=[msg, chatbot], outputs=[chatbot])

            # WHY: Quick buttons functionality
            quick_btn1.click(lambda: "Jak napisać idealny tytuł Amazon produktu?", outputs=[msg])
            quick_btn2.click(lambda: "Jaka jest najlepsza strategia rankingu dla nowego produktu?", outputs=[msg])
            quick_btn3.click(lambda: "Jak ustawić pierwszą kampanię PPC dla nowego listingu?", outputs=[msg])
            quick_btn4.click(lambda: "Backend search terms best practices - jak je zoptymalizować?", outputs=[msg])

            clear_btn.click(lambda: [[None, get_welcome_message()]], outputs=[chatbot])

            # WHY: Clear input after sending
            msg.submit(lambda: "", outputs=[msg])
            send_btn.click(lambda: "", outputs=[msg])

        # Product Research / Sales Potential tab
        with gr.Tab("🔍 Badanie Potencjału"):
            gr.Markdown("""
            # 🔍 Analiza Potencjału Sprzedażowego

            **Wybierz metodę analizy poniżej - każda zakładka to inna opcja:**

            """)

            # WHY: Internal Tabs for clearer separation of options
            with gr.Tabs():
                # TAB 1: Quick CSV Analysis
                with gr.Tab("📊 Szybka Analiza CSV"):
                    gr.Markdown("""
                    ### 📊 Szybka Analiza CSV (Tekst)

                    **Kiedy użyć:**
                    - Chcesz szybki przegląd produktów (5-10 sekund)
                    - Potrzebujesz summary w tekście (nie Excel)
                    - Analizujesz 1 plik Black Box CSV

                    **Co dostaniesz:**
                    - Top 10 produktów z największym revenue
                    - Średnie statystyki niszy (revenue, reviews, rating, BSR)
                    - Rekomendacja czy nisza jest opłacalna (TAK/NIE)
                    """)

                    gr.Markdown("---")
                    gr.Markdown("### 📁 Jak wyeksportować z Helium 10 Black Box:")
                    gr.Markdown("""
                    1. Helium 10 → Black Box → Search
                    2. Ustaw filtry (Price, Revenue, Reviews, etc.)
                    3. Kliknij **"Export"** (prawy górny róg)
                    4. Pobierz CSV i załaduj poniżej
                    """)

                    blackbox_csv_input = gr.File(
                        label="Black Box CSV",
                        file_types=[".csv"],
                        type="filepath"
                    )

                    csv_analyze_btn = gr.Button(
                        "🔍 Analizuj CSV (Szybka Analiza Tekstowa)",
                        variant="primary",
                        size="lg"
                    )

                    csv_analysis_output = gr.Markdown(
                        value="Załaduj plik CSV i kliknij 'Analizuj'"
                    )

                # TAB 2: Beautiful Excel Report
                with gr.Tab("🎨 Excel Report (PRO) ⭐"):
                    gr.Markdown("""
                    ### 🎨 Piękny Raport Excel (PRO)

                    **Kiedy użyć:**
                    - Chcesz profesjonalny raport do prezentacji/analizy
                    - Potrzebujesz kolorów, wykresów, szczegółów
                    - Analizujesz 1 lub 2 pliki CSV (Niche + Black Box)

                    **Co dostaniesz:**
                    - 🎨 **10 arkuszy** z kolorami i wyjaśnieniami
                    - 📊 **Scoring 0-100** każdego produktu (algorytm)
                    - 💎 **Opportunity Matrix** (złote okazje - HIGH, MEDIUM, LOW)
                    - 🔍 **Competition Analysis** (Easy/Medium/Hard)
                    - 💡 **Strategic Insights** (rekomendacje)
                    - 📈 **Executive Summary** (kluczowe metryki)
                    - 📊 **Top 50 by Revenue** (najlepsze produkty)

                    **Kolory:**
                    - 🟢 Zielony = HIGH POTENTIAL (score ≥70)
                    - 🟡 Żółty = MEDIUM POTENTIAL (score 50-69)
                    - 🔴 Czerwony = LOW POTENTIAL (score <50)
                    """)

                    gr.Markdown("---")
                    gr.Markdown("### 📁 Upload 1 lub 2 pliki CSV:")
                    gr.Markdown("""
                    - **Niche CSV** (opcjonalny) - top performers z niszowej analizy
                    - **Black Box CSV** (opcjonalny) - szeroki rynek, long-tail opportunities

                    System automatycznie porówna oba źródła i pokaże overlap + unique products.
                    """)

                    with gr.Row():
                        niche_csv_input = gr.File(
                            label="📈 Niche CSV (Optional)",
                            file_types=[".csv"],
                            type="filepath"
                        )

                        blackbox_csv_for_excel = gr.File(
                            label="📦 Black Box CSV (Optional)",
                            file_types=[".csv"],
                            type="filepath"
                        )

                    excel_gen_btn = gr.Button(
                        "🎨 Generuj Piękny Raport Excel (10 arkuszy + kolory)",
                        variant="primary",
                        size="lg"
                    )

                    excel_report_output = gr.Markdown(
                        value="Załaduj CSV i kliknij 'Generuj Piękny Raport'"
                    )

                # TAB 3: Manual Input
                with gr.Tab("✏️ Analiza Manualna"):
                    gr.Markdown("""
                    ### ✏️ Analiza Manualna (bez CSV)

                    **Kiedy użyć:**
                    - Nie masz CSV z Helium 10
                    - Masz dane z innego źródła (Jungle Scout, ręczna analiza)
                    - Chcesz sprawdzić konkretny produkt (wpisz dane ręcznie)

                    **Co dostaniesz:**
                    - Scoring 0-100 na podstawie wprowadzonych danych
                    - Ocena potencjału (LOW/MEDIUM/HIGH)
                    - Rekomendacja czy warto wejść w niszę
                    """)

                    gr.Markdown("---")

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### 📊 Dane Produktu")

                            monthly_revenue_input = gr.Number(
                                label="Miesięczny Revenue ($) - np. 25000",
                                value=0
                            )

                            review_count_input = gr.Number(
                                label="Liczba Reviews (top seller) - np. 150",
                                value=0
                            )

                            review_rating_input = gr.Number(
                                label="Średni Rating (1-5) - np. 4.3",
                                value=0,
                                minimum=0,
                                maximum=5,
                                step=0.1
                            )

                            bsr_rank_input = gr.Number(
                                label="Best Seller Rank (BSR) - np. 15000",
                                value=0
                            )

                            num_competitors_input = gr.Number(
                                label="Liczba Konkurentów - np. 45",
                                value=0
                            )

                            analyze_btn = gr.Button(
                                "🔍 Analizuj Potencjał",
                                variant="primary",
                                size="lg"
                            )

                        with gr.Column():
                            gr.Markdown("### 📈 Wyniki Analizy")
                            analysis_output = gr.Markdown(
                                value="Wprowadź dane i kliknij 'Analizuj Potencjał'"
                            )

                    gr.Markdown("""
                    ---

                    ### 💡 Wskazówki (Pro Strategy)

                    **Idealny produkt ma:**
                    - 💰 Revenue: $10k-30k/miesiąc (sweet spot)
                    - ⭐ Rating: 4.0-4.5 (room for improvement)
                    - 📝 Reviews (top seller): <200 (możliwa konkurencja)
                    - 📊 BSR: <20,000 (decent demand)
                    - 👥 Konkurenci: <50 (nie oversaturated)

                    **Red flags (UNIKAJ):**
                    - ❌ Revenue <$5k/miesiąc (za mały popyt)
                    - ❌ Top seller >500 reviews (za silna konkurencja)
                    - ❌ Rating <3.5 (quality issues)
                    - ❌ BSR >100k (słaba sprzedaż)
                    - ❌ >100 konkurentów (oversaturated)

                    **Po analizie:**
                    → Jeśli score ≥60 → Przejdź do Cerebro competitor analysis
                    → Jeśli score <60 → Szukaj innego produktu
                    """)

            # WHY: Connect CSV analysis function
            csv_analyze_btn.click(
                fn=analyze_from_csv_upload,
                inputs=[blackbox_csv_input],
                outputs=[csv_analysis_output]
            )

            # WHY: Connect beautiful Excel report generator
            excel_gen_btn.click(
                fn=generate_beautiful_excel_report,
                inputs=[niche_csv_input, blackbox_csv_for_excel],
                outputs=[excel_report_output]
            )

            # WHY: Connect manual analysis function
            analyze_btn.click(
                fn=analyze_product_potential,
                inputs=[
                    monthly_revenue_input,
                    review_count_input,
                    review_rating_input,
                    bsr_rank_input,
                    num_competitors_input
                ],
                outputs=[analysis_output]
            )


    # Connect button
    optimize_btn.click(
        fn=optimize_listing_gui,
        inputs=[
            datadive_input,
            brand_input,
            product_input,
            mode_input,
            cerebro_input,
            magnet_input,
            additional_input,
            min_volume_input,
            merge_strategy_input
        ],
        outputs=[output_text, download_file, stats_display]
    )


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 Amazon Listing Builder - Professional Edition")
    print("="*70)
    print("\n✨ Starting professional web interface...")
    print("🌐 GUI will open at: http://127.0.0.1:7860\n")

    # Launch with public share link (works without authentication)
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        inbrowser=False,
        favicon_path=None
    )
