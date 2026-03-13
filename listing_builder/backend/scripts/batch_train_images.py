# backend/scripts/batch_train_images.py
# Purpose: Batch training — 5000+ A+ Content generations on Beast to optimize prompts
# NOT for: Production serving or API endpoints
# Run ON Beast: python3 batch_train_images.py

import json
import random
import time
import re
import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# WHY: Run inside lbp-backend Docker container on grzegorz152 — has Groq keys
# Usage: docker exec lbp-backend python3 /app/scripts/batch_train_images.py 5000
MODE = os.environ.get("TRAIN_MODE", "groq")  # "groq" (fast, cloud) or "beast" (local)
OLLAMA_URL = "http://localhost:11434/api/chat"
BEAST_MODEL = "qwen3:8b"
OUTPUT_DIR = Path("/tmp/training_data/aplus_content")
RESULTS_FILE = OUTPUT_DIR / "results.jsonl"
STATS_FILE = OUTPUT_DIR / "stats.json"

# WHY: Diverse product catalog covering many Amazon categories
# Each entry = (category, products list with name/brand/bullets)
PRODUCT_CATALOG = [
    ("Elektronika", [
        {"name": "Sluchawki bezprzewodowe ANC Pro 500", "brand": "SoundMax", "bullets": ["Redukcja szumow ANC -42dB", "Bluetooth 5.3 LDAC", "Bateria 60h", "Skladana konstrukcja"]},
        {"name": "Powerbank 20000mAh PD 65W", "brand": "ChargePro", "bullets": ["USB-C PD 65W", "Ladowanie laptopa", "Wyswietlacz LED", "Obudowa aluminiowa"]},
        {"name": "Kamera sportowa 4K 60fps", "brand": "ActionCam", "bullets": ["Stabilizacja 6-osiowa", "Wodoszczelnosc 10m", "WiFi + Bluetooth", "Szerokokatny 170 stopni"]},
        {"name": "Router WiFi 6E AX6000", "brand": "NetSpeed", "bullets": ["Tri-band 6GHz", "8 anten MIMO", "Pokrycie 300m2", "WPA3 szyfrowanie"]},
        {"name": "Monitor 27 cali 4K IPS", "brand": "ViewPro", "bullets": ["100% sRGB", "HDR400", "USB-C 90W PD", "Regulowany stojak"]},
    ]),
    ("Sport i outdoor", [
        {"name": "Plecak turystyczny 65L", "brand": "Alpine Pro", "bullets": ["System nosny Airflow", "Wodoodporny 420D Nylon", "Pokrowiec przeciwdeszczowy", "Regulowany pas biodrowy"]},
        {"name": "Buty trekkingowe Gore-Tex", "brand": "MountainStep", "bullets": ["Membrana Gore-Tex", "Podeszwa Vibram", "Ochrona kostki", "Waga 480g"]},
        {"name": "Namiot 2-osobowy ultralight", "brand": "CampLite", "bullets": ["Waga 1.2kg", "Aluminiowe stelaże DAC", "Wodoodpornosc 3000mm", "Wolnostojacy"]},
        {"name": "Zegarek sportowy GPS", "brand": "RunPro", "bullets": ["GPS + GLONASS", "Pulsometr 24/7", "Wodoszczelnosc 10ATM", "Bateria 14 dni"]},
        {"name": "Mata do jogi premium 6mm", "brand": "YogaFlow", "bullets": ["Naturalny kauczuk", "Antypoślizgowa", "Ekologiczna", "Pasek do noszenia"]},
    ]),
    ("Dom i kuchnia", [
        {"name": "Robot kuchenny wielofunkcyjny 1200W", "brand": "CookMaster", "bullets": ["12 programow automatycznych", "Pojemnosc 3.5L", "Gotowanie na parze", "Wyswietlacz LCD"]},
        {"name": "Odkurzacz pionowy bezprzewodowy", "brand": "CleanPro", "bullets": ["Moc ssania 25kPa", "Bateria 60 min", "Filtr HEPA H13", "Podswietlenie LED"]},
        {"name": "Ekspres do kawy automatyczny", "brand": "CafeRoyal", "bullets": ["Mlynek ceramiczny", "System spieniania mleka", "15 barow cisnienia", "Zbiornik 1.8L"]},
        {"name": "Posciel bambusowa 200x220", "brand": "SleepWell", "bullets": ["100% bambus", "Hipoalergiczna", "Termoregulacja", "Certyfikat OEKO-TEX"]},
        {"name": "Zestaw nozy kuchennych 8 czesci", "brand": "SharpEdge", "bullets": ["Stal damascenska 67 warstw", "Rekojesc z drewna pakka", "Blok magnetyczny", "Twrdosc 60 HRC"]},
    ]),
    ("Uroda i zdrowie", [
        {"name": "Serum z witamina C 30ml", "brand": "SkinGlow", "bullets": ["20% witaminy C", "Kwas hialuronowy", "Witamina E", "Wegańska formuła"]},
        {"name": "Suszarka do wlosow jonowa 2200W", "brand": "HairPro", "bullets": ["Technologia jonowa", "3 stopnie temperatury", "Dysza koncentrujaca", "Waga 450g"]},
        {"name": "Masażer do karku z podgrzewaniem", "brand": "RelaxPro", "bullets": ["Masaz Shiatsu 4D", "Podgrzewanie IR", "3 intensywnosci", "Akumulator 2h"]},
        {"name": "Szczoteczka soniczna do zebow", "brand": "DentCare", "bullets": ["40000 wibracji/min", "5 trybow czyszczenia", "Timer 2 min", "2 koncowki w zestawie"]},
        {"name": "Olejek arganowy do wlosow 100ml", "brand": "NaturOil", "bullets": ["100% organiczny", "Tloczony na zimno", "Certyfikat Ecocert", "Butelka z pipeta"]},
    ]),
    ("Dziecko i zabawki", [
        {"name": "Fotelik samochodowy 0-36kg ISOFIX", "brand": "SafeRide", "bullets": ["Obrotowy 360 stopni", "ISOFIX + Top Tether", "Ochrona boczna", "Certyfikat i-Size R129"]},
        {"name": "Wozek spacerowy skladany", "brand": "BabyGo", "bullets": ["Skladany jedną ręką", "Waga 6.5kg", "Budka UPF50+", "Amortyzacja kol"]},
        {"name": "Klocki magnetyczne 100 elementow", "brand": "MagBuild", "bullets": ["Bezpieczne magnesy NdFeB", "Certyfikat CE EN71", "Rozne ksztalry i kolory", "Torba do przechowywania"]},
        {"name": "Monitor oddechu niemowlecia", "brand": "BabySafe", "bullets": ["Czujnik ruchu Piezo", "Alarm po 20s bez oddechu", "Zasieg 300m", "Kamera nocna HD"]},
        {"name": "Nosidlo ergonomiczne 0-20kg", "brand": "CarryBaby", "bullets": ["4 pozycje noszenia", "Pas biodrowy z kieszeniami", "Oddychajaca siatka", "Ochrona glowki"]},
    ]),
    ("Motoryzacja", [
        {"name": "Kamera samochodowa 4K WiFi GPS", "brand": "DashView", "bullets": ["Nagrywanie 4K 30fps", "GPS + tracker trasy", "Tryb parkingowy 24/7", "Noktowizja Sony IMX335"]},
        {"name": "Kompressor samochodowy 12V cyfrowy", "brand": "AirPump", "bullets": ["Cisnienie max 150 PSI", "Wyswietlacz cyfrowy", "Auto-stop", "Kabel 3m + adapter"]},
        {"name": "Pokrowce na fotele samochodowe", "brand": "AutoComfort", "bullets": ["Skora ekologiczna", "Kompatybilne z airbag", "Podgrzewane siedziska", "Uniwersalny rozmiar"]},
        {"name": "Ladowarka samochodowa USB-C 100W", "brand": "CarCharge", "bullets": ["Dual USB-C 100W", "GaN technologia", "Ladowanie laptopa", "Kompaktowa"]},
        {"name": "Organizer bagaznika samochodowego", "brand": "TrunkPro", "bullets": ["Skladany na plasko", "3 przegrody", "Wzmocnione sciany", "Uchwyty boczne"]},
    ]),
    ("Odziez i akcesoria", [
        {"name": "Kurtka puchowa meska 800 FP", "brand": "WinterPro", "bullets": ["Puch gesi 800 FP", "Wodoodporna powloka DWR", "Waga 350g", "Kaptur odpinany"]},
        {"name": "Buty biegowe z pianka EVA", "brand": "RunFlex", "bullets": ["Pianka EVA amortyzacja", "Oddychajaca siatka", "Podeszwa antypoślizgowa", "Waga 230g"]},
        {"name": "Plecak miejski antykradziezowy", "brand": "SafePack", "bullets": ["Ukryty zamek", "Port USB", "Wodoodporny material", "Kieszeh na laptop 15.6"]},
        {"name": "Portfel skorzany RFID block", "brand": "LeatherCraft", "bullets": ["Skora naturalna", "Blokada RFID/NFC", "12 slotow na karty", "Prezentowe opakowanie"]},
        {"name": "Okulary polaryzacyjne UV400", "brand": "SunShield", "bullets": ["Polaryzacja Cat.3", "Ochrona UV400", "Oprawki TR90", "Etui + sciereczka"]},
    ]),
    ("Narzedzia i majsterkowanie", [
        {"name": "Wiertarko-wkretarka akumulatorowa 20V", "brand": "ToolMax", "bullets": ["Moment obrotowy 60Nm", "2 biegi", "2 akumulatory 4Ah", "Oswietlenie LED"]},
        {"name": "Laser krzyzowy samopoziomujacy", "brand": "LaserPro", "bullets": ["Zasieg 30m", "Dokladnosc 1mm/5m", "Samopoziomowanie +/-4 stopnie", "Statyw w zestawie"]},
        {"name": "Zestaw kluczy nasadowych 216 czesci", "brand": "MechPro", "bullets": ["Chrom-wanad", "Nasadki 4-32mm", "Grzechotka 72 zeby", "Walizka aluminiowa"]},
        {"name": "Spawarka inwertorowa MMA 200A", "brand": "WeldPro", "bullets": ["Prąd spawania 20-200A", "Elektrody 1.6-4.0mm", "Hot Start + Arc Force", "Waga 4.5kg"]},
        {"name": "Dalmierz laserowy 100m Bluetooth", "brand": "MeasurePro", "bullets": ["Zasieg 100m", "Dokladnosc 1.5mm", "Bluetooth do telefonu", "Pomiar powierzchni/objetosci"]},
    ]),
    ("Zwierzeta", [
        {"name": "Karma sucha dla psa dorosłego 12kg", "brand": "PetNutrition", "bullets": ["70% mieso kurczak", "Bez zboz", "Probiotyki", "Omega 3+6"]},
        {"name": "Drapak dla kota z legowiskiem", "brand": "CatHouse", "bullets": ["Wysokosc 150cm", "Sznur sizalowy", "3 platformy", "Pluszowe legowisko"]},
        {"name": "Smycz automatyczna 8m dla psa", "brand": "WalkEasy", "bullets": ["Tasma 8m", "Do 50kg", "System hamowania", "Ergonomiczny uchwyt"]},
        {"name": "Fontanna dla kota 2.5L", "brand": "PetDrink", "bullets": ["Filtr weglowy 3-stopniowy", "Ultra cicha pompa", "Pojemnosc 2.5L", "Bezpieczne tworzywo"]},
        {"name": "Transporter dla psa skladany XL", "brand": "PetTravel", "bullets": ["Rozmiar 91x63x63cm", "Tkanina Oxford 600D", "3 wejscia", "Skladany na plasko"]},
    ]),
    ("Ogrod", [
        {"name": "Robot koszacy GPS RTK", "brand": "MowBot", "bullets": ["Nawigacja GPS RTK", "Powierzchnia do 2000m2", "Sterowanie WiFi/App", "Czujnik deszczu"]},
        {"name": "Lampa solarna ogrodowa LED 200W", "brand": "SunLight", "bullets": ["Panel solarny 25W", "Akumulator 30Ah", "Czujnik zmierzchu", "Pilot zdalny"]},
        {"name": "System nawadniania automatyczny", "brand": "AquaGarden", "bullets": ["16 stref", "WiFi sterowanie", "Czujnik wilgotnosci gleby", "Programator 7 dni"]},
        {"name": "Grill gazowy 4-palnikowy", "brand": "BBQMaster", "bullets": ["4 palniki 14kW", "Ruszt żeliwny", "Termometr w pokrywie", "Szafka na butle"]},
        {"name": "Hamak ogrodowy z moskitierą", "brand": "RelaxGarden", "bullets": ["Nylon spadochronowy", "Udzwig 300kg", "Moskitiera 360 stopni", "Karabinczyki stalowe"]},
    ]),
]

# WHY: Additional product name variations for diversity
ADJECTIVES_PL = ["Premium", "Pro", "Ultra", "Max", "Elite", "Classic", "Turbo", "Smart", "Eco", "Lite", "Advanced", "Plus", "Expert", "Master", "Superior"]
ADJECTIVES_EN = ["Premium", "Pro", "Ultra", "Max", "Elite", "Classic", "Smart", "Eco", "Lite", "Advanced", "Plus", "Expert"]

THEMES = ["dark_premium", "light", "amazon_white"]
LANGS = ["pl", "en", "de"]

IMAGE_CONTENT_PROMPT = """You are an Amazon A+ Content specialist. Based on the product info below, generate STRUCTURED DATA for product infographics.

PRODUCT: {product_name}
BRAND: {brand}
BULLETS: {bullets}
DESCRIPTION: {description}
CATEGORY: {category}

Generate a JSON object with these sections:

1. "features" — 6 key product features for a feature grid:
   Each: {{"headline": "short 3-5 word headline", "description": "1-2 sentence benefit-focused description"}}

2. "comparison" — 6-8 comparison points (your product vs generic alternatives):
   Each: {{"feature": "comparison dimension", "ours": "yes" or specific value, "others": "no" or specific worse value}}

3. "specs" — 8-10 technical specifications:
   Each: {{"label": "Spec name", "value": "Spec value"}}

4. "hero" — hero banner content:
   {{"headline": "Powerful 5-8 word headline", "subheadline": "Supporting benefit statement"}}

RULES:
- Write in the SAME LANGUAGE as the product data ({lang})
- Focus on BENEFITS, not just features — what does the customer gain?
- Comparison: highlight genuine advantages, be specific (e.g., "24 months" vs "6 months")
- Specs: include dimensions, materials, weight, certifications — things Amazon shoppers check
- Headlines: short, punchy, use action words
- NEVER invent certifications or claims not in the product data

Return ONLY valid JSON, no markdown, no explanation.
/no_think"""


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response — handles markdown fences, preamble, truncation."""
    clean = text.strip()

    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)```', clean, re.DOTALL)
    if fence_match:
        clean = fence_match.group(1).strip()

    first_brace = clean.find('{')
    last_brace = clean.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        clean = clean[first_brace:last_brace + 1]

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    for suffix in ['}', ']}', '"]}', '"}]}', '"}]}}']:
        try:
            return json.loads(clean + suffix)
        except json.JSONDecodeError:
            continue

    raise json.JSONDecodeError("Could not extract valid JSON", clean[:200], 0)


def validate_content(data: dict):
    """Validate A+ Content JSON structure. Returns (is_valid, error_msg)."""
    required = ["features", "comparison", "specs", "hero"]
    for key in required:
        if key not in data:
            return False, f"Missing key: {key}"

    if not isinstance(data["features"], list) or len(data["features"]) < 4:
        return False, f"features: expected 4+ items, got {len(data.get('features', []))}"

    if not isinstance(data["comparison"], list) or len(data["comparison"]) < 4:
        return False, f"comparison: expected 4+ items, got {len(data.get('comparison', []))}"

    if not isinstance(data["specs"], list) or len(data["specs"]) < 4:
        return False, f"specs: expected 4+ items, got {len(data.get('specs', []))}"

    hero = data.get("hero", {})
    if not hero.get("headline") or not hero.get("subheadline"):
        return False, "hero: missing headline or subheadline"

    # Check feature structure
    for i, f in enumerate(data["features"]):
        if not f.get("headline") or not f.get("description"):
            return False, f"features[{i}]: missing headline or description"

    return True, ""


def generate_product_variant(product: dict, category: str, idx: int) -> dict:
    """Generate a variant of a product for diversity."""
    adj = random.choice(ADJECTIVES_PL)
    lang = random.choice(LANGS) if random.random() < 0.3 else "pl"  # 70% PL
    theme = random.choice(THEMES)

    # Vary the product name
    name = product["name"]
    if random.random() < 0.5:
        parts = name.split(" ")
        if len(parts) > 2:
            insert_pos = random.randint(1, len(parts) - 1)
            parts.insert(insert_pos, adj)
            name = " ".join(parts)

    # Vary bullets slightly
    bullets = list(product["bullets"])
    if random.random() < 0.3:
        random.shuffle(bullets)
    if random.random() < 0.2 and len(bullets) > 2:
        bullets = bullets[:3]

    return {
        "product_name": name,
        "brand": product["brand"],
        "bullets": bullets,
        "description": f"{name} od {product['brand']} — {category}",
        "category": category,
        "lang": lang,
        "theme": theme,
        "source_idx": idx,
    }


def _init_groq_keys():
    """Load Groq keys from environment (available inside lbp-backend container)."""
    keys = []
    primary = os.environ.get("GROQ_API_KEY", "")
    if primary:
        keys.append(primary)
    for i in range(2, 10):
        k = os.environ.get(f"GROQ_API_KEY_{i}", "")
        if k:
            keys.append(k)
    return keys

GROQ_KEYS = _init_groq_keys()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
_groq_key_idx = 0


def call_llm(prompt: str, attempt: int = 0):
    """Call LLM (Groq or Beast). Returns (response_text, duration_seconds)."""
    global _groq_key_idx
    start = time.time()

    if MODE == "groq" and GROQ_KEYS:
        # WHY: Rotate keys on each call to spread rate limits
        key = GROQ_KEYS[_groq_key_idx % len(GROQ_KEYS)]
        _groq_key_idx += 1

        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 4000,
            },
            timeout=60,
        )
        if resp.status_code == 429:
            # WHY: Rate limited — try next key
            time.sleep(2)
            key = GROQ_KEYS[_groq_key_idx % len(GROQ_KEYS)]
            _groq_key_idx += 1
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 4000,
                },
                timeout=60,
            )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
    else:
        # Beast Ollama fallback
        resp = requests.post(OLLAMA_URL, json={
            "model": BEAST_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": 4096},
        }, timeout=300)
        resp.raise_for_status()
        text = resp.json()["message"]["content"]

    duration = time.time() - start
    return text, duration


def process_one(variant: dict, gen_idx: int) -> dict:
    """Process one generation. Returns result dict."""
    prompt = IMAGE_CONTENT_PROMPT.format(
        product_name=variant["product_name"],
        brand=variant["brand"],
        bullets="\n".join(f"- {b}" for b in variant["bullets"]),
        description=variant["description"],
        category=variant["category"],
        lang=variant["lang"],
    )

    result = {
        "idx": gen_idx,
        "product_name": variant["product_name"],
        "brand": variant["brand"],
        "category": variant["category"],
        "lang": variant["lang"],
        "theme": variant["theme"],
        "timestamp": datetime.utcnow().isoformat(),
        "success": False,
        "error": None,
        "duration_s": 0,
        "response_len": 0,
        "valid": False,
        "validation_error": None,
    }

    for attempt in range(2):
        try:
            text, duration = call_llm(prompt, attempt)
            result["duration_s"] = round(duration, 2)
            result["response_len"] = len(text)

            data = extract_json(text)
            is_valid, err = validate_content(data)
            result["valid"] = is_valid
            result["validation_error"] = err if not is_valid else None
            result["success"] = True

            if is_valid:
                result["content_data"] = data
            else:
                result["raw_response"] = text[:500]

            break
        except json.JSONDecodeError as e:
            result["error"] = f"JSON parse error (attempt {attempt}): {str(e)[:100]}"
            if attempt == 0:
                continue
        except requests.Timeout:
            result["error"] = f"Timeout (attempt {attempt})"
            if attempt == 0:
                continue
        except Exception as e:
            result["error"] = str(e)[:200]
            break

    return result


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 5000

    # WHY: Generate product variants to reach target count
    all_products = []
    for cat, products in PRODUCT_CATALOG:
        for p in products:
            all_products.append((cat, p))

    variants = []
    idx = 0
    while len(variants) < target:
        cat, product = all_products[idx % len(all_products)]
        variants.append(generate_product_variant(product, cat, idx))
        idx += 1

    print(f"=== Beast A+ Content Training ===")
    print(f"Target: {target} generations")
    print(f"Mode: {MODE} | Model: {GROQ_MODEL if MODE == 'groq' else BEAST_MODEL}")
    print(f"Unique products: {len(all_products)}")
    print(f"Output: {RESULTS_FILE}")
    print(f"Started: {datetime.utcnow().isoformat()}")
    print()

    stats = {"total": 0, "success": 0, "valid": 0, "json_errors": 0, "timeouts": 0, "avg_duration": 0}
    durations = []

    # WHY: Sequential — Beast has one GPU, parallel would just queue
    with open(RESULTS_FILE, "a") as f:
        for i, variant in enumerate(variants):
            result = process_one(variant, i)

            # Write to JSONL (without full content_data to save space)
            log_entry = {k: v for k, v in result.items() if k != "content_data"}
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            f.flush()

            stats["total"] += 1
            if result["success"]:
                stats["success"] += 1
            if result["valid"]:
                stats["valid"] += 1
            if result.get("error") and "JSON" in str(result["error"]):
                stats["json_errors"] += 1
            if result.get("error") and "Timeout" in str(result["error"]):
                stats["timeouts"] += 1
            if result["duration_s"] > 0:
                durations.append(result["duration_s"])

            # Save valid content_data separately for training
            if result.get("content_data"):
                training_file = OUTPUT_DIR / "valid_content.jsonl"
                with open(training_file, "a") as tf:
                    tf.write(json.dumps({
                        "product_name": variant["product_name"],
                        "brand": variant["brand"],
                        "category": variant["category"],
                        "lang": variant["lang"],
                        "content_data": result["content_data"],
                    }, ensure_ascii=False) + "\n")

            # Progress every 50
            if (i + 1) % 50 == 0 or i == 0:
                avg_d = sum(durations[-50:]) / len(durations[-50:]) if durations else 0
                valid_pct = (stats["valid"] / stats["total"] * 100) if stats["total"] > 0 else 0
                eta_min = avg_d * (target - i - 1) / 60
                print(f"[{i+1}/{target}] valid={valid_pct:.0f}% avg={avg_d:.1f}s json_err={stats['json_errors']} ETA={eta_min:.0f}min | {variant['product_name'][:40]}")

            # WHY: Rate limit — Groq has per-key limits, small delay prevents 429 storms
            if MODE == "groq":
                time.sleep(0.5)

            # Save stats periodically
            if (i + 1) % 100 == 0:
                stats["avg_duration"] = round(sum(durations) / len(durations), 2) if durations else 0
                stats["valid_pct"] = round(stats["valid"] / stats["total"] * 100, 1)
                with open(STATS_FILE, "w") as sf:
                    json.dump(stats, sf, indent=2)

    # Final stats
    stats["avg_duration"] = round(sum(durations) / len(durations), 2) if durations else 0
    stats["valid_pct"] = round(stats["valid"] / stats["total"] * 100, 1)
    stats["completed_at"] = datetime.utcnow().isoformat()
    with open(STATS_FILE, "w") as sf:
        json.dump(stats, sf, indent=2)

    print(f"\n=== DONE ===")
    print(f"Total: {stats['total']}")
    print(f"Success: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"Valid: {stats['valid']} ({stats['valid_pct']}%)")
    print(f"JSON errors: {stats['json_errors']}")
    print(f"Avg duration: {stats['avg_duration']}s")


if __name__ == "__main__":
    main()
