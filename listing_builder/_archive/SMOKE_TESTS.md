# Smoke Tests - Quick Deployment Verification

**Version:** 1.0.0
**Purpose:** Fast verification tests to run after code changes or deployments
**Duration:** 10 minutes total

---

## Overview

Smoke tests are quick sanity checks to verify critical functionality works after:
- Code deployments
- Configuration changes
- Server restarts
- Database migrations
- Dependency updates

**Pass Criteria:** ALL smoke tests must pass before proceeding to full testing.

---

## Backend Smoke Tests (5 minutes)

### 1. Service Startup

**Test:** Backend starts without errors

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

**Pass:** ✅ No errors in output
**Fail:** ❌ Exceptions, connection errors, or missing dependencies

---

### 2. Health Check

**Test:** Health endpoint returns healthy status

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

**Pass:** ✅ Status 200, database connected
**Fail:** ❌ Status 500, database disconnected, or timeout

---

### 3. Root Endpoint

**Test:** API root returns metadata

```bash
curl http://localhost:8000/
```

**Expected response:**
```json
{
  "name": "Marketplace Listing Automation API",
  "version": "1.0.0",
  "status": "running",
  "environment": "development",
  "endpoints": {
    "import": "/api/import",
    "ai": "/api/ai",
    "export": "/api/export",
    "products": "/api/products",
    "docs": "/docs"
  }
}
```

**Pass:** ✅ Status 200, version correct
**Fail:** ❌ Wrong version, missing endpoints

---

### 4. Database Connection

**Test:** Can query database

```bash
curl http://localhost:8000/api/products
```

**Expected response:**
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

**Pass:** ✅ Status 200, items array present (even if empty)
**Fail:** ❌ Database connection error, timeout

---

### 5. Import Product

**Test:** Can import a single product

```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "smoke_test_001",
    "title": "Smoke Test Product",
    "description": "Testing import functionality",
    "price": 9.99,
    "currency": "EUR",
    "images": ["https://example.com/test.jpg"],
    "category": "Test"
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "product_id": 1
}
```

**Pass:** ✅ Status 200, product_id returned
**Fail:** ❌ Validation error, database error, or timeout

---

### 6. AI Service (Optimization)

**Test:** AI optimization works

```bash
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon"
```

**Expected response:**
```json
{
  "id": 1,
  "title_optimized": "...",
  "description_optimized": "...",
  "optimization_score": 85,
  "status": "optimized"
}
```

**Pass:** ✅ Status 200, optimized fields populated, score > 0
**Fail:** ❌ Groq API error, timeout, or invalid response

---

### 7. List Products

**Test:** Can retrieve products

```bash
curl http://localhost:8000/api/products
```

**Expected response:**
```json
{
  "items": [
    {
      "id": 1,
      "source_id": "smoke_test_001",
      "title_original": "Smoke Test Product",
      "status": "optimized"
    }
  ],
  "total": 1,
  "page": 1
}
```

**Pass:** ✅ Status 200, smoke test product visible
**Fail:** ❌ Empty list, wrong data, or error

---

### 8. Cleanup

**Test:** Can delete test product

```bash
curl -X DELETE http://localhost:8000/api/products/1
```

**Expected response:**
```json
{
  "status": "success",
  "message": "Product deleted"
}
```

**Pass:** ✅ Status 200, product deleted
**Fail:** ❌ Product not found or delete failed

---

## Frontend Smoke Tests (5 minutes)

### 1. Service Startup

**Test:** Frontend starts without errors

```bash
cd frontend
npm run dev
```

**Expected output:**
```
- ready started server on 0.0.0.0:3000
- event compiled client and server successfully
- wait compiling...
- event compiled client and server successfully
```

**Pass:** ✅ No errors, server running on port 3000
**Fail:** ❌ Build errors, missing dependencies, or port conflict

---

### 2. Homepage Loads

**Test:** Can access dashboard

```bash
# Via browser
open http://localhost:3000/

# Via curl (check HTML returned)
curl http://localhost:3000/ | grep -q "Dashboard"
```

**Expected:** Dashboard page loads with title "Dashboard"

**Pass:** ✅ Page loads, no console errors
**Fail:** ❌ 404, blank page, or JavaScript errors

---

### 3. API Connectivity

**Test:** Frontend can connect to backend

**Steps:**
1. Open http://localhost:3000/
2. Open browser DevTools (F12)
3. Go to Network tab
4. Check XHR requests

**Expected:**
- Request to `http://localhost:8000/api/products/stats/summary`
- Status: 200 OK
- Response: JSON with stats

**Pass:** ✅ API calls succeed, data displays
**Fail:** ❌ CORS error, connection refused, or timeout

---

### 4. Navigation

**Test:** Can navigate between pages

**Steps:**
1. Start at http://localhost:3000/
2. Click "Products" in navigation
3. Verify URL changes to /products
4. Click "Import" in navigation
5. Verify URL changes to /products/import

**Expected:** All links work, pages load

**Pass:** ✅ Navigation functional
**Fail:** ❌ 404 errors or broken links

---

### 5. Products Page

**Test:** Products list displays

**Steps:**
1. Navigate to http://localhost:3000/products
2. Verify table displays (even if empty)
3. Check "No products found" message if empty

**Expected:** Page renders without errors

**Pass:** ✅ Table component renders
**Fail:** ❌ Blank page or JavaScript error

---

### 6. Import Form

**Test:** Import form renders

**Steps:**
1. Navigate to http://localhost:3000/products/import
2. Verify form displays with all fields
3. Check required field indicators (*)

**Expected:** Form fully functional

**Pass:** ✅ All fields present, submit button works
**Fail:** ❌ Missing fields or broken form

---

### 7. Dashboard Stats

**Test:** Dashboard shows stats

**Steps:**
1. Navigate to http://localhost:3000/
2. Verify stat cards display
3. Check "Total Products", "Optimized", etc.

**Expected:** Stats load from API

**Pass:** ✅ Numbers display (even if 0)
**Fail:** ❌ Loading spinner stuck or error message

---

### 8. No Console Errors

**Test:** No JavaScript errors

**Steps:**
1. Open DevTools Console (F12)
2. Navigate through all pages
3. Check for red error messages

**Expected:** No uncaught exceptions

**Pass:** ✅ Console clean (warnings OK)
**Fail:** ❌ Errors present

---

## Critical Path Test (Full Workflow)

**Test the complete user journey in 2 minutes:**

### Step 1: Import Product

```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "critical_path_001",
    "title": "Critical Path Test Product",
    "price": 49.99,
    "currency": "EUR"
  }'
```

**Expected:** Product ID returned

---

### Step 2: Verify in Frontend

1. Open http://localhost:3000/products
2. Find "Critical Path Test Product" in list
3. Status should be "imported"

**Expected:** Product visible immediately

---

### Step 3: Optimize Product

```bash
curl -X POST "http://localhost:8000/api/ai/optimize/2?target_marketplace=amazon"
```

**Expected:** Optimization completes in <10s

---

### Step 4: Verify Optimization

1. Refresh http://localhost:3000/products
2. Status should be "optimized"
3. Click "View Details"
4. See optimized title and description

**Expected:** Optimized data visible

---

### Step 5: Cleanup

```bash
curl -X DELETE http://localhost:8000/api/products/2
```

**Expected:** Product deleted

---

### Critical Path Pass Criteria

- ✅ Import → Optimize → View → Delete completes without errors
- ✅ Total time: <2 minutes
- ✅ Data persists between steps
- ✅ Frontend updates reflect backend changes

---

## Deployment-Specific Smoke Tests

### Production Deployment

**Additional checks for production environment:**

**1. HTTPS Enabled**
```bash
curl -I https://your-api.railway.app/health
# Should return 200 OK with SSL certificate
```

**2. Debug Mode Disabled**
```bash
curl https://your-api.railway.app/ | grep -q "debug"
# Should NOT contain debug info
```

**3. API Docs Hidden (optional)**
```bash
curl https://your-api.railway.app/docs
# Should return 404 or require auth
```

**4. CORS Configured**
```bash
curl -H "Origin: https://evil.com" https://your-api.railway.app/health
# Should not include Access-Control-Allow-Origin for unauthorized domains
```

**5. Environment Variables Set**
```bash
# Check Railway dashboard
# Verify all required env vars present:
# - APP_ENV=production
# - GROQ_API_KEY
# - DATABASE_URL
# - etc.
```

---

## Automated Smoke Test Script

Save this as `/backend/smoke_test.sh`:

```bash
#!/bin/bash

# smoke_test.sh - Quick smoke tests for backend
# Usage: ./smoke_test.sh [api_url]

API_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "🔥 Running smoke tests against $API_URL"
echo ""

# Test 1: Health check
echo "Test 1: Health check..."
RESPONSE=$(curl -s -w "%{http_code}" "$API_URL/health")
HTTP_CODE="${RESPONSE: -3}"
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ PASS"
  ((PASSED++))
else
  echo "❌ FAIL (HTTP $HTTP_CODE)"
  ((FAILED++))
fi
echo ""

# Test 2: Root endpoint
echo "Test 2: Root endpoint..."
RESPONSE=$(curl -s -w "%{http_code}" "$API_URL/")
HTTP_CODE="${RESPONSE: -3}"
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ PASS"
  ((PASSED++))
else
  echo "❌ FAIL (HTTP $HTTP_CODE)"
  ((FAILED++))
fi
echo ""

# Test 3: List products
echo "Test 3: List products..."
RESPONSE=$(curl -s -w "%{http_code}" "$API_URL/api/products")
HTTP_CODE="${RESPONSE: -3}"
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ PASS"
  ((PASSED++))
else
  echo "❌ FAIL (HTTP $HTTP_CODE)"
  ((FAILED++))
fi
echo ""

# Test 4: Import product
echo "Test 4: Import product..."
RESPONSE=$(curl -s -w "%{http_code}" -X POST "$API_URL/api/import/product" \
  -H "Content-Type: application/json" \
  -d '{"source_id":"smoke_001","title":"Test","price":9.99,"currency":"EUR"}')
HTTP_CODE="${RESPONSE: -3}"
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ PASS"
  ((PASSED++))
  PRODUCT_ID=$(echo "$RESPONSE" | grep -o '"product_id":[0-9]*' | grep -o '[0-9]*')
  echo "   Product ID: $PRODUCT_ID"
else
  echo "❌ FAIL (HTTP $HTTP_CODE)"
  ((FAILED++))
fi
echo ""

# Test 5: Delete product (cleanup)
if [ ! -z "$PRODUCT_ID" ]; then
  echo "Test 5: Delete product (cleanup)..."
  RESPONSE=$(curl -s -w "%{http_code}" -X DELETE "$API_URL/api/products/$PRODUCT_ID")
  HTTP_CODE="${RESPONSE: -3}"
  if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS"
    ((PASSED++))
  else
    echo "❌ FAIL (HTTP $HTTP_CODE)"
    ((FAILED++))
  fi
  echo ""
fi

# Summary
echo "========================================="
echo "Results: $PASSED passed, $FAILED failed"
echo "========================================="

if [ $FAILED -eq 0 ]; then
  echo "🎉 All smoke tests passed!"
  exit 0
else
  echo "💥 Some smoke tests failed!"
  exit 1
fi
```

**Make executable:**
```bash
chmod +x backend/smoke_test.sh
```

**Run:**
```bash
# Local
./backend/smoke_test.sh

# Production
./backend/smoke_test.sh https://your-api.railway.app
```

---

## Quick Checklist

Print this and check off after deployment:

```
BACKEND SMOKE TESTS
[ ] Service starts without errors
[ ] Health check returns healthy
[ ] Root endpoint returns metadata
[ ] Database connection works
[ ] Can import product
[ ] AI optimization works
[ ] Can list products
[ ] Can delete product

FRONTEND SMOKE TESTS
[ ] Service starts without errors
[ ] Homepage loads
[ ] API connectivity works
[ ] Navigation functional
[ ] Products page renders
[ ] Import form renders
[ ] Dashboard stats display
[ ] No console errors

CRITICAL PATH
[ ] Import → Optimize → View → Delete works end-to-end

PRODUCTION ONLY
[ ] HTTPS enabled
[ ] Debug mode disabled
[ ] CORS configured correctly
[ ] Environment variables set
[ ] API docs hidden (or protected)

SIGN-OFF
Tested by: _______________
Date: _______________
Environment: Production / Staging / Development
Result: PASS / FAIL
```

---

## Troubleshooting Failed Smoke Tests

### Backend won't start
- **Check:** Virtual environment activated
- **Check:** Dependencies installed (`pip list`)
- **Check:** .env file exists with required variables
- **Check:** Port 8000 not already in use (`lsof -i :8000`)

### Health check fails
- **Check:** Database URL correct
- **Check:** Supabase accessible (not IP blocked)
- **Check:** Database credentials valid

### AI optimization fails
- **Check:** Groq API key valid
- **Check:** Groq API credits available
- **Check:** Internet connection

### Frontend won't start
- **Check:** Node.js version (18+)
- **Check:** Dependencies installed (`npm list`)
- **Check:** Port 3000 available
- **Check:** .env.local exists with API URL

### Frontend can't connect to backend
- **Check:** Backend running on port 8000
- **Check:** CORS origins include `http://localhost:3000`
- **Check:** No firewall blocking

---

## Monitoring After Deployment

**Set up monitoring to automatically run smoke tests:**

**Option 1: Cron job (every 5 minutes)**
```bash
*/5 * * * * /path/to/backend/smoke_test.sh https://your-api.railway.app >> /var/log/smoke_tests.log 2>&1
```

**Option 2: Railway health checks**
- Railway automatically monitors `/health` endpoint
- Configure alerts in Railway dashboard

**Option 3: Uptime monitoring service**
- Use UptimeRobot, Pingdom, or StatusCake
- Monitor `/health` endpoint
- Alert if status ≠ 200 or response time > 5s

---

## Conclusion

**Smoke tests are your first line of defense against broken deployments.**

✅ **Run before:**
- Production deployments
- Staging deployments
- Database migrations
- Configuration changes

✅ **Run after:**
- Code updates
- Server restarts
- Dependency updates
- Infrastructure changes

⏱️ **Duration:** 10 minutes
🎯 **Pass rate required:** 100%
🚨 **If any test fails:** DO NOT proceed to full testing

**Next steps after smoke tests pass:**
1. Run full QA testing (QA_TESTING_GUIDE.md)
2. Execute test scenarios (TEST_SCENARIOS.md)
3. Perform security review (SECURITY_REVIEW.md)
4. Obtain sign-off for production
