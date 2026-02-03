# API Examples - Marketplace Listing Automation

Complete examples for testing all API endpoints.

## Setup

```bash
# Set base URL
export API_BASE=http://localhost:8000
export WEBHOOK_SECRET=your-webhook-secret
```

## 1. Health Check

```bash
# Check API status
curl $API_BASE/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "environment": "development"
# }
```

## 2. Import Single Product

```bash
curl -X POST $API_BASE/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_platform": "allegro",
    "source_id": "TEST-002",
    "source_url": "https://allegro.pl/offer/test-002",
    "title": "Premium Wireless Bluetooth Headphones with Noise Cancellation",
    "description": "High-quality wireless headphones featuring active noise cancellation, 30-hour battery life, and premium sound quality. Perfect for travel, work, and entertainment.",
    "category": "Electronics > Audio > Headphones",
    "brand": "AudioPro",
    "price": 349.99,
    "currency": "PLN",
    "images": [
      "https://example.com/headphones-front.jpg",
      "https://example.com/headphones-side.jpg",
      "https://example.com/headphones-case.jpg"
    ],
    "attributes": {
      "color": "Black",
      "wireless": true,
      "battery_life_hours": 30,
      "noise_cancellation": true,
      "bluetooth_version": "5.0",
      "weight_grams": 250
    }
  }'
```

## 3. Import Batch (n8n Webhook)

```bash
curl -X POST $API_BASE/api/import/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $WEBHOOK_SECRET" \
  -d '{
    "source": "allegro",
    "event_type": "product.import",
    "data": {
      "products": [
        {
          "source_id": "ALG-001",
          "title": "Gaming Mouse RGB LED 6400 DPI",
          "description": "Professional gaming mouse with RGB lighting",
          "category": "Electronics",
          "brand": "GamerGear",
          "price": 89.99,
          "currency": "PLN",
          "images": ["https://example.com/mouse1.jpg"],
          "attributes": {"dpi": 6400, "buttons": 6}
        },
        {
          "source_id": "ALG-002",
          "title": "Mechanical Keyboard Cherry MX Blue",
          "description": "Professional mechanical keyboard",
          "category": "Electronics",
          "brand": "KeyMaster",
          "price": 249.99,
          "currency": "PLN",
          "images": ["https://example.com/keyboard1.jpg"],
          "attributes": {"switch_type": "Cherry MX Blue", "rgb": true}
        }
      ]
    }
  }'
```

## 4. List Products

```bash
# All products (page 1, 20 per page)
curl "$API_BASE/api/products?page=1&page_size=20"

# Filter by status
curl "$API_BASE/api/products?status=imported"

# Filter by source
curl "$API_BASE/api/products?source=allegro"

# Combined filters
curl "$API_BASE/api/products?status=optimized&page=1&page_size=10"
```

## 5. Get Single Product

```bash
# Get product by ID
curl $API_BASE/api/products/1

# Expected response includes:
# - id, source info
# - original + optimized content
# - status, marketplace data
# - timestamps
```

## 6. Optimize Product (Full)

```bash
# Optimize for Amazon
curl -X POST "$API_BASE/api/ai/optimize/1?target_marketplace=amazon"

# Optimize for eBay
curl -X POST "$API_BASE/api/ai/optimize/1?target_marketplace=ebay"

# Optimize for Kaufland
curl -X POST "$API_BASE/api/ai/optimize/1?target_marketplace=kaufland"
```

## 7. Optimize Title Only

```bash
curl -X POST "$API_BASE/api/ai/optimize-title/1?target_marketplace=amazon"

# Response:
# {
#   "product_id": 1,
#   "original_title": "Gaming Mouse RGB LED 6400 DPI",
#   "optimized_title": "GamerGear RGB Gaming Mouse - 6400 DPI, 6 Programmable Buttons, LED Backlight",
#   "marketplace": "amazon"
# }
```

## 8. Optimize Description Only

```bash
curl -X POST "$API_BASE/api/ai/optimize-description/1?target_marketplace=amazon"
```

## 9. Batch Optimize

```bash
curl -X POST $API_BASE/api/ai/batch-optimize \
  -H "Content-Type: application/json" \
  -d '{
    "product_ids": [1, 2, 3],
    "target_marketplace": "amazon"
  }'

# Response includes results for each product
```

## 10. Publish to Marketplace

```bash
# Publish to Amazon
curl -X POST "$API_BASE/api/export/publish/1?marketplace=amazon"

# Publish to eBay
curl -X POST "$API_BASE/api/export/publish/1?marketplace=ebay"

# Publish to Kaufland
curl -X POST "$API_BASE/api/export/publish/1?marketplace=kaufland"
```

## 11. Bulk Publish

```bash
curl -X POST $API_BASE/api/export/bulk-publish \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "publish",
    "target_marketplace": "amazon",
    "product_ids": [1, 2, 3, 4, 5]
  }'

# Response includes job_id and results
```

## 12. List Marketplaces

```bash
curl $API_BASE/api/export/marketplaces

# Response:
# {
#   "marketplaces": [
#     {
#       "id": "amazon",
#       "name": "Amazon",
#       "regions": ["eu-west-1", "us-east-1"],
#       "status": "available"
#     },
#     ...
#   ]
# }
```

## 13. Get Statistics

```bash
curl $API_BASE/api/products/stats/summary

# Response:
# {
#   "total_products": 150,
#   "by_status": {
#     "imported": 45,
#     "optimizing": 5,
#     "optimized": 60,
#     "publishing": 10,
#     "published": 30,
#     "failed": 0
#   }
# }
```

## 14. Delete Product

```bash
curl -X DELETE $API_BASE/api/products/1

# Response:
# {
#   "status": "success",
#   "message": "Product deleted"
# }
```

## 15. Get Import Job Status

```bash
curl $API_BASE/api/import/job/1

# Response:
# {
#   "id": 1,
#   "source": "allegro",
#   "status": "completed",
#   "total_products": 10,
#   "processed_products": 10,
#   "failed_products": 0,
#   "created_at": "2024-01-20T10:30:00Z",
#   "completed_at": "2024-01-20T10:35:00Z"
# }
```

## Python Examples

### Using requests library

```python
import requests

BASE_URL = "http://localhost:8000"

# Import product
product_data = {
    "source_id": "PY-001",
    "title": "Python Test Product",
    "price": 99.99,
    "currency": "PLN",
    "images": ["https://example.com/img.jpg"],
    "attributes": {"test": True}
}

response = requests.post(
    f"{BASE_URL}/api/import/product",
    json=product_data
)
print(response.json())

# Optimize product
product_id = 1
response = requests.post(
    f"{BASE_URL}/api/ai/optimize/{product_id}",
    params={"target_marketplace": "amazon"}
)
optimized = response.json()
print(f"Score: {optimized['optimization_score']}")

# Publish to Amazon
response = requests.post(
    f"{BASE_URL}/api/export/publish/{product_id}",
    params={"marketplace": "amazon"}
)
print(response.json())
```

### Using httpx (async)

```python
import httpx
import asyncio

async def optimize_products(product_ids):
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post(
                f"http://localhost:8000/api/ai/optimize/{pid}",
                params={"target_marketplace": "amazon"}
            )
            for pid in product_ids
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

# Run
results = asyncio.run(optimize_products([1, 2, 3, 4, 5]))
print(f"Optimized {len(results)} products")
```

## Complete Workflow Example

```bash
# 1. Import product
PRODUCT_ID=$(curl -s -X POST $API_BASE/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "WORKFLOW-001",
    "title": "Test Product for Complete Workflow",
    "price": 199.99,
    "currency": "PLN",
    "images": ["https://example.com/test.jpg"],
    "attributes": {}
  }' | jq -r '.product_id')

echo "Created product: $PRODUCT_ID"

# 2. Get product details
echo "Product details:"
curl -s $API_BASE/api/products/$PRODUCT_ID | jq .

# 3. Optimize for Amazon
echo "Optimizing..."
curl -s -X POST "$API_BASE/api/ai/optimize/$PRODUCT_ID?target_marketplace=amazon" | jq .

# 4. Publish to Amazon
echo "Publishing..."
curl -s -X POST "$API_BASE/api/export/publish/$PRODUCT_ID?marketplace=amazon" | jq .

# 5. Check final status
echo "Final product state:"
curl -s $API_BASE/api/products/$PRODUCT_ID | jq '.status, .optimization_score, .marketplace_data'
```

## Testing with Interactive API Docs

The easiest way to test is using FastAPI's built-in interactive documentation:

1. Start server: `./start.sh`
2. Open browser: http://localhost:8000/docs
3. Click "Try it out" on any endpoint
4. Fill in parameters
5. Click "Execute"
6. See response

This is much faster than writing curl commands for exploration!

## Error Handling Examples

```bash
# 404 - Product not found
curl -s $API_BASE/api/products/99999

# 401 - Invalid webhook secret
curl -s -X POST $API_BASE/api/import/webhook \
  -H "X-Webhook-Secret: wrong-secret" \
  -d '{"data": {}}'

# 400 - Invalid data
curl -s -X POST $API_BASE/api/import/product \
  -H "Content-Type: application/json" \
  -d '{"source_id": "TEST", "price": -10}'  # Negative price
```

## Notes

- Replace `$API_BASE` with your actual API URL
- Set `$WEBHOOK_SECRET` to match your .env file
- Use `jq` for pretty-printing JSON responses
- Check `/docs` for full API schema
- All timestamps are in UTC
- Pagination starts at page 1 (not 0)
