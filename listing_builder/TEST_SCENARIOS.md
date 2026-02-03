# Test Scenarios - Realistic User Workflows

**Version:** 1.0.0
**Last Updated:** 2026-01-23

This document contains realistic user scenarios for testing the Marketplace Listing Automation System. Each scenario represents actual user workflows from import to publish.

---

## Table of Contents

1. [Scenario 1: Import Product from n8n Webhook](#scenario-1-import-product-from-n8n-webhook)
2. [Scenario 2: Manual Single Product Import](#scenario-2-manual-single-product-import)
3. [Scenario 3: Batch Import (10+ Products)](#scenario-3-batch-import-10-products)
4. [Scenario 4: AI Optimization (Single Product)](#scenario-4-ai-optimization-single-product)
5. [Scenario 5: Bulk AI Optimization (5+ Products)](#scenario-5-bulk-ai-optimization-5-products)
6. [Scenario 6: Publish to Single Marketplace](#scenario-6-publish-to-single-marketplace)
7. [Scenario 7: Bulk Publish to Multiple Marketplaces](#scenario-7-bulk-publish-to-multiple-marketplaces)
8. [Scenario 8: Error Handling](#scenario-8-error-handling)

---

## Scenario 1: Import Product from n8n Webhook

### User Story
*As a seller, I have a web scraper running in n8n that finds trending products on Allegro. When a new product is found, it should automatically import into the system for me to review and optimize.*

### Preconditions
- n8n workflow configured
- Webhook secret configured in both systems
- Backend API running

### Test Data
```json
{
  "source": "allegro",
  "event_type": "product.import",
  "data": {
    "products": [
      {
        "source_id": "allegro_12345678",
        "title": "Bezprzewodowe słuchawki Bluetooth 5.0 - HiFi Stereo",
        "description": "Wysokiej jakości bezprzewodowe słuchawki z aktywną redukcją szumu. Czas działania: 24h. Wodoodporne IPX7.",
        "price": 129.99,
        "currency": "PLN",
        "images": [
          "https://example.com/headphones1.jpg",
          "https://example.com/headphones2.jpg",
          "https://example.com/headphones3.jpg"
        ],
        "category": "Electronics > Audio > Headphones",
        "attributes": {
          "brand": "NoName",
          "color": "Black",
          "connectivity": "Bluetooth 5.0",
          "battery_life": "24 hours"
        }
      }
    ]
  }
}
```

### Steps to Test

**1. Configure n8n webhook (or simulate with cURL)**

```bash
# Get webhook secret from backend/.env
WEBHOOK_SECRET=$(grep WEBHOOK_SECRET backend/.env | cut -d '=' -f2)

# Send webhook POST
curl -X POST http://localhost:8000/api/import/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $WEBHOOK_SECRET" \
  -d '{
    "source": "allegro",
    "event_type": "product.import",
    "data": {
      "products": [
        {
          "source_id": "allegro_12345678",
          "title": "Bezprzewodowe słuchawki Bluetooth 5.0 - HiFi Stereo",
          "description": "Wysokiej jakości bezprzewodowe słuchawki z aktywną redukcją szumu. Czas działania: 24h. Wodoodporne IPX7.",
          "price": 129.99,
          "currency": "PLN",
          "images": [
            "https://example.com/headphones1.jpg",
            "https://example.com/headphones2.jpg"
          ],
          "category": "Electronics"
        }
      ]
    }
  }'
```

**2. Verify import in backend logs**

```
INFO     webhook_received source=allegro event=product.import
INFO     product_imported product_id=1 source_id=allegro_12345678
```

**3. Check frontend dashboard**
- Open http://localhost:3000/
- Verify "Total Products" count increased by 1
- Verify "Recent Imports" shows 1

**4. View imported product**
- Navigate to http://localhost:3000/products
- Find product in list (should be first row)
- Check status: "imported"
- Click "View Details"
- Verify all fields populated correctly

### Expected Results

- ✅ Webhook returns status 200
- ✅ Product visible in database
- ✅ Product appears in frontend immediately
- ✅ All fields mapped correctly (title, price, images)
- ✅ Status = "imported"
- ✅ Source = "allegro"
- ✅ Created timestamp is recent (<1 minute)

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Wrong webhook secret | Check .env file |
| 400 Bad Request | Missing required fields | Verify JSON structure |
| 500 Internal Error | Database connection | Check Supabase connection |
| Product not visible | Frontend cache | Refresh page (F5) |

---

## Scenario 2: Manual Single Product Import

### User Story
*As a seller, I found a product manually that I want to list. I want to import it through the UI without using the scraper.*

### Preconditions
- Frontend running
- Backend API running
- Browser open to import page

### Test Data
```
Source ID: manual_001
Title: Vintage Leather Wallet - Handmade RFID Blocking
Description: Premium full-grain leather wallet with RFID protection. 8 card slots, 2 bill compartments. Handcrafted in Italy.
Price: 89.99
Currency: EUR
Images:
  - https://example.com/wallet1.jpg
  - https://example.com/wallet2.jpg
Category: Fashion > Accessories > Wallets
```

### Steps to Test

**1. Navigate to import page**
- Go to http://localhost:3000/products/import
- Verify form displays with all fields

**2. Fill out form**
- Source ID: `manual_001`
- Title: `Vintage Leather Wallet - Handmade RFID Blocking`
- Description: `Premium full-grain leather wallet with RFID protection. 8 card slots, 2 bill compartments. Handcrafted in Italy.`
- Price: `89.99`
- Currency: Select "EUR" from dropdown
- Category: `Fashion`
- Images: Paste URLs (one per line or comma-separated)

**3. Submit form**
- Click "Import Product" button
- Wait for loading indicator

**4. Verify success**
- Success toast notification appears
- Form resets to empty
- Can navigate to products page and find new product

**5. Alternative: Test via API**
```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "manual_001",
    "title": "Vintage Leather Wallet - Handmade RFID Blocking",
    "description": "Premium full-grain leather wallet with RFID protection. 8 card slots, 2 bill compartments. Handcrafted in Italy.",
    "price": 89.99,
    "currency": "EUR",
    "images": [
      "https://example.com/wallet1.jpg",
      "https://example.com/wallet2.jpg"
    ],
    "category": "Fashion"
  }'
```

### Expected Results

- ✅ Form validation works (required fields marked)
- ✅ Price accepts decimal values
- ✅ Currency dropdown populated correctly
- ✅ Can paste multiple image URLs
- ✅ Success notification shows "Product imported successfully"
- ✅ Product appears in products list immediately
- ✅ All data saved correctly
- ✅ Status = "imported"

### Validation Tests

**Test missing required fields:**
- Leave title empty → Error: "Title is required"
- Leave price empty → Error: "Price is required"
- Invalid price (negative) → Error: "Price must be positive"
- Invalid currency (not 3 letters) → Error: "Invalid currency code"

**Test edge cases:**
- Very long title (500+ chars) → Should truncate or show error
- Special characters in title → Should sanitize/escape
- Invalid image URL → Should validate or skip
- Price with more than 2 decimals → Should round

---

## Scenario 3: Batch Import (10+ Products)

### User Story
*As a seller, I scraped 20 products from a competitor and want to import them all at once to optimize and list on my stores.*

### Preconditions
- Have CSV or JSON file with product data
- Backend API running

### Test Data

Create file: `/tmp/batch_products.json`

```json
[
  {
    "source_id": "batch_001",
    "title": "Wireless Mouse Bluetooth Silent Click",
    "description": "Ergonomic wireless mouse with silent buttons. 6 months battery life.",
    "price": 24.99,
    "currency": "EUR",
    "images": ["https://example.com/mouse1.jpg"],
    "category": "Electronics"
  },
  {
    "source_id": "batch_002",
    "title": "USB-C Hub 7-in-1 Adapter",
    "description": "7-port USB-C hub with HDMI, USB 3.0, SD card reader.",
    "price": 39.99,
    "currency": "EUR",
    "images": ["https://example.com/hub1.jpg"],
    "category": "Electronics"
  },
  {
    "source_id": "batch_003",
    "title": "Mechanical Keyboard RGB Gaming",
    "description": "Gaming keyboard with Cherry MX switches and RGB backlight.",
    "price": 89.99,
    "currency": "EUR",
    "images": ["https://example.com/keyboard1.jpg"],
    "category": "Electronics"
  },
  {
    "source_id": "batch_004",
    "title": "Webcam 1080p HD with Microphone",
    "description": "Full HD webcam with built-in noise-canceling microphone.",
    "price": 59.99,
    "currency": "EUR",
    "images": ["https://example.com/webcam1.jpg"],
    "category": "Electronics"
  },
  {
    "source_id": "batch_005",
    "title": "Laptop Stand Aluminum Adjustable",
    "description": "Ergonomic laptop stand with 6 height adjustments.",
    "price": 34.99,
    "currency": "EUR",
    "images": ["https://example.com/stand1.jpg"],
    "category": "Office"
  },
  {
    "source_id": "batch_006",
    "title": "Monitor Arm Dual Screen Mount",
    "description": "Heavy-duty monitor arm for two 27-inch screens.",
    "price": 79.99,
    "currency": "EUR",
    "images": ["https://example.com/arm1.jpg"],
    "category": "Office"
  },
  {
    "source_id": "batch_007",
    "title": "Cable Management Box White",
    "description": "Hide and organize cables with this sleek box.",
    "price": 19.99,
    "currency": "EUR",
    "images": ["https://example.com/cablebox1.jpg"],
    "category": "Office"
  },
  {
    "source_id": "batch_008",
    "title": "Desk Lamp LED Dimmable Touch Control",
    "description": "Modern LED desk lamp with touch dimmer and USB port.",
    "price": 44.99,
    "currency": "EUR",
    "images": ["https://example.com/lamp1.jpg"],
    "category": "Office"
  },
  {
    "source_id": "batch_009",
    "title": "Phone Holder Car Mount Magnetic",
    "description": "Strong magnetic car mount for phones and GPS devices.",
    "price": 14.99,
    "currency": "EUR",
    "images": ["https://example.com/mount1.jpg"],
    "category": "Automotive"
  },
  {
    "source_id": "batch_010",
    "title": "Portable Charger 20000mAh Power Bank",
    "description": "High-capacity power bank with fast charging and dual USB ports.",
    "price": 49.99,
    "currency": "EUR",
    "images": ["https://example.com/powerbank1.jpg"],
    "category": "Electronics"
  }
]
```

### Steps to Test

**1. Import via API**

```bash
curl -X POST "http://localhost:8000/api/import/batch?source=manual" \
  -H "Content-Type: application/json" \
  -d @/tmp/batch_products.json
```

**2. Monitor backend logs**
```
INFO     batch_import_started count=10 source=manual
INFO     product_imported product_id=1 source_id=batch_001
INFO     product_imported product_id=2 source_id=batch_002
...
INFO     batch_import_completed success=10 failed=0
```

**3. Check API response**
```json
{
  "status": "success",
  "success_count": 10,
  "failed_count": 0,
  "results": [...]
}
```

**4. Verify in frontend**
- Dashboard shows +10 products
- Products page shows all 10 products
- All have status "imported"
- All have source "manual"

### Performance Expectations

| Metric | Expected | Acceptable | Unacceptable |
|--------|----------|------------|--------------|
| Import time (10 products) | <2 seconds | <5 seconds | >10 seconds |
| Database writes | Transactional | Eventual consistency | Data loss |
| API response | 200 OK | 207 Multi-Status | 500 Error |
| Memory usage | <50MB increase | <100MB | >200MB |

### Expected Results

- ✅ All 10 products imported successfully
- ✅ API returns `success_count: 10, failed_count: 0`
- ✅ No duplicate `source_id` errors
- ✅ Dashboard stats update correctly
- ✅ Products page shows all 10 (with pagination if needed)
- ✅ Total time <5 seconds

### Error Handling Tests

**Test duplicate `source_id`:**
```bash
# Import same batch twice
curl -X POST "http://localhost:8000/api/import/batch?source=manual" \
  -d @/tmp/batch_products.json

# Second import should fail or skip duplicates
```

**Expected:** Either reject duplicates or update existing products

**Test partial failure (invalid data):**
Create file with 1 invalid product among 10 valid ones.

**Expected:**
- 9 products imported successfully
- 1 product failed with clear error message
- API returns `success_count: 9, failed_count: 1`

---

## Scenario 4: AI Optimization (Single Product)

### User Story
*As a seller, I imported a product from Allegro with a Polish title and description. I want to optimize it for Amazon with English text, better keywords, and compliance with Amazon's guidelines.*

### Preconditions
- Product already imported (from Scenario 1 or 2)
- Groq API key configured
- Backend AI service running

### Test Data
Use product from Scenario 1:
- Product ID: 1
- Title: "Bezprzewodowe słuchawki Bluetooth 5.0 - HiFi Stereo"
- Target marketplace: Amazon
- Target language: English

### Steps to Test

**Option A: Via API (fastest)**

```bash
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon" \
  -H "Content-Type: application/json"
```

**Option B: Via Frontend**

1. Navigate to http://localhost:3000/optimize
2. Find product in table (ID: 1)
3. Check the checkbox next to product
4. Select "Amazon" from marketplace dropdown
5. Click "Optimize Selected" button
6. Wait for progress indicator (estimated 5-10 seconds)
7. See success notification

**Option C: Via Product Details Page**

1. Navigate to http://localhost:3000/products/1
2. Click "Optimize for Amazon" button
3. Wait for optimization to complete
4. Page refreshes with optimized data

### What to Observe

**During optimization:**
- Loading indicator shows
- Backend logs show Groq API calls
- Frontend shows "Optimizing..." status

**After optimization:**
- Status changes from "imported" to "optimized"
- Optimization score displayed (e.g., 85%)
- Side-by-side comparison visible:
  - Original (Polish) vs Optimized (English)
  - Original title vs Optimized title (with keywords)
  - Original description vs Optimized description (with bullet points)

### Expected Results

**Title Optimization:**
- ✅ Translated to English
- ✅ Keywords added (Wireless, Bluetooth, Headphones, Noise Cancelling)
- ✅ Follows Amazon format (Brand + Product Type + Key Features)
- ✅ Within Amazon limits (200 characters)

**Example:**
- **Before:** Bezprzewodowe słuchawki Bluetooth 5.0 - HiFi Stereo
- **After:** Wireless Bluetooth Headphones 5.0 with Active Noise Cancelling, 24H Battery, IPX7 Waterproof, Hi-Fi Stereo Sound

**Description Optimization:**
- ✅ Translated to English
- ✅ Formatted with bullet points
- ✅ Highlights key features and benefits
- ✅ Within Amazon limits (2000 characters)
- ✅ Includes SEO keywords naturally

**Example:**
```
Premium Wireless Bluetooth Headphones - Your Perfect Audio Companion

KEY FEATURES:
• Advanced Bluetooth 5.0 technology for stable connection up to 30 feet
• Active Noise Cancellation (ANC) blocks up to 95% of ambient noise
• 24-hour battery life with quick charge support (10 min = 2 hours)
• IPX7 waterproof rating - perfect for sports and outdoor activities
• Hi-Fi stereo sound with deep bass and crystal clear highs

COMFORTABLE ALL-DAY WEAR:
Soft memory foam ear cushions and adjustable headband ensure comfortable wear for hours. Lightweight design (only 180g) makes them perfect for travel, work, or leisure.

UNIVERSAL COMPATIBILITY:
Works seamlessly with iPhone, Android, iPad, laptop, tablet, and all Bluetooth-enabled devices. Also includes 3.5mm aux cable for wired connection.

WHAT'S IN THE BOX:
• Bluetooth Headphones
• USB-C Charging Cable
• 3.5mm Audio Cable
• Carrying Case
• User Manual
```

**Optimization Score:**
- ✅ Score between 70-100%
- ✅ Breakdown by category (optional):
  - Title quality: 90%
  - Description quality: 85%
  - Keyword density: 80%
  - Compliance: 95%

### Performance Expectations

| Metric | Expected | Acceptable | Unacceptable |
|--------|----------|------------|--------------|
| Optimization time | <5 seconds | <10 seconds | >30 seconds |
| Groq API calls | 1-2 calls | 3-4 calls | >5 calls |
| Title length | 150-200 chars | 100-250 chars | >250 chars |
| Description length | 1000-1500 chars | 500-2000 chars | >2500 chars |

### Error Scenarios to Test

**Test 1: Optimize non-existent product**
```bash
curl -X POST "http://localhost:8000/api/ai/optimize/99999?target_marketplace=amazon"
```
**Expected:** 404 Not Found

**Test 2: Invalid marketplace**
```bash
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=invalid"
```
**Expected:** 400 Bad Request or validation error

**Test 3: Groq API error (simulate)**
- Temporarily set invalid Groq API key
- Try optimization
**Expected:** 500 error with clear message "AI service unavailable"

**Test 4: Optimize already optimized product**
```bash
# Optimize twice
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon"
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon"
```
**Expected:** Should re-optimize or return existing optimization

---

## Scenario 5: Bulk AI Optimization (5+ Products)

### User Story
*As a seller, I imported 10 products and want to optimize all of them for Amazon at once instead of one by one.*

### Preconditions
- 10 products imported (from Scenario 3)
- Groq API key configured
- Sufficient Groq API credits

### Test Data
Product IDs: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
Target marketplace: Amazon

### Steps to Test

**Option A: Via API**

```bash
curl -X POST "http://localhost:8000/api/ai/batch-optimize?target_marketplace=amazon" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]'
```

**Option B: Via Frontend**

1. Navigate to http://localhost:3000/optimize
2. Click "Select All" checkbox (or select 10 products individually)
3. Verify 10 products selected (counter shows "10 selected")
4. Select "Amazon" from marketplace dropdown
5. Click "Optimize Selected (10)" button
6. See progress bar (e.g., "Optimizing 3/10...")
7. Wait for completion (estimated 30-60 seconds)
8. See results summary

### What to Observe

**During bulk optimization:**
- Progress indicator updates (1/10, 2/10, etc.)
- Backend processes products sequentially or in parallel
- Groq API rate limits may apply
- Frontend shows loading state

**After completion:**
- Results summary shows:
  - Total: 10
  - Successful: 10
  - Failed: 0
- Each product status updated to "optimized"
- Optimization scores visible for each product

### Expected Results

**API Response:**
```json
{
  "status": "completed",
  "total": 10,
  "success": 10,
  "failed": 0,
  "results": [
    {
      "product_id": 1,
      "status": "success",
      "score": 87
    },
    {
      "product_id": 2,
      "status": "success",
      "score": 91
    },
    ...
  ]
}
```

**Performance:**
- ✅ All 10 products optimized
- ✅ Total time: <60 seconds (average 6s per product)
- ✅ No timeouts
- ✅ No API errors

**Data Quality:**
- ✅ All titles optimized correctly
- ✅ All descriptions optimized
- ✅ All optimization scores >70%
- ✅ No duplicate content (each unique)

### Performance Expectations

| Metric | Expected | Acceptable | Unacceptable |
|--------|----------|------------|--------------|
| Total time (10 products) | <60 seconds | <120 seconds | >180 seconds |
| Average time per product | <6 seconds | <12 seconds | >20 seconds |
| Success rate | 100% | >90% | <80% |
| Groq API errors | 0 | <2 | >3 |

### Error Scenarios

**Test partial failure:**
- Include 1 invalid product ID in batch
**Expected:**
- 9 successful, 1 failed
- Failed product shows clear error
- Successful products still saved

**Test Groq rate limit:**
- Send 50 optimization requests rapidly
**Expected:**
- Some requests may queue or retry
- Appropriate error message if rate limit hit
- Successful requests still complete

**Test timeout:**
- Set artificially low timeout (e.g., 5 seconds)
- Optimize 10 products
**Expected:**
- Timeout error with clear message
- Partial results saved (if some completed)

---

## Scenario 6: Publish to Single Marketplace

### User Story
*As a seller, I optimized a product for Amazon. Now I want to publish it to Amazon using my API credentials.*

### Preconditions
- Product optimized for Amazon (from Scenario 4)
- Amazon API credentials configured in .env
- Product status = "optimized"

### Test Data
- Product ID: 1
- Marketplace: Amazon
- Region: EU-WEST-1

### Steps to Test

**Option A: Via API**

```bash
curl -X POST "http://localhost:8000/api/export/publish/1?marketplace=amazon" \
  -H "Content-Type: application/json"
```

**Option B: Via Frontend**

1. Navigate to http://localhost:3000/publish
2. Find product ID 1 in table (should show status "optimized")
3. Check checkbox next to product
4. Select "Amazon" from marketplace dropdown
5. Click "Publish Selected (1)" button
6. Confirm in modal: "Are you sure you want to publish 1 product to Amazon?"
7. Click "Confirm"
8. Wait for publishing to complete

### What to Observe

**During publishing:**
- Loading indicator shows
- Backend calls Amazon API
- Frontend shows "Publishing..." status

**After publishing:**
- Status changes to "published"
- Published timestamp displayed
- Marketplace badge shows "Amazon"
- External listing URL visible (if provided by Amazon)

### Expected Results

**API Response:**
```json
{
  "status": "success",
  "product_id": 1,
  "marketplace": "amazon",
  "published_at": "2026-01-23T10:30:00Z",
  "external_id": "B09XYZ123",
  "listing_url": "https://amazon.com/dp/B09XYZ123"
}
```

**Database:**
- ✅ Product status updated to "published"
- ✅ `published_at` timestamp saved
- ✅ `marketplace` field = "amazon"
- ✅ `external_id` saved (Amazon ASIN)

**Frontend:**
- ✅ Success notification: "Product published to Amazon successfully"
- ✅ Product details page shows published status
- ✅ "View on Amazon" link available

### Marketplace-Specific Tests

**Amazon:**
- ✅ Title within 200 characters
- ✅ Description within 2000 characters
- ✅ Price formatted correctly (USD/EUR)
- ✅ Images uploaded (primary + up to 8 additional)
- ✅ Category mapped correctly

**eBay:**
- ✅ Title within 80 characters
- ✅ Description HTML formatted
- ✅ Payment methods configured
- ✅ Shipping options set

**Kaufland:**
- ✅ EAN/GTIN provided
- ✅ German description
- ✅ VAT included in price

### Error Scenarios

**Test 1: Publish without optimization**
```bash
# Import new product (not optimized)
curl -X POST http://localhost:8000/api/import/product \
  -d '{"source_id":"unoptimized","title":"Test","price":9.99,"currency":"EUR"}'

# Try to publish immediately
curl -X POST "http://localhost:8000/api/export/publish/11?marketplace=amazon"
```
**Expected:** Error or warning "Product not optimized for Amazon"

**Test 2: Invalid marketplace credentials**
```bash
# Temporarily remove Amazon credentials from .env
# Try to publish
curl -X POST "http://localhost:8000/api/export/publish/1?marketplace=amazon"
```
**Expected:** 400 Bad Request "Amazon credentials not configured"

**Test 3: Amazon API error (simulate)**
- Network timeout
- Invalid ASIN
- Product already exists
**Expected:** Clear error message, product status remains "optimized"

---

## Scenario 7: Bulk Publish to Multiple Marketplaces

### User Story
*As a seller, I optimized 10 products. I want to publish all of them to Amazon, eBay, and Kaufland at once.*

### Preconditions
- 10 products optimized (from Scenario 5)
- API credentials for all 3 marketplaces configured
- Products have status "optimized"

### Test Data
- Product IDs: 1-10
- Marketplaces: Amazon, eBay, Kaufland

### Steps to Test

**Approach 1: Publish to one marketplace at a time**

```bash
# Publish all 10 to Amazon
curl -X POST http://localhost:8000/api/export/bulk-publish \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "publish",
    "target_marketplace": "amazon",
    "product_ids": [1,2,3,4,5,6,7,8,9,10]
  }'

# Wait for completion, then publish to eBay
curl -X POST http://localhost:8000/api/export/bulk-publish \
  -d '{
    "job_type": "publish",
    "target_marketplace": "ebay",
    "product_ids": [1,2,3,4,5,6,7,8,9,10]
  }'

# Wait, then publish to Kaufland
curl -X POST http://localhost:8000/api/export/bulk-publish \
  -d '{
    "job_type": "publish",
    "target_marketplace": "kaufland",
    "product_ids": [1,2,3,4,5,6,7,8,9,10]
  }'
```

**Approach 2: Via Frontend (multi-marketplace)**

1. Navigate to http://localhost:3000/publish
2. Select all 10 products (checkbox)
3. **Multi-marketplace publishing:**
   - Option A: Publish to Amazon first, then repeat for eBay, Kaufland
   - Option B: Select multiple marketplaces at once (if UI supports)
4. Confirm each bulk publish operation
5. Monitor progress

### Expected Results

**Per marketplace:**
```json
{
  "id": 1,
  "job_type": "publish",
  "target_marketplace": "amazon",
  "status": "completed",
  "total_products": 10,
  "completed_count": 10,
  "failed_count": 0,
  "results": [...]
}
```

**Database state after all 3 marketplaces:**
- ✅ Each product has 3 marketplace entries
- ✅ Products show on Amazon, eBay, Kaufland
- ✅ Each has unique `external_id` per marketplace
- ✅ All published_at timestamps recorded

**Frontend:**
- ✅ Dashboard shows "Published: 30" (10 products × 3 marketplaces)
- ✅ Product details show 3 marketplace badges
- ✅ "View on Amazon", "View on eBay", "View on Kaufland" links

### Performance Expectations

| Metric | Expected | Acceptable | Unacceptable |
|--------|----------|------------|--------------|
| Time per marketplace | <2 minutes | <5 minutes | >10 minutes |
| Total time (3 marketplaces) | <6 minutes | <15 minutes | >30 minutes |
| Success rate | 100% | >90% | <80% |

### Conflict Scenarios

**Test 1: Publish same product twice**
```bash
# Publish to Amazon
curl -X POST "http://localhost:8000/api/export/publish/1?marketplace=amazon"

# Publish again
curl -X POST "http://localhost:8000/api/export/publish/1?marketplace=amazon"
```
**Expected:**
- Option A: Update existing listing (re-publish)
- Option B: Error "Already published to Amazon"

**Test 2: Partial marketplace failure**
- Amazon succeeds (10/10)
- eBay fails for 3 products (7/10 success)
- Kaufland succeeds (10/10)
**Expected:**
- Clear report showing 27/30 successful
- Failed products listed with errors
- Successful products still live on marketplaces

---

## Scenario 8: Error Handling

### User Story
*As a developer/tester, I need to verify the system handles errors gracefully without crashing or exposing sensitive data.*

### Preconditions
- System running
- Test data prepared

### Error Scenarios to Test

#### 8.1: API Unavailable

**Test:** Backend API is down

```bash
# Stop backend
pkill -f "python main.py"

# Try to load frontend
open http://localhost:3000/

# Try API call
curl http://localhost:8000/api/products
```

**Expected:**
- ✅ Frontend shows error message "Unable to connect to API"
- ✅ Frontend doesn't crash (graceful degradation)
- ✅ Error logged in browser console
- ✅ Retry button available

#### 8.2: Database Connection Lost

**Test:** Database becomes unavailable mid-operation

```bash
# Simulate by setting wrong DATABASE_URL
# Or disconnect Supabase

curl http://localhost:8000/api/products
```

**Expected:**
- ✅ 500 Internal Server Error
- ✅ Generic error message (not exposing DB details)
- ✅ Error logged in backend with details
- ✅ Health check endpoint shows "unhealthy"

#### 8.3: Groq API Failure

**Test:** AI optimization fails due to API error

```bash
# Set invalid Groq API key
export GROQ_API_KEY="invalid"

# Try optimization
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon"
```

**Expected:**
- ✅ 500 or 503 Service Unavailable
- ✅ Error message: "AI service temporarily unavailable"
- ✅ Product status remains "imported" (not corrupted)
- ✅ Can retry optimization later

#### 8.4: Invalid Input Data

**Test:** Malformed JSON

```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{"invalid json'
```

**Expected:**
- ✅ 400 Bad Request
- ✅ Error message: "Invalid JSON"

**Test:** XSS attempt

```bash
curl -X POST http://localhost:8000/api/import/product \
  -d '{
    "source_id": "xss001",
    "title": "<script>alert(1)</script>",
    "price": 9.99,
    "currency": "EUR"
  }'
```

**Expected:**
- ✅ Script tags sanitized/escaped
- ✅ Product saved with safe title
- ✅ No JavaScript executed in frontend

**Test:** SQL injection attempt

```bash
curl http://localhost:8000/api/products/1' OR '1'='1
```

**Expected:**
- ✅ 404 Not Found (invalid ID)
- ✅ No SQL execution (ORM protects)

#### 8.5: Marketplace API Errors

**Test:** Amazon API returns error

Simulate various Amazon errors:
- 401 Unauthorized (invalid credentials)
- 403 Forbidden (insufficient permissions)
- 429 Too Many Requests (rate limit)
- 500 Internal Server Error (Amazon down)

**Expected for each:**
- ✅ Clear error message to user
- ✅ Product status unchanged
- ✅ Can retry publishing later
- ✅ Error logged for debugging

#### 8.6: Concurrent Operations

**Test:** Delete product while optimizing

```bash
# Start optimization (slow)
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon" &

# Immediately delete product
sleep 1
curl -X DELETE http://localhost:8000/api/products/1
```

**Expected:**
- ✅ Either optimization completes first, then deletion succeeds
- ✅ Or deletion succeeds, optimization fails with "Product not found"
- ✅ No server crash
- ✅ Data consistency maintained

#### 8.7: Network Timeout

**Test:** Slow network connection

```bash
# Simulate slow response (100s timeout)
curl --max-time 1 http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon
```

**Expected:**
- ✅ Request times out after 1 second
- ✅ Error message: "Request timeout"
- ✅ Backend continues processing (or cancels)

#### 8.8: Disk Full / Out of Memory

**Test:** System resource exhaustion

(Difficult to simulate safely - use monitoring instead)

**Expected:**
- ✅ 503 Service Unavailable
- ✅ Monitoring alerts triggered
- ✅ System recovers after resources freed

### Error Recovery Tests

**Test 1: Retry failed optimization**
1. Cause optimization to fail (invalid API key)
2. Fix issue (restore correct API key)
3. Retry optimization
4. Verify success

**Test 2: Republish after marketplace error**
1. Cause publish to fail (invalid credentials)
2. Fix credentials
3. Retry publish
4. Verify product published successfully

**Test 3: Resume interrupted batch operation**
1. Start batch optimization (10 products)
2. Kill server after 5 complete
3. Restart server
4. Resume batch operation
5. Verify all 10 optimized (or 5 remaining)

---

## Test Data Cleanup

After completing all scenarios, clean up test data:

```bash
# Delete all test products via API
for id in {1..30}; do
  curl -X DELETE http://localhost:8000/api/products/$id
done

# Or via SQL
psql $DATABASE_URL -c "DELETE FROM products WHERE source_id LIKE 'batch_%' OR source_id LIKE 'manual_%';"

# Verify dashboard shows 0 products
curl http://localhost:8000/api/products/stats/summary
```

---

## Success Criteria Summary

| Scenario | Pass Criteria |
|----------|---------------|
| Scenario 1 | Webhook imports product, visible in UI immediately |
| Scenario 2 | Manual import via UI works, form validates correctly |
| Scenario 3 | Batch import of 10 products completes in <5s |
| Scenario 4 | Single optimization completes in <10s with quality >70% |
| Scenario 5 | Bulk optimization of 10 products completes in <60s |
| Scenario 6 | Publish to Amazon succeeds, product live on marketplace |
| Scenario 7 | Bulk publish to 3 marketplaces succeeds (27/30+ products) |
| Scenario 8 | All error scenarios handled gracefully, no crashes |

**Overall System Health:**
- ✅ No unhandled exceptions
- ✅ All features functional
- ✅ Performance within acceptable limits
- ✅ Data integrity maintained
- ✅ Error messages clear and helpful

---

**Next Steps:**
1. Execute scenarios in order (1-8)
2. Document results in test report
3. File bugs for any failures
4. Retest after fixes
5. Obtain sign-off for production deployment
