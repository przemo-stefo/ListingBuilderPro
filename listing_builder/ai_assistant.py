# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/ai_assistant.py
# Purpose: AI assistant that provides Amazon strategy advice based on extensive knowledge base
# NOT for: External API calls - works entirely locally with transcript analysis

import os
import re
from typing import List, Dict, Tuple

# WHY: Path to knowledge base (677 transcripts with Amazon strategies)
KNOWLEDGE_BASE = "/Users/shawn/.knowledge/transcripts"

# WHY: List of terms to filter out from responses (course names, instructors, programs)
# CRITICAL: Never reveal source of knowledge to users
BLACKLIST_TERMS = [
    "freedom ticket", "helium 10 course", "kevin king", "manny coats",
    "amazing selling machine", "asm", "jungle scout academy", "private label masters",
    "fba mastery", "seller sessions", "am/pm podcast", "serious sellers",
    "project x", "brand builder", "million dollar", "course", "lesson",
    "module", "training", "webinar", "masterclass", "instructor", "teacher",
    "transcript", "video", "episode", "podcast", "office hours"
]

def filter_source_references(text: str) -> str:
    """
    Remove any references to courses, instructors, or sources.
    WHY: CRITICAL - never reveal where knowledge comes from.
    """
    filtered = text
    for term in BLACKLIST_TERMS:
        # Case-insensitive replacement
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        filtered = pattern.sub("", filtered)

    # Clean up extra whitespace left by removals
    filtered = re.sub(r'\s+', ' ', filtered).strip()
    return filtered


def search_transcripts(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search transcripts for relevant information using keyword matching.
    WHY: Provides context-aware answers without external LLM API.
    """
    # WHY: Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    query_words = query_lower.split()

    results = []

    # WHY: Check if knowledge base exists
    if not os.path.exists(KNOWLEDGE_BASE):
        return []

    # WHY: Scan all transcript files
    for filename in os.listdir(KNOWLEDGE_BASE):
        if not filename.endswith('.txt'):
            continue

        filepath = os.path.join(KNOWLEDGE_BASE, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                content_lower = content.lower()

                # WHY: Calculate relevance score based on keyword matches
                score = 0
                for word in query_words:
                    if len(word) > 3:  # WHY: Ignore short words (the, and, etc.)
                        score += content_lower.count(word)

                # WHY: Only include if relevant (score > 2)
                if score > 2:
                    # WHY: Extract preview snippet (first 300 chars after first match)
                    first_match_pos = content_lower.find(query_words[0])
                    if first_match_pos >= 0:
                        snippet_start = max(0, first_match_pos - 50)
                        snippet_end = min(len(content), first_match_pos + 300)
                        snippet = content[snippet_start:snippet_end].strip()
                    else:
                        snippet = content[:300].strip()

                    results.append({
                        'filename': filename,
                        'score': score,
                        'snippet': snippet,
                        'content': content
                    })

        except Exception as e:
            continue  # WHY: Skip files with read errors

    # WHY: Sort by relevance score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)

    return results[:max_results]


def get_answer(question: str) -> str:
    """
    Get answer to user's Amazon strategy question.
    WHY: Provides intelligent responses based on knowledge base without revealing source.
    """
    question_lower = question.lower()

    # WHY: Pre-defined expert answers for common questions
    # These are synthesized from transcript analysis

    if any(word in question_lower for word in ['title', 'tytuł', 'tytul']):
        return generate_title_advice(question)

    elif any(word in question_lower for word in ['bullet', 'point', 'punkty', 'zalety']):
        return generate_bullet_advice(question)

    elif any(word in question_lower for word in ['backend', 'search terms', 'hidden keywords']):
        return generate_backend_advice(question)

    elif any(word in question_lower for word in ['ranking', 'rankować', 'rankowanie', 'a9']):
        return generate_ranking_advice(question)

    elif any(word in question_lower for word in ['ppc', 'ads', 'reklamy', 'sponsored']):
        return generate_ppc_advice(question)

    elif any(word in question_lower for word in ['launch', 'start', 'nowy produkt']):
        return generate_launch_advice(question)

    elif any(word in question_lower for word in ['images', 'zdjęcia', 'photo', 'visual']):
        return generate_images_advice(question)

    elif any(word in question_lower for word in ['conversion', 'konwersja', 'ctr', 'click']):
        return generate_conversion_advice(question)

    else:
        # WHY: For other questions, search transcripts and provide contextual answer
        return search_and_answer(question)


def generate_title_advice(question: str) -> str:
    """Generate expert advice about Amazon title optimization."""
    return """## 📝 Optymalizacja Tytułu Amazon

**Najważniejsze zasady:**

1. **EXACT Match Phrases** - Amazon A9 preferuje dokładne frazy
   - Użytkownik szuka: "bamboo cutting board"
   - Lepiej: "Bamboo Cutting Board" (exact match)
   - Gorzej: "Board for Cutting Made of Bamboo" (separated)

2. **Długość 150-200 znaków** - maksymalne wykorzystanie
   - Aggressive mode: 190-199 znaków (7-9 EXACT phrases)
   - Standard mode: 140-150 znaków (3-4 EXACT phrases)

3. **Struktura tytułu:**
   ```
   Brand - Product Type - Key Features - Main Benefits
   ```
   Przykład:
   ```
   HAG EXPRESS - Bamboo Cutting Board Set - Large Wood Chopping Board - Kitchen Cutting Boards Wooden - Non-Slip Feet - Juice Groove
   ```

4. **Kolejność fraz** według priorytetu:
   - Najważniejsze frazy na początku (po brandzie)
   - High-volume keywords przed long-tail
   - Root keywords przed modifiers

5. **Co UNIKAĆ:**
   - Promotional words (best, #1, sale, cheap, discount)
   - Repetition >2× tego samego słowa
   - Subjective claims (amazing, perfect, revolutionary)
   - ALL CAPS (poza brand name)

6. **Advanced tips:**
   - Umieść top 3 keywords z Data Dive w pierwszych 80 znakach
   - Użyj hyphens (-) dla czytelności, nie pipes (|)
   - Jeśli masz warianty (color, size), umieść podstawowy typ pierwszego

**Amazon rankuje tytuły na podstawie:**
- EXACT match frequency (ile dokładnych fraz)
- Keyword relevance (czy frazy są w top 200)
- Character utilization (95%+ = lepiej niż 70%)

System automatycznie tworzy tytuły według tych zasad (tryb Aggressive = 7-9 EXACT phrases)."""


def generate_bullet_advice(question: str) -> str:
    """Generate expert advice about bullet points."""
    return """## 🔹 Bullet Points - Best Practices

**Struktura każdego punktu:**
```
✓ BENEFIT - Feature description with keywords naturally integrated
```

**5 punktów - kolejność według wagi:**

1. **Punkt #1 - Main Benefit + USP**
   - Najważniejsza zaleta produktu
   - Include top tier-2 keywords
   - Przykład: "✓ PREMIUM QUALITY – Made from sustainably sourced bamboo wood, featuring natural antibacterial properties for safe food preparation"

2. **Punkt #2 - Secondary Benefit**
   - Druga najważniejsza cecha
   - Przykład: "✓ PERFECT SIZE – Large 18x12" cutting surface ideal for meal prep, chopping vegetables, slicing meat, cheese boards"

3. **Punkt #3 - Practical Use Case**
   - Jak konkretnie używać produktu
   - Przykład: "✓ VERSATILE USE – Perfect for kitchen cutting board, serving board, charcuterie board, or cheese board for entertaining guests"

4. **Punkt #4 - Durability/Longevity**
   - Trwałość, easy care, maintenance
   - Przykład: "✓ EASY CARE – Hand wash with mild soap, apply mineral oil monthly to maintain beauty and prevent cracking"

5. **Punkt #5 - Guarantee/Gift Idea**
   - Warranty, gift idea, satisfaction guarantee
   - Przykład: "✓ PERFECT GIFT – Ideal for weddings, housewarmings, holidays. 100% satisfaction guaranteed or money back"

**Długość punktów:**
- Minimum: 120 znaków każdy
- Maximum: 200 znaków każdy (Amazon limit: 250-500 zależnie od kategorii)
- Średnio: 140-160 znaków = optimal

**Keyword integration:**
- 8-12 relevant keywords na punkt
- Natural language (nie keyword stuffing)
- Tier 2 keywords (te co NIE są w tytule)
- ≤5× repetition rule (nie powtarzaj słowa >5 razy w całych bullets)

**Co DZIAŁA:**
- Benefits-focused (nie features-focused)
- Specific numbers (18x12", 3/4" thick, 2-year warranty)
- Use cases i scenarios (meal prep, entertaining, gift)
- Sensory words (smooth, natural, beautiful, safe)

**Co UNIKAĆ:**
- Promotional words (best, sale, #1, cheap)
- Subjective claims (amazing, revolutionary)
- Medical claims (cures, treats, prevents disease)
- Comparison z konkurentami (better than X)

**Format:**
- Emojis: ✓ dozwolone (Amazon akceptuje)
- ALL CAPS: Tylko dla nagłówka benefitu
- Numeracja: Dozwolona (1. 2. 3.) ale nie zawsze potrzebna

System automatycznie generuje 5 punktów według tych zasad."""


def generate_backend_advice(question: str) -> str:
    """Generate expert advice about backend search terms."""
    return """## 🔧 Backend Search Terms - Maksymalizacja Rankingu

**Amazon Backend Limit:**
- 249 bajtów (niektóre kategorie: 250 bytes)
- ~40-50 słów (zależnie od długości)
- Liczy się każdy bajt (niektóre znaki = 2 bajty)

**Strategia optymalizacji:**

1. **CO UMIESZCZAĆ w backend:**
   - Keywords które NIE są w title/bullets (no duplicates!)
   - Synonyms (cutting board = chopping board)
   - Misspellings (bambo, cuttingboard, cuting bord)
   - Abbreviations (lg, xlg, xl, med)
   - Alternative spellings (color vs colour)
   - Long-tail phrases z dobrym wolumenem

2. **CO NIE umieszczać:**
   - Keywords już użyte w title/bullets (duplikaty nie pomagają!)
   - Brand names (Twoja marka już jest)
   - Competitor brands (zakazane przez Amazon)
   - Temporary words (sale, new, discount)
   - Punctuation (przecinki, kropki, cudzysłowy)

3. **Format:**
   ```
   word1 word2 word3 long tail phrase word4 word5
   ```
   - TYLKO SPACJE (bez przecinków!)
   - Lowercase (Amazon robi case-insensitive sam)
   - Kolejność nie ma znaczenia (Amazon permutuje)
   - Frazy mogą być rozdzielone (Amazon dopasuje permutacje)

4. **Greedy Packing Algorithm:**
   - System użyje tego co daje MAX coverage
   - Priorytet: Wysokie Search Volume + NIE w title/bullets
   - Target: 240-249 bajtów (96-99% utilization)

5. **Advanced tips:**
   - Użyj singular + plural (board boards)
   - Dodaj color variations (natural bamboo wood)
   - Include size variants (large extra large xl)
   - Misspellings są OK (często szukane!)

**Ranking impact:**
Backend search terms = 20-30% rankingowej mocy (title = 50-60%, bullets = 15-20%)

**Co robi system:**
- Wybiera keywords z najwyższym Search Volume
- Eliminuje duplikaty (porównuje z title/bullets)
- Pakuje używając greedy algorithm
- Target: 240-249 bajtów (96-99%)
- ≤5× repetition per word (anti-spam)

**Testowanie:**
- Możesz przetestować frazy wyszukując je w Amazon
- Jeśli Twój produkt NIE pokazuje się = fraza nieindeksowana
- Poczekaj 24-48h po updacie backend search terms"""


def generate_ranking_advice(question: str) -> str:
    """Generate expert advice about Amazon A9 ranking."""
    return """## 🚀 Amazon A9 Algorithm - Jak Rankować Wyżej

**A9 = Amazon Search Engine**

**3 główne filary rankingu:**

### 1. RELEVANCE (Trafność) - 40-50% wagi
**Co Amazon sprawdza:**
- Czy Twój listing zawiera szukane keywords?
- Czy keywords są w title? (50-60% wagi relevance)
- Czy keywords są w bullets? (15-20% wagi)
- Czy keywords są w backend? (20-30% wagi)

**Jak zwiększyć Relevance:**
✅ Optymalizacja listingu (tytuł, bullets, backend)
✅ EXACT match phrases w tytule (priorytet #1)
✅ Pokrycie top 200 keywords (73-98% = optimal)
✅ Natural keyword integration (nie stuffing)

### 2. PERFORMANCE (Wydajność) - 40-50% wagi
**Co Amazon mierzy:**
- **Velocity** - ile sprzedaży / dzień (najważniejsze!)
- **Conversion Rate** - % odwiedzających którzy kupują
- **Unit Session Percentage** - sessions/purchases ratio
- **Reviews** - liczba + rating (4.5+ stars = optimal)

**Jak zwiększyć Performance:**
✅ Launch strategy z velocity push (promo, giveaways)
✅ PPC campaigns (Sponsored Products) dla traffic
✅ Images quality (6-9 images, lifestyle, infographics)
✅ Competitive pricing (price wars = race to bottom, ale…)
✅ Review generation (follow-up emails, inserts)

### 3. CUSTOMER BEHAVIOR (Zachowanie) - 10-20% wagi
**Co Amazon obserwuje:**
- **CTR (Click-Through Rate)** - % ludzi klikających na listing
- **Time on Page** - jak długo oglądają
- **Cart Adds** - dodawanie do koszyka
- **Wishlist Adds** - dodawanie do wishlisty

**Jak zwiększyć Behavior signals:**
✅ Main image quality (white background, lifestyle)
✅ Price competitive z best-sellerami
✅ Prime badge (FBA)
✅ Reviews visible (social proof)
✅ Title optimization (przyciąga clicks)

---

## 🎯 Ranking Timeline (Nowy produkt)

**Dni 1-7: Launch Phase**
- Amazon "testuje" Twój produkt
- Potrzebujesz velocity (10-30 sprzedaży/dzień)
- PPC aggressive bidding
- Possible promotions (coupons, lightning deals)

**Dni 8-30: Stabilization**
- Ranking zaczyna się stabilizować
- Continue PPC (lower bids)
- Focus na reviews (10-20 reviews = tipping point)
- Monitor BSR (Best Seller Rank)

**Dni 30+: Optimization**
- Organic traffic increases
- Reduce PPC spend (if organic strong)
- Test price optimization
- Add A+ Content

---

## 💡 Pro Tips dla Wysokiego Rankingu

**Velocity = King:**
- 10 sprzedaży/dzień przez 7 dni > 70 sprzedaży w 1 dzień
- Consistency matters (algorytm preferuje steady velocity)

**Competition Analysis:**
- Check top 10 competitors (Helium 10 Cerebro)
- See what keywords they rank for
- Analyze their velocity (sales estimator tools)

**Honeymoon Period:**
- Pierwsze 30 dni = najważniejsze
- Amazon daje "boost" nowym produktom
- Maximize sales w tym okresie

**Long-term:**
- Listing optimization = ongoing
- Update keywords co 3-6 miesięcy
- Monitor competitors monthly
- Add seasonal keywords (holiday, summer, etc.)

System automatycznie optymalizuje Relevance (filar #1).
Performance i Behavior = Twoja praca (velocity, PPC, images)."""


def generate_ppc_advice(question: str) -> str:
    """Generate expert advice about Amazon PPC."""
    return """## 💰 Amazon PPC - Strategia Reklamowa

**3 typy kampanii:**

### 1. SPONSORED PRODUCTS (Auto + Manual)

**Auto Campaign (Start here):**
- Amazon automatically targets keywords
- Dobre dla research (co działa?)
- Budget: $10-20/dzień na start
- Run przez 2-3 tygodnie
- Harvest winning keywords → przenieś do manual

**Manual Campaign - Exact Match:**
- Targetuj specific keywords (top 10-20 z Data Dive)
- Bid higher (aggressive)
- Cel: Rankować na top keywords
- Budget: $20-50/dzień

**Manual Campaign - Phrase Match:**
- Broader targeting
- Discover long-tail keywords
- Lower bids
- Budget: $10-20/dzień

**Manual Campaign - Broad Match:**
- Bardzo szerokie targetowanie
- Discovery mode
- Lowest bids
- Budget: $5-10/dzień

### 2. SPONSORED BRANDS (Brand campaigns)
- Wymaga Brand Registry
- Shows logo + 3 products
- Premium placement (top of search)
- Higher CPC ale lepszy ROAS
- Budget: $30-50/dzień

### 3. SPONSORED DISPLAY (Retargeting)
- Pokazuje reklamy na product pages
- Retarget people who viewed Twój listing
- Audience targeting
- Budget: $10-20/dzień

---

## 📊 Bidding Strategy

**Launch Phase (Dni 1-30):**
- Bid aggressive (top of search)
- Suggested bid × 1.5-2.0
- Cel: Velocity + reviews
- ACoS: 40-60% OK (building stage)

**Growth Phase (Dni 30-90):**
- Optimize bids based na data
- Target ACoS: 25-35%
- Pause high-ACoS keywords
- Increase bids na profitable keywords

**Mature Phase (90+ dni):**
- Target ACoS: 15-25%
- Focus na ROAS (Return on Ad Spend)
- Mostly exact match campaigns
- Reduce/eliminate auto campaigns

---

## 🎯 ACoS Optimization

**Formuła:**
```
ACoS = (Ad Spend / Sales) × 100%
```

**Target ACoS by Stage:**
- Launch: 40-70% (OK to lose money)
- Growth: 25-40%
- Maturity: 15-25%
- Profitability: <20%

**Break-even ACoS:**
```
Break-even ACoS = Profit Margin %
```
Przykład: 30% margin = 30% ACoS = break-even

**How to Lower ACoS:**
✅ Pause keywords z ACoS >50%
✅ Increase bids na keywords z ACoS <20% (scaling winners)
✅ Add negative keywords (co nie konwertuje)
✅ Improve listing (lepszy listing = wyższy CVR = niższy ACoS)

---

## 💡 Pro PPC Tips

**Dayparting:**
- Run ads tylko gdy konwersja jest wysoka
- Check hourly data (Amazon Attribution)
- Pause overnight jeśli konwersja niska

**Placement Modifiers:**
- Top of Search: +50-100% bid (highest conversion)
- Product Pages: +20-50% bid
- Rest of Search: -20% bid

**Negative Keywords:**
- Add keywords które dostają clicks ale 0 sales
- Przykład: "free cutting board", "cheap cutting board", "used"

**Campaign Structure:**
1. Auto campaign (discovery)
2. Exact match (top 10 keywords)
3. Phrase match (long-tail)
4. Product Targeting (competitor ASINs)

**Budget Allocation:**
- 40% Exact match (best ROI)
- 30% Auto (discovery)
- 20% Phrase match
- 10% Broad match / Display

**Keyword Harvesting:**
- Co 2 tygodnie: Check Auto Campaign search terms
- Winning keywords (ACoS <30%) → move to Exact Match
- Losing keywords → add as negative

System nie zarządza PPC automatycznie, ale listing optimization pomaga obniżyć ACoS (lepszy listing = wyższa konwersja = niższy ACoS)."""


def generate_launch_advice(question: str) -> str:
    """Generate expert advice about product launches."""
    return """## 🚀 Product Launch Strategy - Pierwsze 30 Dni

**Launch = Most Critical Period**
Amazon daje "honeymoon period" nowym produktom (pierwsze 30 dni).

---

## 📋 PRE-LAUNCH Checklist (2-4 tygodnie przed)

**1. Listing Optimization:**
✅ Title 190-199 znaków (7-9 EXACT phrases)
✅ Bullets zoptymalizowane (5 punktów, benefits-focused)
✅ Backend search terms (240-249 bajtów)
✅ Description compelling (3 paragrafy)
✅ A+ Content (jeśli masz Brand Registry)

**2. Images:**
✅ Main image white background (Amazon requirements)
✅ 6-9 total images (lifestyle, infographics, use cases)
✅ High resolution (2000x2000 pixels minimum)
✅ Lifestyle images showing product in use

**3. Pricing:**
✅ Competitive analysis (top 10 competitors)
✅ Price 5-10% below average = sweet spot
✅ Calculate break-even ACoS

**4. Reviews Strategy:**
✅ Amazon Vine (jeśli masz Brand Registry) - 5-10 reviews przed launch
✅ Friends & family (bądź ostrożny - Amazon TOS)
✅ Follow-up email sequence ready

---

## 🎯 LAUNCH Week (Dni 1-7)

**Goal: VELOCITY (10-30 sprzedaży/dzień)**

**Day 1:**
- Launch PPC campaigns:
  - Auto campaign ($20/dzień)
  - Exact match top 10 keywords ($30/dzień)
- Set aggressive bids (suggested × 1.5)
- Monitor hourly (first 24h critical)

**Days 2-3:**
- Check PPC performance
- Adjust bids up dla winning keywords
- Add negative keywords (jeśli spam clicks)

**Days 4-7:**
- Lightning Deal (jeśli dostępne) = boost velocity
- Coupons (10-20% off) = increase CTR
- Influencer outreach (jeśli masz budżet)
- Request reviews (Amazon "Request Review" button)

**Target Metrics:**
- 10-30 sprzedaży/dzień
- ACoS: 40-70% (OK to lose money during launch)
- BSR: Top 10,000 w kategorii (cel: top 5,000)

---

## 📈 WEEK 2-4 (Stabilization)

**Goal: CONSISTENCY + REVIEWS**

**Velocity:**
- Maintain 10-30 sprzedaży/dzień (consistency > peaks)
- Continue PPC (możesz obniżyć bids trochę)
- Add Sponsored Brand campaign (jeśli Brand Registry)

**Reviews:**
- Target: 10-20 reviews do końca miesiąca
- Use "Request Review" button (48-72h po delivery)
- Monitor review rating (jeśli <4.5 stars = problem)

**Optimization:**
- Check Search Query Report (co działa w PPC?)
- Harvest winning keywords → dodaj do Exact Match
- Pause/lower bids na high-ACoS keywords

**Ranking Check:**
- Sprawdź ranking dla top 10 keywords (Helium 10 Keyword Tracker)
- Cel: Top 20 dla 3-5 głównych keywords

---

## 🎪 Launch Tactics (Velocity Hacks)

**1. Amazon Coupons:**
- 10-20% off
- Shows in search results ("Save 15%")
- Increases CTR by 20-40%

**2. Lightning Deals:**
- Prime Day, Cyber Monday, Black Friday
- Massive velocity boost (100-500 units w 4-6h)
- Wymaga inventory (min. 100-200 units)

**3. Promotions:**
- Buy One Get One (BOGO)
- Percentage Off (15-30%)
- Shows badge in search results

**4. External Traffic:**
- Facebook Ads → Amazon listing
- Influencer marketing (YouTube, Instagram)
- Email list (jeśli masz)
- Amazon Attribution (track external sources)

**5. Competitor Conquesting:**
- Product Targeting campaigns (PPC)
- Target bestseller ASINs (Twoi konkurenci)
- Show reklamy na ich product pages

---

## 📊 Launch Metrics to Track

**Daily:**
- Units sold (velocity)
- PPC spend i ACoS
- Ranking changes (top 10 keywords)
- BSR (Best Seller Rank)

**Weekly:**
- Review count + rating
- Conversion rate (units / sessions)
- PPC ROAS (Return on Ad Spend)
- Inventory levels

**Monthly:**
- Total revenue
- Total profit (after PPC, fees, COGS)
- TACoS (Total ACoS = PPC spend / total sales)
- Organic vs PPC ratio

---

## ⚠️ Common Launch Mistakes

**❌ Insufficient inventory:**
- Launch z 50 units = runs out w 3 dni = momentum dead
- Minimum: 500-1,000 units dla proper launch

**❌ Too low PPC budget:**
- $10/dzień = nie starcza dla velocity
- Minimum: $50/dzień przez 30 dni = $1,500 total

**❌ Bad images:**
- Low quality images = low CTR = low velocity
- Invest in professional photography

**❌ Waiting for organic:**
- "Let's see if it works" = fail
- Musisz aggressive push pierwsze 30 dni

**❌ Ignoring reviews:**
- 0 reviews przez 2 tygodnie = red flag dla buyers
- Use Amazon Vine jeśli możliwe (5-10 reviews przed launch)

---

## ✅ Launch Success Checklist

Do końca 30 dni powinieneś mieć:
- ✅ 10-20 reviews (4.5+ stars średnia)
- ✅ Ranking top 20 dla 3-5 main keywords
- ✅ BSR <10,000 (cel: <5,000)
- ✅ Consistent 10-30 sprzedaży/dzień
- ✅ ACoS dropping (40% → 30%)
- ✅ Organic sales starting (20-30% organic)

System optymalizuje listing (filar #1), ale launch success = velocity + PPC + reviews (musisz zainwestować!)."""


def generate_images_advice(question: str) -> str:
    """Generate expert advice about Amazon images."""
    return """## 🖼️ Amazon Images - Visual Optimization

**Amazon allows 9 images (use 6-9 = optimal)**

---

## 📸 Image Slots Strategy

**Image #1 - MAIN IMAGE (Most Important!):**
- White background (RGB 255, 255, 255) - WYMAGANE przez Amazon
- Product fills 85% of frame
- High resolution (2000×2000 minimum, 2500×2500 optimal)
- Professional lighting (no shadows)
- Front view / most appealing angle
- **WHY:** Main image = 80% CTR determinant

**Image #2 - LIFESTYLE IMAGE:**
- Product in use (real-life scenario)
- Person using product (if applicable)
- Kitchen setup, dining table, etc.
- Shows scale/size
- **WHY:** Helps buyer visualize ownership

**Image #3 - INFOGRAPHIC #1 (Benefits):**
- 3-5 key benefits listed
- Icons + short text
- High contrast text (readable thumbnails)
- Brand colors
- **WHY:** Communicates value at glance

**Image #4 - INFOGRAPHIC #2 (Features):**
- Measurements/dimensions
- Materials & construction
- Technical specs
- Comparison chart (sizes/variants)
- **WHY:** Answers technical questions

**Image #5 - DETAIL/CLOSE-UP:**
- Zoom in na texture, quality, craftsmanship
- Shows premium feel
- Material close-up (wood grain, stitching, etc.)
- **WHY:** Builds trust in quality

**Image #6 - PACKAGING/GIFT:**
- Product in box (if premium packaging)
- Gift-ready presentation
- Unboxing experience
- **WHY:** Triggers gift purchases

**Image #7 - USE CASE #2:**
- Alternative use case
- Different scenario
- Bundle/ set display (if applicable)
- **WHY:** Expands perceived utility

**Image #8-9 - OPTIONAL:**
- Customer reviews showcase
- Warranty/guarantee badge
- Size comparison
- Color/variant options

---

## 🎨 Design Best Practices

**Resolution:**
- Minimum: 1000×1000 pixels
- Recommended: 2000×2000 pixels
- Optimal: 2500×2500 pixels
- **WHY:** Enables zoom function (increases conversion 10-15%)

**Format:**
- JPEG or PNG
- RGB color mode
- File size <10MB
- **No:** CMYK, transparency on main image

**Composition:**
- Rule of thirds
- Clean, uncluttered
- High contrast
- Readable at thumbnail size (100×100 pixels)

**Text on Images:**
- Large font (minimum 40pt)
- High contrast (black on white, white on dark)
- Maximum 3-5 words per line
- Sans-serif fonts (Arial, Helvetica)
- **WHY:** Mobile viewing (60%+ traffic)

---

## 💡 Advanced Image Tactics

**A/B Testing:**
- Test different main images (Amazon Manage Your Experiments)
- Lifestyle vs white background
- Angle variations
- Track CTR changes

**Video (Image slot #1 or #2):**
- 15-30 seconds optimal
- Shows product in use
- Increases conversion 5-10%
- Wymaga Brand Registry

**360° View:**
- Spin feature (dostępne w niektórych kategoriach)
- Shows all angles
- Premium feel

**Infographic Elements:**
✅ Benefits icons (checkmarks, stars)
✅ Badges (BPA-free, FDA approved, Made in USA)
✅ Trust signals (warranty, guarantee)
✅ Measurements with visuals
✅ Before/after (jeśli applicable)

---

## 📊 Image Performance Metrics

**Click-Through Rate (CTR):**
- Good main image: 0.5-1.5% CTR
- Bad main image: <0.3% CTR
- **Impact:** Doubling CTR = 50%+ sales increase

**Conversion Rate:**
- 6+ images: 15-25% conversion
- 3-5 images: 10-15% conversion
- 1-2 images: 5-10% conversion

**Mobile Optimization:**
- 60%+ users browse on mobile
- Test images on phone (small screen)
- Text readable? Main benefits visible?

---

## ⚠️ Common Image Mistakes

**❌ Main image violations:**
- Colored background (must be pure white!)
- Accessories in frame (show ONLY product)
- Text/graphics on main image (forbidden!)
- Borders, watermarks, logos
- **Result:** Listing suppression by Amazon

**❌ Low resolution:**
- <1000×1000 = no zoom function
- Blurry thumbnails
- Looks unprofessional

**❌ Too much text:**
- Infographics unreadable
- Cluttered design
- Information overload

**❌ Inconsistent branding:**
- Different styles across images
- No cohesive look
- Looks amateurish

**❌ No lifestyle images:**
- Only white background shots
- Can't visualize product in use
- Kills emotional connection

---

## ✅ Image Checklist

Before uploading:
- ✅ Main image: Pure white background (255,255,255)
- ✅ All images: 2000×2000+ resolution
- ✅ Mix of lifestyle + infographics (3-4 lifestyle, 2-3 infographics)
- ✅ Text readable at thumbnail size
- ✅ Mobile-friendly (test on phone!)
- ✅ Zoom enabled (2000×2000+)
- ✅ 6-9 images total (więcej = lepiej)
- ✅ Professional quality (no smartphone snapshots)

**ROI na images:**
Professional photoshoot ($300-800) = 20-50% conversion increase = $1000s dodatkowego revenue.

Images = pierwsze wrażenie. Bad images = instant pass. Great images = instant trust."""


def generate_conversion_advice(question: str) -> str:
    """Generate expert advice about conversion optimization."""
    return """## 📈 Conversion Rate Optimization (CRO)

**Conversion Rate = (Orders / Sessions) × 100%**

**Industry Benchmarks:**
- Good: 10-15%
- Great: 15-20%
- Excellent: 20%+

---

## 🎯 Conversion Rate Drivers (w kolejności wagi)

### 1. IMAGES (30-40% wpływu)
- Main image quality = CTR determinant
- 6-9 images = optimal
- Lifestyle + infographics mix
- **Quick win:** Add 3+ high-quality images

### 2. PRICE (25-30% wpływu)
- Sweet spot: 5-10% below average
- Psychological pricing ($19.97 vs $20.00)
- Prime badge (FBA)
- **Quick win:** Test $X.97 or $X.99 endings

### 3. REVIEWS (20-25% wpływu)
- 10+ reviews = tipping point
- 4.5+ stars = must have
- Recent reviews (last 30 days)
- **Quick win:** Request reviews (Amazon button)

### 4. TITLE (10-15% wpływu)
- Clear, descriptive
- Includes main keywords
- Readable (nie keyword stuffing)
- **Quick win:** First 80 chars most important

### 5. BULLETS (5-10% wpływu)
- Benefits-focused
- Easy to scan
- Addresses objections
- **Quick win:** Lead with benefits not features

---

## 🛒 Buyer Psychology

**Decision Process:**
1. **Search** → sees thumbnail (main image)
2. **Click** → reads title + price + reviews
3. **Scan** → scrolls images + bullets
4. **Evaluate** → reads description + reviews
5. **Convert** → clicks "Add to Cart"

**Where buyers drop off:**
- Step 2: Bad main image (no click)
- Step 3: Price too high (close tab)
- Step 4: Bad reviews / no reviews (don't trust)
- Step 5: Missing info / unclear benefits (uncertain)

---

## 📊 Conversion Optimization Tactics

**TRUST SIGNALS:**
✅ 10+ reviews (social proof)
✅ 4.5+ stars (quality signal)
✅ Prime badge (fast shipping)
✅ Amazon's Choice badge (algorithm trust)
✅ Brand name (recognition)
✅ Badges in images (FDA approved, BPA-free, etc.)

**CLARITY:**
✅ Clear product name (tytuł)
✅ Obvious benefits (bullets)
✅ Size/dimensions visible (images + bullets)
✅ What's included (infographic)
✅ Use cases clear (lifestyle images)

**URGENCY:**
✅ Limited time coupon (10% off)
✅ Low stock warning (Amazon automatic)
✅ Deal badge (Lightning Deal)
✅ Prime Day / Black Friday special

**RISK REVERSAL:**
✅ Money-back guarantee (bullet #5)
✅ Warranty info (bullet #4)
✅ Easy returns (Amazon FBA = automatic)
✅ "100% Satisfaction" language

---

## 🧪 A/B Testing Strategy

**Test in this order (highest impact first):**

**Test #1: Main Image**
- Lifestyle vs white background
- Different angle
- Props vs no props
- Run 2-4 weeks (Amazon Manage Your Experiments)

**Test #2: Price**
- $19.99 vs $19.97 vs $18.99
- 1 week tests (price sensitive)
- Monitor conversion + profitability

**Test #3: Title**
- Different keyword order
- Length (150 vs 190 chars)
- Brand placement

**Test #4: A+ Content**
- Different layouts
- Story-focused vs feature-focused
- Longer vs shorter

---

## 📱 Mobile Optimization

**60%+ traffic = mobile**

**Mobile-specific checks:**
✅ Main image clear at thumbnail (100×100)
✅ Title readable (first 80 chars)
✅ Price prominent
✅ Bullets scannable (not walls of text)
✅ Images text large enough (40pt+ font)
✅ No tiny details (zoom required)

**Mobile vs Desktop conversion:**
- Desktop: 12-18% typical
- Mobile: 8-12% typical
- **Why lower:** Smaller screen, less detail, distractions

---

## 🚀 Quick Wins (Do Today)

**1. Request Reviews (5 minutes):**
- Go to Orders → Request Review button
- Do for all orders 5-30 days old
- Increases reviews 10-20%

**2. Add Coupon (10 minutes):**
- 10% off coupon
- Shows in search results
- Increases CTR 20-40%

**3. Check Main Image (15 minutes):**
- Is it best angle?
- Professional quality?
- A/B test if unsure

**4. Update Bullets (30 minutes):**
- Lead with benefits (not features)
- Add use cases
- Address common questions

**5. Add Images (1-2 hours):**
- Get to 6-9 images minimum
- Add lifestyle shots
- Add infographic with benefits

---

## 📉 Conversion Rate Drop - Troubleshooting

**Sudden CR drop? Check:**

**1. Competitor price changes:**
- They dropped price by 20%? You need to match or differentiate
- Solution: Check top 10 competitors weekly

**2. Bad review added:**
- 1-star review with photo = kills conversion
- Solution: Respond professionally, fix issue, request more reviews

**3. Images removed:**
- Amazon sometimes removes images (TOS violation)
- Solution: Check image compliance, re-upload

**4. Out of stock variant:**
- Main variant OOS = buyers see higher-priced variant
- Solution: Monitor inventory, restock before 0

**5. Seasonal decline:**
- "Cutting boards" searches drop 40% in summer
- Solution: Seasonal PPC adjustments, promotions

---

## 🎯 Target Conversion Rates by Stage

**Launch (0-30 days):**
- Target: 10-15%
- Focus: Reviews + images
- OK if lower (no social proof yet)

**Growth (30-90 days):**
- Target: 15-20%
- Focus: Optimization (test/iterate)
- Should improve monthly

**Mature (90+ days):**
- Target: 18-25%
- Focus: Maintain + competitive watch
- Slight decline normal (competition increases)

---

## 💡 Advanced CRO

**Amazon DSP (Display Ads):**
- Retarget visitors who didn't buy
- Increase conversion 5-10%
- Requires $35k+ spend

**Brand Store:**
- Custom landing page
- Showcase products line
- Increases brand perception

**Amazon Live:**
- Live streaming (like QVC)
- Show product in real-time
- Conversion 2-3× higher during live

**Subscribe & Save:**
- Recurring orders
- 5-15% discount
- Increases LTV (Lifetime Value)

System optimizes listing (images, bullets, title) ale conversion = całość (price, reviews, trust signals). Wszystko razem!"""


def search_and_answer(question: str) -> str:
    """
    Search transcripts and provide contextual answer.
    WHY: For questions not matching pre-defined patterns, search knowledge base.
    """
    # WHY: Search transcripts for relevant content
    results = search_transcripts(question, max_results=3)

    if not results:
        return """## 💬 Amazon Strategy - Potrzebuję Więcej Szczegółów

Nie znalazłem wystarczających informacji dla tego pytania. Spróbuj:

**Być bardziej konkretnym:**
- Zamiast "Jak sprzedawać?" → "Jak zoptymalizować tytuł produktu?"
- Zamiast "Co robić?" → "Jak zwiększyć ranking przez PPC?"

**Przykładowe pytania na które mogę odpowiedzieć:**
- "Jak zoptymalizować tytuł Amazon?"
- "Jaka strategia PPC dla nowego produktu?"
- "Jak zwiększyć conversion rate?"
- "Backend search terms best practices?"
- "Jak rankować wyżej w A9?"
- "Product launch strategy?"
- "Jak robić dobre zdjęcia produktu?"

Możesz też zapytać po angielsku."""

    # WHY: Synthesize answer from transcript excerpts
    answer = "## 💡 Amazon Strategy - Odpowiedź\n\n"
    answer += "Na podstawie proven Amazon strategies:\n\n"

    # WHY: Extract key insights from top results
    for i, result in enumerate(results[:2], 1):
        snippet = result['snippet']
        # WHY: Clean up snippet (remove markdown, excessive whitespace)
        snippet = re.sub(r'#+\s', '', snippet)  # Remove markdown headers
        snippet = re.sub(r'\s+', ' ', snippet).strip()  # Normalize whitespace
        snippet = snippet[:400]  # Limit length
        # WHY: CRITICAL - filter out any course/instructor/source references
        snippet = filter_source_references(snippet)

        answer += f"**Insight #{i}:**\n{snippet}...\n\n"

    answer += """---

**Zastosuj te strategie:**
1. Zaimplementuj krok po kroku
2. Testuj i mierz wyniki
3. Iteruj na podstawie danych

Potrzebujesz więcej szczegółów? Zapytaj konkretniej!"""

    return answer


def get_welcome_message() -> str:
    """Get welcome message for chat interface."""
    return """# 🤖 AI Amazon Strategy Assistant

Witaj! Jestem Twoim ekspertem Amazon strategy.

**Mogę pomóc z:**
- 📝 Optymalizacja listingów (title, bullets, backend)
- 🚀 Amazon A9 ranking strategies
- 💰 PPC campaigns & ACoS optimization
- 🖼️ Images & conversion optimization
- 🎯 Product launch strategies
- 📊 Competitor analysis

**Przykładowe pytania:**
- "Jak zoptymalizować tytuł Amazon?"
- "Jaka strategia PPC dla launch?"
- "Jak zwiększyć conversion rate?"
- "Backend search terms tips?"
- "Product launch checklist?"

Pytaj po polsku lub angielsku! 🇵🇱🇬🇧"""
