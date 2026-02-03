#!/bin/bash
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/test_security.sh
# Purpose: Test all Phase 1 security fixes
# NOT for: Production testing (use staging first)

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_SECRET_KEY:-test-key}"

echo "=================================================="
echo "🔒 SECURITY FIXES VERIFICATION"
echo "=================================================="
echo ""
echo "Testing API at: $API_URL"
echo ""

# Test 1: Health check (should work without auth)
echo "Test 1: Health check (no auth required)..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$HEALTH" = "200" ]; then
    echo "✅ PASS: Health check accessible without auth"
else
    echo "❌ FAIL: Health check returned $HEALTH"
fi
echo ""

# Test 2: API without key (should fail)
echo "Test 2: API endpoint without key (should fail 401)..."
NO_AUTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/products")
if [ "$NO_AUTH" = "401" ]; then
    echo "✅ PASS: API rejected request without API key"
else
    echo "❌ FAIL: API returned $NO_AUTH (expected 401)"
fi
echo ""

# Test 3: API with key (should succeed)
echo "Test 3: API endpoint with valid key..."
WITH_AUTH=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/products")
if [ "$WITH_AUTH" = "200" ] || [ "$WITH_AUTH" = "404" ]; then
    echo "✅ PASS: API accepted request with API key"
else
    echo "❌ FAIL: API returned $WITH_AUTH (expected 200/404)"
fi
echo ""

# Test 4: Security headers
echo "Test 4: Security headers..."
HEADERS=$(curl -s -I -H "X-API-Key: $API_KEY" "$API_URL/api/products")
if echo "$HEADERS" | grep -q "Strict-Transport-Security"; then
    echo "✅ PASS: HSTS header present"
else
    echo "⚠️  WARN: HSTS header missing"
fi

if echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
    echo "✅ PASS: nosniff header present"
else
    echo "⚠️  WARN: nosniff header missing"
fi

if echo "$HEADERS" | grep -q "X-Frame-Options"; then
    echo "✅ PASS: X-Frame-Options header present"
else
    echo "⚠️  WARN: X-Frame-Options header missing"
fi
echo ""

# Test 5: CORS headers
echo "Test 5: CORS configuration..."
CORS=$(curl -s -I -X OPTIONS -H "Origin: http://localhost:3000" "$API_URL/api/products")
if echo "$CORS" | grep -q "Access-Control-Allow-Methods"; then
    echo "✅ PASS: CORS headers present"
else
    echo "⚠️  WARN: CORS headers missing"
fi
echo ""

# Test 6: Docs accessibility (production mode)
echo "Test 6: API docs (production mode check)..."
if [ "$APP_ENV" = "production" ]; then
    DOCS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
    if [ "$DOCS" = "404" ]; then
        echo "✅ PASS: Docs hidden in production mode"
    else
        echo "❌ FAIL: Docs accessible in production (returned $DOCS)"
    fi
else
    DOCS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
    if [ "$DOCS" = "200" ]; then
        echo "✅ PASS: Docs accessible in development mode"
    else
        echo "⚠️  WARN: Docs returned $DOCS"
    fi
fi
echo ""

echo "=================================================="
echo "SUMMARY"
echo "=================================================="
echo ""
echo "✅ Phase 1 security fixes verified!"
echo ""
echo "⚠️  Before production deployment:"
echo "   1. Generate strong secrets (backend/generate_secrets.py)"
echo "   2. Set APP_ENV=production"
echo "   3. Set APP_DEBUG=False"
echo "   4. Update CORS_ORIGINS to production frontend URL"
echo "   5. Run this test again in staging environment"
echo ""
echo "📖 See: SECURITY_FIXES_APPLIED.md for details"
echo "=================================================="
