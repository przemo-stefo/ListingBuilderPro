# backend/scripts/import_training_to_db.py
# Purpose: Generate A+ Content examples and save directly to aplus_training_examples table
# NOT for: Production use — one-time seeding script
# Run: docker exec lbp-backend python3 /app/scripts/import_training_to_db.py [count]

import json
import os
import sys
import time
import random
import re
import requests
from datetime import datetime

sys.path.insert(0, "/app")
from database import SessionLocal
from models.aplus_example import AplusTrainingExample
from services.image_service import IMAGE_CONTENT_PROMPT

COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 200

# WHY: Groq API with key rotation — same as batch_train_images.py
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_KEYS = [v for k, v in sorted(os.environ.items()) if k.startswith("GROQ_API_KEY") and v]

PRODUCTS = [
    ("Elektronika", [
        {"name": "Sluchawki bezprzewodowe ANC Pro 500", "brand": "SoundMax", "bullets": ["Redukcja szumow ANC -42dB", "Bluetooth 5.3 LDAC", "Bateria 60h"]},
        {"name": "Powerbank solarny 30000mAh", "brand": "SunCharge", "bullets": ["Panel solarny 5W", "USB-C PD 65W", "Wodoodporny IP67"]},
        {"name": "Router WiFi 6E Mesh AX7800", "brand": "NetPro", "bullets": ["Tri-band 7800Mbps", "Pokrycie 600m2", "WPA3"]},
        {"name": "Kamera IP 4K PTZ outdoor", "brand": "SecureVision", "bullets": ["4K Ultra HD", "Obrot 360 stopni", "Noktowizja 50m"]},
    ]),
    ("Sport i outdoor", [
        {"name": "Mata do jogi TPE premium 183x66cm", "brand": "YogaFlow", "bullets": ["TPE ekologiczny 6mm", "Antypoślizgowa", "Pasek w zestawie"]},
        {"name": "Butelka termiczna 750ml stal", "brand": "HydroSteel", "bullets": ["Utrzymuje temp 24h", "Stal 18/8", "BPA free"]},
        {"name": "Plecak turystyczny 65L", "brand": "TrailMaster", "bullets": ["System nosny AirFlow", "Pokrowiec na deszcz", "Kieszenie boczne"]},
    ]),
    ("Dom i kuchnia", [
        {"name": "Robot kuchenny wielofunkcyjny 1200W", "brand": "ChefPro", "bullets": ["12 programow", "Pojemnosc 4.5L", "Wyswietlacz LCD"]},
        {"name": "Oczyszczacz powietrza HEPA H13", "brand": "PureAir", "bullets": ["Filtr HEPA H13", "CADR 400m3/h", "Czujnik PM2.5"]},
        {"name": "Ekspres cisnieniowy 20bar", "brand": "BaristaPro", "bullets": ["Cisnienie 20 bar", "Mlynek ceramiczny", "Spieniacz mleka"]},
    ]),
    ("Uroda i zdrowie", [
        {"name": "Szczoteczka soniczna 40000rpm", "brand": "DentaSonic", "bullets": ["40000 ruchow/min", "5 trybow", "Timer 2min"]},
        {"name": "Masazer pistoletowy 30 poziomow", "brand": "MuscleRelax", "bullets": ["30 poziomow intensywnosci", "6 koncowek", "Bateria 6h"]},
    ]),
    ("Dziecko i zabawki", [
        {"name": "Monitor oddechu niemowlat WiFi", "brand": "BabySafe", "bullets": ["Czujnik ruchu Piezo", "Powiadomienia na telefon", "Kamera HD"]},
        {"name": "Fotelik samochodowy 0-36kg i-Size", "brand": "KidSecure", "bullets": ["i-Size R129", "ISOFIX", "Ochrona boczna SIP"]},
    ]),
    ("Motoryzacja", [
        {"name": "Kamera samochodowa 4K WiFi GPS", "brand": "DashCam", "bullets": ["4K 30fps", "GPS wbudowany", "Tryb parkingowy"]},
        {"name": "Prostownik inteligentny 12V/24V", "brand": "ChargeSmart", "bullets": ["12V i 24V", "Diagnostyka baterii", "Tryb zimowy"]},
    ]),
    ("Odziez i akcesoria", [
        {"name": "Kurtka puchowa meska 800FP", "brand": "AlpinWear", "bullets": ["Puch gesowy 800FP", "Wodoodporna DWR", "Waga 380g"]},
        {"name": "Plecak miejski antykradziezowy USB", "brand": "UrbanSafe", "bullets": ["Port USB", "Zamek ukryty", "Wodoodporny"]},
    ]),
    ("Narzedzia i majsterkowanie", [
        {"name": "Wiertarko-wkretarka 20V bezsczotkowa", "brand": "PowerDrill", "bullets": ["Silnik bezsczotkowy", "80Nm momentu", "2 akumulatory"]},
        {"name": "Laser krzyzowy 360 zielony", "brand": "LevelPro", "bullets": ["360 stopni", "Zasieg 30m", "Samopoziomowanie"]},
    ]),
    ("Zwierzeta", [
        {"name": "Automatyczny dozownik karmy WiFi 6L", "brand": "PetFeeder", "bullets": ["Pojemnosc 6L", "Sterowanie WiFi", "Kamera HD"]},
        {"name": "Transporter dla kota IATA 55x35x25", "brand": "TravelPet", "bullets": ["Norma IATA", "Wentylacja 360", "Kolka i raczka"]},
    ]),
    ("Ogrod", [
        {"name": "Robot koszacy GPS RTK 3500m2", "brand": "MowBot", "bullets": ["GPS RTK bez kabla", "Do 3500m2", "Mulczowanie"]},
        {"name": "Lampa solarna ogrodowa LED 200lm", "brand": "SolarGlow", "bullets": ["Panel solarny", "200 lumenow", "IP65 wodoodporna"]},
    ]),
]

LANGS = ["pl"] * 7 + ["en"] * 2 + ["de"]
ADJECTIVES = ["Premium", "Ultra", "Kompaktowy", "Zaawansowany", "Nowoczesny", "Profesjonalny"]


def extract_json(text):
    clean = text.strip()
    fence = re.search(r'```(?:json)?\s*\n?(.*?)```', clean, re.DOTALL)
    if fence:
        clean = fence.group(1).strip()
    fb = clean.find('{')
    lb = clean.rfind('}')
    if fb != -1 and lb > fb:
        clean = clean[fb:lb+1]
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    for suffix in ['}', ']}', '"]}', '"}]}']:
        try:
            return json.loads(clean + suffix)
        except json.JSONDecodeError:
            continue
    return None


def call_groq(prompt, key):
    resp = requests.post(GROQ_API_URL, json={
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 4000,
    }, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def validate_content(data):
    required = ["features", "comparison", "specs", "hero"]
    return all(k in data and data[k] for k in required)


db = SessionLocal()
success = 0
errors = 0
key_idx = 0

print(f"Starting import: {COUNT} generations, {len(GROQ_KEYS)} Groq keys")

for i in range(COUNT):
    cat, products = random.choice(PRODUCTS)
    prod = random.choice(products)
    lang = random.choice(LANGS)
    adj = random.choice(ADJECTIVES)
    name = f"{adj} {prod['name']}" if random.random() > 0.5 else prod["name"]

    prompt = IMAGE_CONTENT_PROMPT.format(
        product_name=name, brand=prod["brand"],
        bullets="\n".join(f"- {b}" for b in prod["bullets"]),
        description="", category=cat, lang=lang, examples_block="",
    )

    key = GROQ_KEYS[key_idx % len(GROQ_KEYS)]
    key_idx += 1

    try:
        text = call_groq(prompt, key)
        data = extract_json(text)
        if data and validate_content(data):
            ex = AplusTrainingExample(
                product_name=name, brand=prod["brand"],
                category=cat, lang=lang, content_data=data,
                quality_score=0.7, source="training_import",
            )
            db.add(ex)
            db.commit()
            success += 1
        else:
            errors += 1
    except Exception as e:
        errors += 1
        if "429" in str(e):
            time.sleep(2)

    if (i + 1) % 50 == 0:
        print(f"Progress: {i+1}/{COUNT} | OK: {success} | Errors: {errors}")

    time.sleep(0.5)

print(f"\nDone: {success}/{COUNT} imported to DB | {errors} errors")
db.close()
