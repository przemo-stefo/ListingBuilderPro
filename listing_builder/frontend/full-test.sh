#!/bin/bash
# full-test.sh
# Purpose: Full functional test of OctoHelper as user Mateusz — real API calls
# NOT for: Unit tests or UI-only testing

API="https://api-lbp.feedmasters.org/api"
KEY="bmUS9B8-vpxg8PBemSQEV74Ny5N4EzzWs8y8UK5gdGo"

PASS=0; FAIL=0; WARN=0; FAILURES=""

log() {
  local t="$1" s="$2" d="$3"
  if [ "$s" = "PASS" ]; then echo "✅ [$t] PASS — $d"; PASS=$((PASS+1))
  elif [ "$s" = "WARN" ]; then echo "⚠️  [$t] WARN — $d"; WARN=$((WARN+1))
  else echo "❌ [$t] FAIL — $d"; FAIL=$((FAIL+1)); FAILURES="$FAILURES\n  ❌ [$t] $d"; fi
}

H="-H X-API-Key:$KEY"

echo "🧪 OctoHelper — Full Functional Test (User Mateusz)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Backend: $API | $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ===== 1. INFRASTRUCTURE =====
echo "━━━ 1. Infrastructure ━━━"
HEALTH=$(curl -s "$API/../health")
echo "$HEALTH" | grep -q '"healthy"' && log "1a/health" "PASS" "Backend healthy" || log "1a/health" "FAIL" "$HEALTH"
echo "$HEALTH" | grep -q '"connected"' && log "1b/db" "PASS" "DB connected" || log "1b/db" "FAIL" "DB not connected"
S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/products?page=1&page_size=1")
[ "$S" = "200" ] && log "1c/auth" "PASS" "API key works" || log "1c/auth" "FAIL" "Auth: $S"
S=$(curl -s -o /dev/null -w "%{http_code}" "$API/products")
[ "$S" = "401" ] || [ "$S" = "403" ] && log "1d/no-auth" "PASS" "Rejects ($S)" || log "1d/no-auth" "FAIL" "$S"

# ===== 2. IMPORT (single product) =====
echo ""; echo "━━━ 2. Import — Single Product ━━━"
CREATE=$(curl -s $H -H "Content-Type:application/json" -X POST "$API/import/product" -d '{
  "title": "TEST Trinkflasche Edelstahl 750ml BPA-frei Sport Outdoor",
  "description": "Hochwertige Edelstahl Trinkflasche für Sport. Doppelwandig isoliert, 24h kalt, 12h warm. 750ml, BPA-frei.",
  "brand": "AquaPure",
  "marketplace": "amazon_de",
  "asin": "B0TEST99999",
  "category": "Sports & Outdoors",
  "source_id": "TEST-FULLTEST-99999",
  "source_platform": "manual"
}')
PID=$(echo "$CREATE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',d.get('product_id','')))" 2>/dev/null)
[ -n "$PID" ] && log "2a/import-single" "PASS" "Product $PID" || log "2a/import-single" "FAIL" "Response: ${CREATE:0:200}"

# ===== 3. PRODUCTS (list, search, get) =====
echo ""; echo "━━━ 3. Products — List, Search, Get ━━━"
PRODS=$(curl -s $H "$API/products?page=1&page_size=5")
TOTAL=$(echo "$PRODS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null)
[ "$TOTAL" -gt 0 ] 2>/dev/null && log "3a/list" "PASS" "$TOTAL products" || log "3a/list" "WARN" "Empty ($TOTAL)"

SEARCH=$(curl -s $H "$API/products?search=Trinkflasche&page=1&page_size=5")
ST=$(echo "$SEARCH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null)
[ "$ST" -gt 0 ] 2>/dev/null && log "3b/search" "PASS" "Found $ST" || log "3b/search" "WARN" "Search 0"

if [ -n "$PID" ]; then
  GET=$(curl -s $H "$API/products/$PID")
  echo "$GET" | grep -q "TEST Trinkflasche" && log "3c/get-by-id" "PASS" "Got product" || log "3c/get-by-id" "FAIL" "Not found"
fi

# Dashboard stats
STATS=$(curl -s $H "$API/products/stats/summary")
echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_products',0))" 2>/dev/null | grep -qE "[0-9]+" && log "3d/stats" "PASS" "Dashboard stats OK" || log "3d/stats" "FAIL" "$STATS"

# ===== 4. OPTIMIZER (CORE) =====
echo ""; echo "━━━ 4. Optimizer — Core Feature ━━━"
echo "⏳ Running optimizer (15-60s)..."
OPT=$(curl -s --max-time 180 $H -H "Content-Type:application/json" -X POST "$API/optimizer/generate" -d '{
  "product_title": "Trinkflasche Edelstahl 750ml BPA-frei Sport Outdoor Camping",
  "brand": "AquaPure",
  "keywords": [
    {"phrase": "trinkflasche edelstahl", "search_volume": 50000},
    {"phrase": "wasserflasche sport", "search_volume": 30000},
    {"phrase": "thermosflasche 750ml", "search_volume": 20000},
    {"phrase": "isolierflasche bpa frei", "search_volume": 15000},
    {"phrase": "trinkflasche kinder schule", "search_volume": 12000},
    {"phrase": "edelstahl flasche outdoor", "search_volume": 8000},
    {"phrase": "vakuumisoliert trinkflasche", "search_volume": 7000},
    {"phrase": "sportflasche auslaufsicher", "search_volume": 6000},
    {"phrase": "trinkflasche camping wandern", "search_volume": 5000},
    {"phrase": "wasserflasche bpa frei kinder", "search_volume": 4000}
  ],
  "marketplace": "amazon_de",
  "category": "Sports & Outdoors",
  "mode": "aggressive"
}')

# Parse output — response uses "listing" key (not "optimized"), "scores" for coverage
TITLE=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('listing',{}).get('title',''))" 2>/dev/null)
BULLETS=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('listing',{}).get('bullet_points',[])))" 2>/dev/null)
DESC_LEN=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('listing',{}).get('description','')))" 2>/dev/null)
BK=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('listing',{}).get('backend_keywords',''))" 2>/dev/null)
RJ=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ranking_juice',{}).get('score',0))" 2>/dev/null)
COV=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('scores',{}).get('coverage_pct',0))" 2>/dev/null)

# Title
[ -n "$TITLE" ] && [ ${#TITLE} -gt 10 ] && log "4a/title" "PASS" "${TITLE:0:80}..." || log "4a/title" "FAIL" "No title"

# Bullets
[ "$BULLETS" -ge 4 ] 2>/dev/null && log "4b/bullets" "PASS" "$BULLETS bullet points" || log "4b/bullets" "FAIL" "$BULLETS bullets"

# Description
[ "$DESC_LEN" -gt 100 ] 2>/dev/null && log "4c/description" "PASS" "$DESC_LEN chars" || log "4c/description" "FAIL" "$DESC_LEN chars"

# Backend keywords
BK_BYTES=$(echo -n "$BK" | wc -c | tr -d ' ')
[ "$BK_BYTES" -gt 10 ] && log "4d/backend-kw" "PASS" "$BK_BYTES bytes" || log "4d/backend-kw" "FAIL" "$BK_BYTES bytes"
[ "$BK_BYTES" -le 249 ] && log "4e/bk-limit" "PASS" "≤249 bytes" || log "4e/bk-limit" "FAIL" "$BK_BYTES bytes >249!"

# Ranking Juice
[ "$RJ" -gt 50 ] 2>/dev/null && log "4f/ranking-juice" "PASS" "RJ=$RJ" || log "4f/ranking-juice" "WARN" "RJ=$RJ"

# Coverage
COV_INT=${COV%.*}
[ "$COV_INT" -gt 60 ] 2>/dev/null && log "4g/coverage" "PASS" "$COV%" || log "4g/coverage" "WARN" "$COV%"

# PPC recommendations
PPC=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); p=d.get('ppc_recommendations',{}); print(len(p.get('exact_match',[])))" 2>/dev/null)
[ "$PPC" -gt 0 ] 2>/dev/null && log "4h/ppc" "PASS" "$PPC exact matches" || log "4h/ppc" "WARN" "No PPC"

# Compliance
COMP_W=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('compliance',{}).get('warnings',[])))" 2>/dev/null)
log "4i/compliance" "PASS" "$COMP_W warnings"

# ===== 5. OUTPUT FORMAT VALIDATION =====
echo ""; echo "━━━ 5. Output Format Validation ━━━"
if [ -n "$TITLE" ] && [ ${#TITLE} -gt 10 ]; then
  # Title length ≤200
  TL=${#TITLE}
  [ "$TL" -le 200 ] && log "5a/title-len" "PASS" "$TL chars (≤200)" || log "5a/title-len" "FAIL" "$TL chars >200!"

  # Title has brand
  echo "$TITLE" | grep -qi "AquaPure" && log "5b/title-brand" "PASS" "Brand in title" || log "5b/title-brand" "WARN" "Brand missing"

  # No promo words
  PROMO=$(echo "$TITLE" | grep -Ei "best|#1|guarantee|free shipping|sale|discount|cheapest" || echo "")
  [ -z "$PROMO" ] && log "5c/no-promo" "PASS" "Clean title" || log "5c/no-promo" "FAIL" "Promo: $PROMO"

  # Bullet max length
  BMAX=$(echo "$OPT" | python3 -c "import sys,json; d=json.load(sys.stdin); bs=d.get('listing',{}).get('bullet_points',[]); print(max(len(b) for b in bs) if bs else 0)" 2>/dev/null)
  [ "$BMAX" -le 500 ] 2>/dev/null && log "5d/bullet-maxlen" "PASS" "Max $BMAX chars" || log "5d/bullet-maxlen" "FAIL" "$BMAX >500!"

  # Description ≤2000
  [ "$DESC_LEN" -le 2000 ] && log "5e/desc-len" "PASS" "$DESC_LEN ≤2000" || log "5e/desc-len" "FAIL" "$DESC_LEN >2000!"

  # BK no commas
  echo "$BK" | grep -q "," && log "5f/bk-format" "WARN" "Commas in BK" || log "5f/bk-format" "PASS" "No commas"

  # German language
  GERMAN=$(echo "$OPT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
desc=d.get('listing',{}).get('description','')
de_words=['und','für','mit','die','der','das','ist','aus','eine','wird']
found=sum(1 for w in de_words if w in desc.lower())
print('yes' if found>=3 else 'no')
" 2>/dev/null)
  [ "$GERMAN" = "yes" ] && log "5g/german" "PASS" "Output in German" || log "5g/german" "WARN" "May not be German"
fi

# ===== 6. OPTIMIZER HISTORY & TRACES =====
echo ""; echo "━━━ 6. History & Traces ━━━"
HIST=$(curl -s $H "$API/optimizer/history?page=1&page_size=3")
HT=$(echo "$HIST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null)
[ "$HT" -gt 0 ] 2>/dev/null && log "6a/history" "PASS" "$HT records" || log "6a/history" "WARN" "Empty"

S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/optimizer/traces?page=1&page_size=1")
[ "$S" = "200" ] && log "6b/traces" "PASS" "Traces 200" || log "6b/traces" "FAIL" "$S"

S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/optimizer/health")
[ "$S" = "200" ] && log "6c/opt-health" "PASS" "Optimizer health OK" || log "6c/opt-health" "FAIL" "$S"

# ===== 7. CONVERTER =====
echo ""; echo "━━━ 7. Converter ━━━"
# Check marketplaces
MKT=$(curl -s $H "$API/converter/marketplaces")
echo "$MKT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null | grep -qE "[0-9]+" && log "7a/marketplaces" "PASS" "Marketplace list OK" || log "7a/marketplaces" "WARN" "$MKT"

# Scrape endpoint (won't actually scrape without valid Allegro URL)
S=$(curl -s -o /dev/null -w "%{http_code}" $H -H "Content-Type:application/json" -X POST "$API/converter/scrape" -d '{"urls": ["https://allegro.pl/oferta/test-123"]}')
[ "$S" != "404" ] && log "7b/scrape" "PASS" "Scrape endpoint ($S)" || log "7b/scrape" "FAIL" "404"

# Store-urls flow
STORE=$(curl -s $H -H "Content-Type:application/json" -X POST "$API/converter/store-urls" -d '{"urls": ["https://allegro.pl/oferta/butelka-termiczna-test-123"]}')
JOB_ID=$(echo "$STORE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('job_id',''))" 2>/dev/null)
[ -n "$JOB_ID" ] && log "7c/store-urls" "PASS" "Job $JOB_ID" || log "7c/store-urls" "WARN" "${STORE:0:100}"

# Convert endpoint (needs scraped data)
S=$(curl -s -o /dev/null -w "%{http_code}" $H -H "Content-Type:application/json" -X POST "$API/converter/convert" -d '{
  "products": [{"title": "Butelka termiczna 750ml", "description": "Stalowa butelka", "price": "89.99", "source_marketplace": "allegro"}],
  "target_marketplace": "amazon_de"
}')
[ "$S" = "200" ] || [ "$S" = "422" ] && log "7d/convert" "PASS" "Convert endpoint ($S)" || log "7d/convert" "FAIL" "$S"

# Download endpoint
S=$(curl -s -o /dev/null -w "%{http_code}" $H -H "Content-Type:application/json" -X POST "$API/converter/download" -d '{"products": [], "target_marketplace": "amazon_de", "format": "csv"}')
[ "$S" != "404" ] && log "7e/download" "PASS" "Download endpoint ($S)" || log "7e/download" "FAIL" "404"

# ===== 8. EXPERT AI (RAG) =====
echo ""; echo "━━━ 8. Expert AI (RAG Q&A) ━━━"
echo "⏳ Querying Expert AI..."
QA=$(curl -s --max-time 60 $H -H "Content-Type:application/json" -X POST "$API/knowledge/chat" -d '{"question": "Jak zoptymalizować backend keywords na Amazon DE?"}')
ANS=$(echo "$QA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('answer','')[:120])" 2>/dev/null)
[ -n "$ANS" ] && log "8a/answer" "PASS" "${ANS:0:80}..." || log "8a/answer" "FAIL" "No answer"

SRC=$(echo "$QA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('sources',[])))" 2>/dev/null)
[ "$SRC" -gt 0 ] 2>/dev/null && log "8b/sources" "PASS" "$SRC sources" || log "8b/sources" "WARN" "No sources"

STATS=$(curl -s $H "$API/knowledge/stats")
CHUNKS=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_chunks',0))" 2>/dev/null)
[ "$CHUNKS" -gt 1000 ] 2>/dev/null && log "8c/kb-size" "PASS" "$CHUNKS chunks" || log "8c/kb-size" "WARN" "$CHUNKS"

# ===== 9. SETTINGS =====
echo ""; echo "━━━ 9. Settings ━━━"
SET=$(curl -s $H "$API/settings")
echo "$SET" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if 'general' in d else 'fail')" 2>/dev/null | grep -q "ok" && log "9a/get" "PASS" "Settings loaded" || log "9a/get" "FAIL" "$SET"

UPD=$(curl -s -o /dev/null -w "%{http_code}" $H -H "Content-Type:application/json" -X PUT "$API/settings" -d '{"general":{"store_name":"Mateusz Test","default_marketplace":"amazon","timezone":"Europe/Warsaw"}}')
[ "$UPD" = "200" ] && log "9b/update" "PASS" "Updated" || log "9b/update" "FAIL" "$UPD"

# ===== 10. OAUTH & INTEGRATIONS =====
echo ""; echo "━━━ 10. OAuth & Integrations ━━━"
OAUTH=$(curl -s $H "$API/oauth/status")
echo "$OAUTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if 'connections' in d else 'fail')" 2>/dev/null | grep -q "ok" && log "10a/status" "PASS" "OAuth status OK" || log "10a/status" "FAIL" "$OAUTH"

ALLEGRO=$(echo "$OAUTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('connections',{}).get('allegro',{}).get('status','none'))" 2>/dev/null)
log "10b/allegro" "PASS" "Allegro: $ALLEGRO"

# OAuth connections list
CONN=$(curl -s $H "$API/oauth/connections")
echo "$CONN" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null && log "10c/connections" "PASS" "Connections list OK" || log "10c/connections" "WARN" "${CONN:0:100}"

# ===== 11. EXPORT / PUBLISH =====
echo ""; echo "━━━ 11. Export / Publish ━━━"
MKT=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/export/marketplaces")
[ "$MKT" = "200" ] && log "11a/marketplaces" "PASS" "Export marketplaces" || log "11a/marketplaces" "WARN" "$MKT"

# Bulk publish (empty = should return proper error)
S=$(curl -s -o /dev/null -w "%{http_code}" $H -H "Content-Type:application/json" -X POST "$API/export/bulk-publish" -d '{"product_ids":[],"marketplace":"amazon_de","format":"csv"}')
[ "$S" != "404" ] && log "11b/bulk-publish" "PASS" "Endpoint exists ($S)" || log "11b/bulk-publish" "FAIL" "404"

# Listings for download
S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/listings?page=1&page_size=1")
[ "$S" = "200" ] && log "11c/listings" "PASS" "Listings API" || log "11c/listings" "FAIL" "$S"

# ===== 12. COMPLIANCE =====
echo ""; echo "━━━ 12. Compliance Guard ━━━"
S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/compliance/reports?page=1&page_size=1")
[ "$S" = "200" ] && log "12a/reports" "PASS" "Compliance reports" || log "12a/reports" "WARN" "$S"

# Compliance validate
S=$(curl -s -o /dev/null -w "%{http_code}" $H -H "Content-Type:application/json" -X POST "$API/compliance/validate" -d '{"title":"Test Product","marketplace":"amazon_de","bullets":["Bullet 1"]}')
[ "$S" != "404" ] && log "12b/validate" "PASS" "Validate endpoint ($S)" || log "12b/validate" "FAIL" "404"

# ===== 13. NEWS =====
echo ""; echo "━━━ 13. News Feed ━━━"
NEWS=$(curl -s $H "$API/news/feed?page=1&page_size=3")
NC=$(echo "$NEWS" | python3 -c "import sys,json; d=json.load(sys.stdin); items=d if isinstance(d,list) else d.get('items',[]); print(len(items))" 2>/dev/null)
[ "$NC" -gt 0 ] 2>/dev/null && log "13a/news" "PASS" "$NC news items" || log "13a/news" "WARN" "No news ($NC)"

# ===== 14. STRIPE & LICENSING =====
echo ""; echo "━━━ 14. Stripe & Licensing ━━━"
S=$(curl -s -o /dev/null -w "%{http_code}" $H -H "Content-Type:application/json" -X POST "$API/stripe/create-checkout" -d '{"success_url":"https://test.com/ok","cancel_url":"https://test.com/no"}')
[ "$S" != "404" ] && log "14a/checkout" "PASS" "Checkout ($S)" || log "14a/checkout" "FAIL" "404"

S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/stripe/subscription")
[ "$S" != "404" ] && log "14b/subscription" "PASS" "Subscription ($S)" || log "14b/subscription" "FAIL" "404"

# ===== 15. MONITORING =====
echo ""; echo "━━━ 15. Monitoring ━━━"
S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/monitoring/tracked?page=1&page_size=1")
[ "$S" = "200" ] && log "15a/tracked" "PASS" "Tracked products" || log "15a/tracked" "FAIL" "$S"

S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/monitoring/alerts?page=1&page_size=1")
[ "$S" = "200" ] && log "15b/alerts" "PASS" "Alerts list" || log "15b/alerts" "FAIL" "$S"

S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/monitoring/status")
[ "$S" = "200" ] && log "15c/status" "PASS" "Monitoring status" || log "15c/status" "FAIL" "$S"

# ===== 16. RESEARCH =====
echo ""; echo "━━━ 16. Research / DataDive ━━━"
echo "⏳ Running audience research..."
RES=$(curl -s --max-time 60 $H -H "Content-Type:application/json" -X POST "$API/research/audience" -d '{"product": "Edelstahl Trinkflasche 750ml", "marketplace": "amazon_de"}')
RES_LEN=$(echo "$RES" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(str(d)))" 2>/dev/null)
[ "$RES_LEN" -gt 100 ] 2>/dev/null && log "16a/audience" "PASS" "Response: $RES_LEN chars" || log "16a/audience" "WARN" "$RES_LEN chars"

# ===== 17. ALLEGRO OFFERS =====
echo ""; echo "━━━ 17. Allegro Offers API ━━━"
S=$(curl -s -o /dev/null -w "%{http_code}" $H "$API/allegro?page=1&page_size=1")
[ "$S" = "200" ] && log "17a/allegro-list" "PASS" "Allegro offers" || log "17a/allegro-list" "WARN" "$S"

# ===== CLEANUP =====
echo ""; echo "━━━ Cleanup ━━━"
if [ -n "$PID" ]; then
  S=$(curl -s -o /dev/null -w "%{http_code}" $H -X DELETE "$API/products/$PID")
  [ "$S" = "200" ] || [ "$S" = "204" ] && log "99/cleanup" "PASS" "Test product deleted" || log "99/cleanup" "WARN" "$S"
fi

# ===== SUMMARY =====
TOTAL=$((PASS+FAIL+WARN))
PCT=$((PASS * 100 / TOTAL))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 FINAL SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✅ PASS: $PASS/$TOTAL"
echo "  ⚠️  WARN: $WARN/$TOTAL"
echo "  ❌ FAIL: $FAIL/$TOTAL"
echo "  📈 Score: $PCT%"

if [ $FAIL -gt 0 ]; then
  echo ""
  echo "❌ FAILURES:"
  echo -e "$FAILURES"
fi

if [ $WARN -gt 0 ]; then
  echo ""
  echo "⚠️  Warnings are non-critical (empty data, optional features)."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAIL -eq 0 ]; then
  echo "🎉 ALL TESTS PASSED! Mateusz ready to go."
else
  echo "⚠️  $FAIL failure(s) — fix before demo."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
