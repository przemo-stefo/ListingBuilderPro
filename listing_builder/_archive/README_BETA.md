# 🚀 Amazon Listing Builder v2.0 - Beta Testing Guide

## 📋 Wymagania Systemowe

- **Python 3.8+** (zalecane: 3.12)
- **System operacyjny:** Windows, macOS, lub Linux
- **RAM:** minimum 4GB
- **Dysk:** ~500MB wolnego miejsca

---

## ⚡ Szybki Start (3 kroki)

### 1. Pobierz pliki
```bash
# Rozpakuj ZIP lub sklonuj repozytorium
cd amazon-master-tool/listing_builder
```

### 2. Uruchom instalację
```bash
chmod +x INSTALL.sh
./INSTALL.sh
```

### 3. Uruchom program
```bash
./start.sh
```

**GUI otworzy się automatycznie w przeglądarce:** http://127.0.0.1:7860

---

## 📚 Co Program Robi?

### ✅ Funkcje Główne:

1. **📝 Listing Builder**
   - Generowanie tytułów (7-9 fraz kluczowych)
   - 5 bullet points z benefitami
   - Opis SEO-optimized
   - Backend search terms (240-249 bajtów)
   - Pokrycie keywords 73-98%

2. **🔍 Badanie Potencjału Sprzedażowego**
   - Upload CSV z Helium 10 Black Box
   - Automatyczna analiza całej niszy
   - Scoring 0-100 (Inner Circle algorithm)
   - **NOWOŚĆ:** Generowanie pięknych raportów Excel

3. **📊 Excel Reports (BETA NOWOŚĆ)**
   - 10 arkuszy z kolorami i wyjaśnieniami
   - Opportunity Matrix (złote okazje)
   - Competition Analysis po poziomach
   - Strategic Insights (Inner Circle)
   - Porównanie Niche CSV + Black Box

4. **💬 AI Assistant**
   - 677 transkryptów Inner Circle
   - Pomoc z Amazon strategies
   - Keyword research tips
   - PPC campaign advice

---

## 📁 Pliki Potrzebne

### Do Listing Builder:
- **Data Dive CSV** (obowiązkowy) - główne keywords
- **Cerebro CSV** (opcjonalny) - keywords konkurentów
- **Magnet CSV** (opcjonalny) - related keywords

### Do Excel Reports:
- **Niche CSV** (opcjonalny) - top performers
- **Black Box CSV** (opcjonalny) - szeroki rynek

**Gdzie je wziąć?** Helium 10 → Data Dive/Black Box → Export

---

## 🎨 Jak Używać Excel Generator (NOWOŚĆ)

1. Otwórz tab **"🔍 Badanie Potencjału"**
2. Przewiń do **"Opcja 1B: Generuj Piękny Raport Excel"**
3. Upload 1 lub 2 pliki CSV:
   - Niche CSV (np. z Data Dive)
   - Black Box CSV (szeroki rynek)
4. Kliknij **"🎨 Generuj Piękny Raport Excel"**
5. Excel zapisze się w folderze programu

### Co dostaniesz w Excel:
- 📖 **INSTRUKCJA** - jak czytać raport
- 📊 **EXECUTIVE SUMMARY** - kluczowe metryki
- 🏆 **TOP 50 BY REVENUE** - najlepsze produkty
- 💎 **OPPORTUNITY MATRIX** - złote okazje
- 🔍 **COMPETITION ANALYSIS** - analiza konkurencji
- 📊 **ALL PRODUCTS** - kompletna lista
- 💡 **STRATEGIC INSIGHTS** - rekomendacje

**Kolory:**
- 🟢 Zielony = HIGH POTENTIAL (score ≥70)
- 🟡 Żółty = MEDIUM POTENTIAL (score 50-69)
- 🔴 Czerwony = LOW POTENTIAL (score <50)

---

## ❓ FAQ - Beta Testing

### Q: Czy działa offline?
**A:** TAK - całkowicie offline po instalacji. Nie wysyła danych na zewnątrz.

### Q: Czy potrzebuję API key?
**A:** NIE - program nie łączy się z żadnymi API. Wszystko działa lokalnie.

### Q: Co jeśli nie mam bazy wiedzy (.knowledge)?
**A:** Program będzie działał bez AI Assistant. Pozostałe funkcje (Listing Builder + Excel Reports) działają normalnie.

### Q: Czy mogę używać na Windows?
**A:** TAK - Python działa na Windows. Użyj `python` zamiast `python3` w komendach.

### Q: Jak zatrzymać program?
**A:** Wciśnij **Ctrl+C** w terminalu lub zamknij okno terminala.

### Q: Gdzie zapisują się Excele?
**A:** W tym samym folderze co program (`listing_builder/`).

---

## 🐛 Zgłaszanie Błędów

Jeśli coś nie działa:

1. **Skopiuj błąd** z terminala
2. **Zrób screenshot** GUI (jeśli problem w interfejsie)
3. **Opisz co robiłeś** przed błędem
4. Wyślij do: [twój email/Discord/Slack]

**Przydatne info:**
- System operacyjny (Windows/Mac/Linux)
- Wersja Pythona: `python3 --version`
- Błąd z terminala (tekst czerwony)

---

## 🚀 Zaawansowane Opcje

### Zmiana portu (jeśli 7860 zajęty):
```bash
# Edytuj gradio_app_pro.py
# Znajdź: demo.launch(share=False)
# Zmień na: demo.launch(share=False, server_port=7861)
```

### Dostęp z innego komputera w sieci:
```bash
# Edytuj gradio_app_pro.py
# Zmień: demo.launch(share=False)
# Na: demo.launch(share=False, server_name="0.0.0.0")
# Dostęp: http://[IP-komputera]:7860
```

---

## 📊 Testowanie Excel Generator - Checklist

Przetestuj proszę:

- [ ] Upload tylko Niche CSV → Czy generuje Excel?
- [ ] Upload tylko Black Box CSV → Czy generuje Excel?
- [ ] Upload oba CSV → Czy porównuje i generuje?
- [ ] Czy Excel się otwiera w Excel/LibreOffice?
- [ ] Czy kolory działają (zielony/żółty/czerwony)?
- [ ] Czy "INSTRUKCJA" jest zrozumiała?
- [ ] Czy liczby wyglądają sensownie?
- [ ] Czy "Opportunity Matrix" pokazuje dobre okazje?

---

## 💡 Tips dla Beta Testerów

1. **Testuj z prawdziwymi danymi** - nie używaj przykładowych CSV
2. **Sprawdź Excel na różnych produktach** - niche, high competition, low competition
3. **Zobacz czy Strategic Insights mają sens** - czy rekomendacje są logiczne?
4. **Testuj różne kombinacje** - sam Niche, sam Black Box, oba razem
5. **Zgłaszaj wszystko co wydaje się dziwne** - nawet małe rzeczy

---

## 🎯 Następne Kroki

Po testach beta planujemy:
- ☁️ Wersja cloud (dostęp przez przeglądarkę bez instalacji)
- 📱 Mobilna wersja
- 🔄 Automatyczne aktualizacje
- 📈 Więcej typów raportów Excel
- 🤖 Integracja z Claude API (opcjonalna)

---

**Wersja:** 2.0-beta
**Data:** 2025-11-05
**Support:** [twój kontakt]

---

# 🙏 Dziękujemy za testowanie!

Twój feedback jest mega ważny. Każda uwaga pomoże ulepszyć produkt dla wszystkich użytkowników Amazon FBA.

**Happy Testing! 🚀**
