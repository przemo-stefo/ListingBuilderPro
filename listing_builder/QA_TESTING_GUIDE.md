# QA Testing Guide - Marketplace Listing Automation System

**Version:** 1.0.0
**Last Updated:** 2026-01-23
**Testing Approach:** Manual testing (following David's philosophy)

---

## Table of Contents
1. [Setup Verification](#setup-verification)
2. [API Endpoint Tests](#api-endpoint-tests)
3. [Frontend Feature Tests](#frontend-feature-tests)
4. [Integration Tests](#integration-tests)
5. [Edge Case Tests](#edge-case-tests)
6. [Performance Tests](#performance-tests)
7. [Browser Compatibility](#browser-compatibility)
8. [Mobile Responsiveness](#mobile-responsiveness)

---

## Setup Verification

### Prerequisites Check
Test each prerequisite before starting main tests.

**Backend:**
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Virtual environment activated (`which python` shows venv)
- [ ] All dependencies installed (`pip list | grep fastapi`)
- [ ] .env file exists with all required variables
- [ ] Supabase database accessible
- [ ] Groq API key valid

**Frontend:**
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Dependencies installed (`ls node_modules | grep next`)
- [ ] .env.local exists with API URL
- [ ] Can access backend API URL

### Environment Variables Test

**Backend (.env):**
```bash
# Check required variables exist
grep -E "SUPABASE_URL|GROQ_API_KEY|WEBHOOK_SECRET" backend/.env

# Test database connection
cd backend && python -c "from database import check_db_connection; print('DB:', check_db_connection())"
```

**Expected:** All variables present, DB connection returns True

**Frontend (.env.local):**
```bash
# Check API URL configured
grep "NEXT_PUBLIC_API_URL" frontend/.env.local

# Expected: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Service Startup Test

**Start Backend:**
```bash
cd backend
python main.py
```

**Expected output:**
```
INFO     application_starting env=development
INFO     database_connected
INFO     database_initialized
INFO     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test health endpoint:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "development"
}
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```

**Expected output:**
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully
```

**Test frontend loads:**
```bash
curl http://localhost:3000
# Or open browser: http://localhost:3000
```

**Expected:** HTML response with Next.js content

---

## API Endpoint Tests

Test all 15 API endpoints manually using cURL or httpie.

### 1. Root & Health Endpoints

**Test 1.1: Root endpoint**
```bash
curl http://localhost:8000/
```

**Expected:**
```json
{
  "name": "Marketplace Listing Automation API",
  "version": "1.0.0",
  "status": "running",
  "environment": "development",
  "endpoints": {...}
}
```

**Pass criteria:** ✅ Status 200, all fields present

**Test 1.2: Health check**
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "development"
}
```

**Pass criteria:** ✅ Status 200, database connected

### 2. Import Routes (POST /api/import/webhook)

**Test 2.1: Webhook without secret (should fail)**
```bash
curl -X POST http://localhost:8000/api/import/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "allegro",
    "event_type": "product.import",
    "data": {
      "products": []
    }
  }'
```

**Expected:**
```json
{"detail": "Invalid webhook secret"}
```

**Pass criteria:** ✅ Status 401

**Test 2.2: Webhook with valid secret**
```bash
# Get webhook secret from .env
WEBHOOK_SECRET=$(grep WEBHOOK_SECRET backend/.env | cut -d '=' -f2)

curl -X POST http://localhost:8000/api/import/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $WEBHOOK_SECRET" \
  -d '{
    "source": "allegro",
    "event_type": "product.import",
    "data": {
      "products": [
        {
          "source_id": "test123",
          "title": "Test Product",
          "description": "Test description",
          "price": 99.99,
          "currency": "EUR",
          "images": ["https://example.com/img.jpg"],
          "category": "Electronics"
        }
      ]
    }
  }'
```

**Expected:**
```json
{
  "status": "success",
  "message": "Imported 1 products",
  "success_count": 1,
  "failed_count": 0
}
```

**Pass criteria:** ✅ Status 200, success_count = 1

**Test 2.3: Single product import**
```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "manual001",
    "title": "Manual Import Test",
    "description": "Manually imported product",
    "price": 49.99,
    "currency": "USD",
    "images": ["https://example.com/manual.jpg"],
    "category": "Test"
  }'
```

**Expected:**
```json
{
  "status": "success",
  "product_id": 2
}
```

**Pass criteria:** ✅ Status 200, product_id returned

**Test 2.4: Batch import**
```bash
curl -X POST "http://localhost:8000/api/import/batch?source=allegro" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "source_id": "batch001",
      "title": "Batch Product 1",
      "description": "First batch product",
      "price": 29.99,
      "currency": "EUR",
      "images": ["https://example.com/batch1.jpg"],
      "category": "Test"
    },
    {
      "source_id": "batch002",
      "title": "Batch Product 2",
      "description": "Second batch product",
      "price": 39.99,
      "currency": "EUR",
      "images": ["https://example.com/batch2.jpg"],
      "category": "Test"
    }
  ]'
```

**Expected:**
```json
{
  "status": "success",
  "success_count": 2,
  "failed_count": 0
}
```

**Pass criteria:** ✅ Status 200, both products imported

### 3. Product Routes (GET /api/products)

**Test 3.1: List all products**
```bash
curl "http://localhost:8000/api/products?page=1&page_size=20"
```

**Expected:**
```json
{
  "items": [...],
  "total": 4,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

**Pass criteria:** ✅ Status 200, items array present

**Test 3.2: Get single product**
```bash
# Use product_id from previous imports (e.g., 1)
curl http://localhost:8000/api/products/1
```

**Expected:**
```json
{
  "id": 1,
  "source_id": "test123",
  "title_original": "Test Product",
  "status": "imported",
  ...
}
```

**Pass criteria:** ✅ Status 200, product details returned

**Test 3.3: Get non-existent product**
```bash
curl http://localhost:8000/api/products/99999
```

**Expected:**
```json
{"detail": "Product not found"}
```

**Pass criteria:** ✅ Status 404

**Test 3.4: Product statistics**
```bash
curl http://localhost:8000/api/products/stats/summary
```

**Expected:**
```json
{
  "total_products": 4,
  "by_status": {
    "imported": 4,
    "optimized": 0,
    "published": 0,
    "failed": 0
  }
}
```

**Pass criteria:** ✅ Status 200, stats match expected

**Test 3.5: Filter by status**
```bash
curl "http://localhost:8000/api/products?status=imported"
```

**Expected:** List of imported products only

**Pass criteria:** ✅ Status 200, all items have status "imported"

**Test 3.6: Delete product**
```bash
curl -X DELETE http://localhost:8000/api/products/4
```

**Expected:**
```json
{
  "status": "success",
  "message": "Product deleted"
}
```

**Pass criteria:** ✅ Status 200, product removed from DB

### 4. AI Routes (POST /api/ai/optimize)

**Test 4.1: Optimize single product**
```bash
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon" \
  -H "Content-Type: application/json"
```

**Expected:**
```json
{
  "id": 1,
  "title_optimized": "Optimized title with keywords",
  "description_optimized": "Optimized description...",
  "optimization_score": 85,
  "status": "optimized",
  ...
}
```

**Pass criteria:** ✅ Status 200, optimized fields populated, score > 0

**Test 4.2: Optimize title only**
```bash
curl -X POST "http://localhost:8000/api/ai/optimize-title/1?target_marketplace=amazon"
```

**Expected:**
```json
{
  "product_id": 1,
  "original_title": "Test Product",
  "optimized_title": "Optimized title with keywords",
  "marketplace": "amazon"
}
```

**Pass criteria:** ✅ Status 200, optimized_title different from original

**Test 4.3: Optimize description only**
```bash
curl -X POST "http://localhost:8000/api/ai/optimize-description/1?target_marketplace=ebay"
```

**Expected:**
```json
{
  "product_id": 1,
  "optimized_description": "Enhanced description...",
  "marketplace": "ebay"
}
```

**Pass criteria:** ✅ Status 200, optimized description returned

**Test 4.4: Batch optimize**
```bash
curl -X POST "http://localhost:8000/api/ai/batch-optimize?target_marketplace=amazon" \
  -H "Content-Type: application/json" \
  -d '[1, 2]'
```

**Expected:**
```json
{
  "status": "completed",
  "total": 2,
  "success": 2,
  "failed": 0,
  "results": [...]
}
```

**Pass criteria:** ✅ Status 200, all products optimized successfully

**Test 4.5: Optimize non-existent product**
```bash
curl -X POST "http://localhost:8000/api/ai/optimize/99999?target_marketplace=amazon"
```

**Expected:**
```json
{"detail": "Product not found"}
```

**Pass criteria:** ✅ Status 404

### 5. Export Routes (POST /api/export/publish)

**Test 5.1: List available marketplaces**
```bash
curl http://localhost:8000/api/export/marketplaces
```

**Expected:**
```json
{
  "marketplaces": [
    {"id": "amazon", "name": "Amazon", ...},
    {"id": "ebay", "name": "eBay", ...},
    {"id": "kaufland", "name": "Kaufland", ...}
  ]
}
```

**Pass criteria:** ✅ Status 200, 3 marketplaces listed

**Test 5.2: Publish single product**
```bash
curl -X POST "http://localhost:8000/api/export/publish/1?marketplace=amazon" \
  -H "Content-Type: application/json"
```

**Expected:**
```json
{
  "status": "success",
  "product_id": 1,
  "marketplace": "amazon",
  "published_at": "2026-01-23T10:00:00"
}
```

**Pass criteria:** ✅ Status 200, product published

**Test 5.3: Bulk publish**
```bash
curl -X POST http://localhost:8000/api/export/bulk-publish \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "publish",
    "target_marketplace": "amazon",
    "product_ids": [1, 2]
  }'
```

**Expected:**
```json
{
  "id": 1,
  "job_type": "publish",
  "status": "completed",
  "total_products": 2,
  "completed_count": 2,
  "failed_count": 0
}
```

**Pass criteria:** ✅ Status 200, bulk job completed

**Test 5.4: Publish without optimization (should fail)**
```bash
# Import a new product
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "unoptimized001",
    "title": "Unoptimized Product",
    "description": "Not optimized yet",
    "price": 19.99,
    "currency": "EUR",
    "images": ["https://example.com/test.jpg"],
    "category": "Test"
  }'

# Try to publish without optimization
curl -X POST "http://localhost:8000/api/export/publish/5?marketplace=amazon"
```

**Expected:** Error or warning about missing optimization

**Pass criteria:** ✅ Appropriate error message

---

## Frontend Feature Tests

Test all 6 pages and UI features manually in browser.

### Page 1: Dashboard (/)

**Test Steps:**
1. Open http://localhost:3000/
2. Wait for page to load
3. Check all stat cards display
4. Check "Quick Actions" section present

**Expected behavior:**
- [ ] Dashboard title visible
- [ ] 8 stat cards display (Total Products, Pending, Optimized, Published, Failed, Avg Score, Recent Imports, Recent Publishes)
- [ ] Stats load from API (not hardcoded)
- [ ] Quick Actions: Import, Optimize, Publish buttons visible
- [ ] Clicking quick action navigates to correct page
- [ ] Loading state shows skeleton cards
- [ ] Error state shows red error card if API down

**Pass criteria:** All elements visible and functional

### Page 2: Products List (/products)

**Test Steps:**
1. Navigate to http://localhost:3000/products
2. Verify product table displays
3. Test pagination
4. Test filters
5. Test search

**Expected behavior:**
- [ ] Product table with columns: Title, Status, Source, Price, Actions
- [ ] Products load from API
- [ ] Pagination controls visible (if >20 products)
- [ ] Status filter dropdown works
- [ ] Source filter dropdown works
- [ ] "View Details" button navigates to product page
- [ ] "Delete" button shows confirmation modal
- [ ] Empty state shows if no products

**Pass criteria:** All table features work correctly

### Page 3: Product Details (/products/[id])

**Test Steps:**
1. Click "View Details" on a product
2. Verify all product data displays
3. Check original vs optimized comparison

**Expected behavior:**
- [ ] Product title displays
- [ ] Status badge shows correct color
- [ ] Original data section shows raw import data
- [ ] Optimized data section shows AI results (if optimized)
- [ ] Side-by-side comparison clear
- [ ] Images display correctly
- [ ] Price formatted with currency
- [ ] Timestamps formatted correctly
- [ ] "Back to Products" button works
- [ ] "Optimize" button appears if not optimized
- [ ] "Publish" button appears if optimized

**Pass criteria:** All product data displays correctly

### Page 4: Import Products (/products/import)

**Test Steps:**
1. Navigate to /products/import
2. Test manual import form
3. Test webhook instructions

**Expected behavior:**
- [ ] Page title "Import Products" visible
- [ ] Two sections: Manual Import, Webhook Setup
- [ ] Manual import form has all fields
- [ ] Required fields marked with *
- [ ] Submit button triggers API call
- [ ] Success toast shows on successful import
- [ ] Error toast shows on failure
- [ ] Webhook URL displayed with copy button
- [ ] Webhook secret instructions clear
- [ ] Sample payload provided

**Pass criteria:** Form validation works, imports successful

### Page 5: Optimize Listings (/optimize)

**Test Steps:**
1. Navigate to /optimize
2. Select products to optimize
3. Choose target marketplace
4. Run optimization

**Expected behavior:**
- [ ] Product selection table displays
- [ ] Checkboxes for multi-select
- [ ] "Select All" checkbox works
- [ ] Marketplace dropdown (Amazon, eBay, Kaufland)
- [ ] "Optimize Selected" button enabled when products selected
- [ ] Optimization runs (loading state)
- [ ] Progress indicator shows
- [ ] Success/failure results display
- [ ] Optimized products status updates
- [ ] Can view optimized products immediately

**Pass criteria:** Optimization workflow completes successfully

### Page 6: Publish to Marketplaces (/publish)

**Test Steps:**
1. Navigate to /publish
2. Select optimized products
3. Choose marketplace
4. Publish products

**Expected behavior:**
- [ ] Only optimized products shown
- [ ] Multi-select works
- [ ] Marketplace selection (Amazon, eBay, Kaufland)
- [ ] "Publish Selected" button enabled when products selected
- [ ] Confirmation modal shows before publish
- [ ] Publishing runs (loading state)
- [ ] Success/failure results display
- [ ] Published products status updates
- [ ] Error messages clear if API credentials missing

**Pass criteria:** Publishing workflow completes successfully

---

## Integration Tests

Test complete workflows from start to finish.

### Workflow 1: Import → View → Delete

**Steps:**
1. Import a product via API or UI
2. Navigate to Products page
3. Find imported product in list
4. Click "View Details"
5. Verify product data
6. Go back, click "Delete"
7. Confirm deletion
8. Verify product removed

**Expected:** Complete flow works without errors

**Pass criteria:** ✅ Product imported, viewed, deleted successfully

### Workflow 2: Import → Optimize → View Results

**Steps:**
1. Import a test product
2. Navigate to /optimize
3. Select the product
4. Choose "Amazon" as marketplace
5. Click "Optimize Selected"
6. Wait for optimization to complete
7. View product details
8. Compare original vs optimized data

**Expected:**
- Optimization completes in <10 seconds
- Title optimized (keywords added)
- Description enhanced
- Optimization score >70
- Status changed to "optimized"

**Pass criteria:** ✅ Product successfully optimized with visible improvements

### Workflow 3: Batch Import → Bulk Optimize → Bulk Publish

**Steps:**
1. Import 5 products via batch API
2. Navigate to /optimize
3. Select all 5 products
4. Optimize for "Amazon"
5. Navigate to /publish
6. Select all 5 optimized products
7. Publish to "Amazon"
8. Check all products status = "published"

**Expected:**
- Batch import successful (5/5)
- Bulk optimization successful (5/5)
- Bulk publishing successful (5/5)
- Total time <2 minutes

**Pass criteria:** ✅ All 5 products go through complete pipeline

### Workflow 4: Webhook Import → Auto-Optimize → View

**Steps:**
1. Send webhook POST with product data
2. Verify product imported (check DB or UI)
3. Run optimization on imported product
4. View optimized results

**Expected:**
- Webhook accepted (status 200)
- Product visible in UI immediately
- Optimization works on webhook-imported products

**Pass criteria:** ✅ Webhook integration works end-to-end

---

## Edge Case Tests

Test boundary conditions and error scenarios.

### Edge Case 1: Empty/Missing Data

**Test 1.1: Import product with missing required fields**
```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "incomplete001"
  }'
```

**Expected:** Validation error, clear message about missing fields

**Pass criteria:** ✅ Status 422, lists missing fields

**Test 1.2: Very long title (>500 characters)**
```bash
LONG_TITLE=$(python -c "print('A' * 600)")
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d "{
    \"source_id\": \"long001\",
    \"title\": \"$LONG_TITLE\",
    \"price\": 9.99,
    \"currency\": \"EUR\"
  }"
```

**Expected:** Either truncated or validation error

**Pass criteria:** ✅ Handled gracefully (no crash)

**Test 1.3: Special characters in title**
```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "special001",
    "title": "Test <script>alert(\"XSS\")</script> Product",
    "description": "SQL injection attempt: '\'' OR 1=1 --",
    "price": 9.99,
    "currency": "EUR"
  }'
```

**Expected:** XSS/SQL injection prevented, special chars escaped

**Pass criteria:** ✅ Data sanitized, no script execution

**Test 1.4: Negative price**
```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "negative001",
    "title": "Negative Price Test",
    "price": -9.99,
    "currency": "EUR"
  }'
```

**Expected:** Validation error (price must be positive)

**Pass criteria:** ✅ Status 422, clear error message

### Edge Case 2: Concurrent Operations

**Test 2.1: Optimize same product twice simultaneously**
```bash
# Run two optimization requests at same time
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon" &
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon" &
wait
```

**Expected:** Both complete, no data corruption

**Pass criteria:** ✅ No database locks, product optimized correctly

**Test 2.2: Delete product while optimizing**
```bash
# Start optimization
curl -X POST "http://localhost:8000/api/ai/optimize/2?target_marketplace=amazon" &

# Immediately delete
sleep 1
curl -X DELETE http://localhost:8000/api/products/2
```

**Expected:** Either optimization fails gracefully or completes before deletion

**Pass criteria:** ✅ No server crash, appropriate error handling

### Edge Case 3: Large Batch Operations

**Test 3.1: Import 100 products at once**
```bash
# Generate 100 product JSON objects
python -c "
import json
products = [{
    'source_id': f'batch{i:03d}',
    'title': f'Bulk Product {i}',
    'price': 9.99 + i,
    'currency': 'EUR'
} for i in range(100)]
print(json.dumps(products))
" > /tmp/bulk_products.json

curl -X POST "http://localhost:8000/api/import/batch?source=test" \
  -H "Content-Type: application/json" \
  -d @/tmp/bulk_products.json
```

**Expected:** All 100 imported successfully (or with clear error limit)

**Pass criteria:** ✅ Response within 30 seconds, success count = 100

**Test 3.2: Optimize 50 products at once**
```bash
# Get first 50 product IDs
PRODUCT_IDS=$(curl -s "http://localhost:8000/api/products?page_size=50" | \
  python -c "import sys, json; print(json.dumps([p['id'] for p in json.load(sys.stdin)['items']]))")

curl -X POST "http://localhost:8000/api/ai/batch-optimize?target_marketplace=amazon" \
  -H "Content-Type: application/json" \
  -d "$PRODUCT_IDS"
```

**Expected:** Completes within reasonable time (<5 minutes), all optimized

**Pass criteria:** ✅ No timeout, all products processed

### Edge Case 4: Invalid Marketplace Credentials

**Test 4.1: Publish without Amazon credentials**
```bash
# Temporarily remove Amazon credentials from .env
# Then try to publish
curl -X POST "http://localhost:8000/api/export/publish/1?marketplace=amazon"
```

**Expected:** Clear error message about missing credentials

**Pass criteria:** ✅ Status 400/500, error explains missing credentials

### Edge Case 5: Groq API Failures

**Test 5.1: Invalid Groq API key**
```bash
# Temporarily set invalid Groq key in .env
# Then try optimization
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon"
```

**Expected:** Clear error message about API authentication failure

**Pass criteria:** ✅ Status 500, error mentions API key issue

**Test 5.2: Groq rate limit hit**
```bash
# Send many optimization requests rapidly
for i in {1..20}; do
  curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon" &
done
wait
```

**Expected:** Some requests may fail with rate limit error

**Pass criteria:** ✅ Graceful handling, clear rate limit message

---

## Performance Tests

Measure response times and throughput.

### Performance Test 1: API Response Times

**Measure p50, p95, p99 response times for key endpoints.**

**Setup:**
```bash
# Install Apache Bench (if not installed)
# macOS: brew install httpd
# Linux: apt-get install apache2-utils
```

**Test 1.1: Health check (baseline)**
```bash
ab -n 1000 -c 10 http://localhost:8000/health
```

**Expected:**
- p50: <10ms
- p95: <50ms
- p99: <100ms

**Pass criteria:** ✅ p95 < 50ms

**Test 1.2: List products**
```bash
ab -n 100 -c 5 "http://localhost:8000/api/products?page=1&page_size=20"
```

**Expected:**
- p50: <100ms
- p95: <500ms
- p99: <1000ms

**Pass criteria:** ✅ p95 < 500ms

**Test 1.3: Single product optimization**
```bash
# Manual test (ab doesn't work well with POST)
time curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon"
```

**Expected:** <10 seconds (depends on Groq API)

**Pass criteria:** ✅ Completes in <10s

**Test 1.4: Batch optimization (10 products)**
```bash
time curl -X POST "http://localhost:8000/api/ai/batch-optimize?target_marketplace=amazon" \
  -H "Content-Type: application/json" \
  -d '[1,2,3,4,5,6,7,8,9,10]'
```

**Expected:** <60 seconds for 10 products

**Pass criteria:** ✅ <6s per product average

### Performance Test 2: Frontend Load Times

**Measure using browser DevTools.**

**Test 2.1: Dashboard page load**
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Navigate to http://localhost:3000/
4. Check "DOMContentLoaded" time

**Expected:** <1 second

**Pass criteria:** ✅ DOMContentLoaded < 1s

**Test 2.2: Products page with 100 items**
1. Import 100 products (see edge case test)
2. Navigate to /products
3. Measure load time

**Expected:** <2 seconds

**Pass criteria:** ✅ Page interactive < 2s

**Test 2.3: Product details page**
1. Navigate to /products/1
2. Measure time to full content load

**Expected:** <500ms

**Pass criteria:** ✅ Full load < 500ms

### Performance Test 3: Database Query Performance

**Test database queries directly.**

**Setup:**
```bash
cd backend
python
```

**Test 3.1: List products query**
```python
from database import SessionLocal
from models import Product
import time

db = SessionLocal()
start = time.time()
products = db.query(Product).limit(100).all()
elapsed = time.time() - start
print(f"Query time: {elapsed:.3f}s")
```

**Expected:** <100ms for 100 products

**Pass criteria:** ✅ Query < 100ms

**Test 3.2: Stats aggregation**
```python
from database import SessionLocal
from models import Product, ProductStatus
import time

db = SessionLocal()
start = time.time()
total = db.query(Product).count()
by_status = {status: db.query(Product).filter(Product.status == status).count()
             for status in ProductStatus}
elapsed = time.time() - start
print(f"Stats query time: {elapsed:.3f}s")
```

**Expected:** <500ms

**Pass criteria:** ✅ Aggregation < 500ms

### Performance Test 4: Concurrent Users

**Simulate multiple users accessing the system.**

**Test 4.1: 10 concurrent users listing products**
```bash
ab -n 100 -c 10 "http://localhost:8000/api/products?page=1&page_size=20"
```

**Expected:** All requests successful, no errors

**Pass criteria:** ✅ 100% success rate, no 500 errors

**Test 4.2: 5 concurrent optimizations**
```bash
# Run 5 optimizations simultaneously
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/ai/optimize/$i?target_marketplace=amazon" &
done
wait
```

**Expected:** All complete successfully

**Pass criteria:** ✅ All 5 succeed, total time <30s

---

## Browser Compatibility

Test across major browsers and versions.

### Browsers to Test

- [ ] **Chrome** (latest)
- [ ] **Firefox** (latest)
- [ ] **Safari** (latest, macOS only)
- [ ] **Edge** (latest)

### Test Checklist (per browser)

**Basic Functionality:**
- [ ] Dashboard loads correctly
- [ ] Navigation between pages works
- [ ] Forms submit correctly
- [ ] Buttons clickable
- [ ] Dropdowns work
- [ ] Modals open/close
- [ ] Toasts/notifications appear

**Visual Consistency:**
- [ ] Dark mode colors correct
- [ ] Borders and spacing consistent
- [ ] Icons display properly
- [ ] Tables formatted correctly
- [ ] Cards aligned properly

**API Integration:**
- [ ] API calls succeed
- [ ] Loading states show
- [ ] Error states display
- [ ] Data updates in real-time

**Pass criteria:** ✅ All features work identically across browsers

### Known Browser Issues

**Document any browser-specific bugs here:**

_Example:_
- Safari: Toast notifications don't auto-dismiss (need to fix CSS)
- Firefox: Dropdown arrow slightly misaligned (cosmetic only)

---

## Mobile Responsiveness

Test on mobile devices and small screens.

### Devices to Test

- [ ] **iPhone** (iOS Safari)
- [ ] **Android phone** (Chrome)
- [ ] **iPad** (Safari)
- [ ] **Desktop at 320px width** (DevTools mobile emulation)

### Test Checklist (per device)

**Layout:**
- [ ] Dashboard cards stack vertically
- [ ] Product table scrolls horizontally or stacks
- [ ] Navigation menu collapses to hamburger
- [ ] Forms fit within viewport
- [ ] Buttons large enough to tap (min 44px)

**Functionality:**
- [ ] Touch targets work (no hover-only features)
- [ ] Pinch-to-zoom disabled (or enabled as appropriate)
- [ ] Virtual keyboard doesn't break layout
- [ ] Modals fit within screen
- [ ] Dropdowns accessible

**Performance:**
- [ ] Pages load quickly on 4G
- [ ] Images sized appropriately
- [ ] No excessive data transfer

**Pass criteria:** ✅ All core features usable on mobile

### Mobile Testing Tool

**Use Chrome DevTools:**
1. Open DevTools (F12)
2. Click "Toggle Device Toolbar" (Ctrl+Shift+M)
3. Select device: iPhone 12 Pro, Pixel 5, iPad Pro
4. Test all pages and features

### Responsive Breakpoints to Verify

- [ ] **320px** - Small phone (iPhone SE)
- [ ] **375px** - Standard phone (iPhone 12)
- [ ] **768px** - Tablet (iPad)
- [ ] **1024px** - Desktop
- [ ] **1440px** - Large desktop

**Pass criteria:** ✅ Layout adapts correctly at each breakpoint

---

## Test Reporting

### Test Session Report Template

```
# Test Session Report

**Date:** YYYY-MM-DD
**Tester:** Name
**Environment:** Development/Staging/Production
**Version:** 1.0.0

## Test Summary
- Total Tests: X
- Passed: X
- Failed: X
- Skipped: X
- Pass Rate: X%

## Failed Tests
| Test ID | Description | Expected | Actual | Severity |
|---------|-------------|----------|--------|----------|
| T1.2    | Health check | Status 200 | Status 500 | High |

## Bugs Found
| Bug ID | Title | Steps to Reproduce | Severity | Status |
|--------|-------|-------------------|----------|--------|
| B001   | Dashboard crashes on empty DB | 1. Clear DB, 2. Load dashboard | Critical | Open |

## Performance Notes
- Dashboard load time: X ms
- API response time (p95): X ms
- Optimization time (single): X s

## Recommendations
1. Fix critical bug B001 before deployment
2. Improve dashboard error handling
3. Add loading states to optimize page

## Sign-off
- [ ] All critical tests passed
- [ ] No blocker bugs
- [ ] Performance acceptable
- [ ] Ready for next stage

**Tester Signature:** _______________
**Date:** _______________
```

---

## Quick Smoke Test Checklist

**Use this for rapid verification after code changes.**

**Backend (5 minutes):**
- [ ] Backend starts without errors
- [ ] /health returns "healthy"
- [ ] Can import a product
- [ ] Can optimize a product
- [ ] Can list products
- [ ] Database connected

**Frontend (5 minutes):**
- [ ] Frontend starts without errors
- [ ] Dashboard loads and shows stats
- [ ] Can navigate to all pages
- [ ] Products page shows data
- [ ] Import form works
- [ ] No console errors

**Pass criteria:** ✅ All checks pass = Safe to proceed

---

## Test Data Cleanup

**After testing, clean up test data:**

```bash
# Connect to Supabase and delete test products
curl -X DELETE http://localhost:8000/api/products/1
curl -X DELETE http://localhost:8000/api/products/2
# ... or truncate table in Supabase dashboard

# Or use SQL directly
psql $DATABASE_URL -c "DELETE FROM products WHERE source_id LIKE 'test%';"
```

**Important:** Don't delete test data in production!

---

## Conclusion

This testing guide provides comprehensive manual testing procedures following David's philosophy:
- No formal test frameworks (pytest/jest)
- Realistic user scenarios
- Clear pass/fail criteria
- Easy to execute manually
- Focus on actual user workflows

**Remember:**
- Test after every meaningful change
- Document any deviations from expected behavior
- Update this guide as features evolve
- Security is critical - verify all endpoints protected

**Next Steps:**
1. Execute all tests in this guide
2. Document results in Test Session Report
3. File bugs for any failures
4. Retest after fixes
5. Sign off when all critical tests pass
