# Marketplace Listing Automation - Backend

FastAPI backend for automated product listing across multiple marketplaces (Amazon, eBay, Kaufland).

## Features

- **Product Import**: Receive products from n8n Allegro scraper via webhook
- **AI Optimization**: Groq-powered listing optimization (titles, descriptions)
- **Multi-Marketplace Publishing**: Amazon, eBay, Kaufland support
- **Background Jobs**: Redis + Dramatiq for async processing
- **Database**: PostgreSQL via Supabase

## Tech Stack

- **API**: FastAPI 0.109
- **Database**: PostgreSQL (Supabase)
- **Queue**: Redis + Dramatiq
- **AI**: Groq (llama-3.3-70b-versatile)
- **ORM**: SQLAlchemy 2.0

## Quick Start

### 1. Installation

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `SUPABASE_URL` and `SUPABASE_KEY`
- `DATABASE_URL` (PostgreSQL connection string)
- `GROQ_API_KEY` (get from groq.com)
- `REDIS_URL` (default: redis://localhost:6379/0)

### 3. Database Setup

Run the migration SQL file in your Supabase SQL editor:

```bash
cat migrations/001_initial_schema.sql
# Copy and paste into Supabase SQL editor
```

Or use psql:

```bash
psql $DATABASE_URL < migrations/001_initial_schema.sql
```

### 4. Run API Server

```bash
uvicorn main:app --reload --port 8000
```

API will be available at: http://localhost:8000

Interactive docs: http://localhost:8000/docs

### 5. Run Background Workers (Optional)

In a separate terminal:

```bash
# Make sure Redis is running
redis-server

# Run Dramatiq worker
dramatiq workers.ai_worker
```

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── config.py              # Environment variables
├── database.py            # Supabase/PostgreSQL connection
├── models/                # SQLAlchemy models
│   ├── product.py
│   ├── jobs.py
│   └── __init__.py
├── schemas/               # Pydantic validation schemas
│   ├── product.py
│   ├── jobs.py
│   └── __init__.py
├── api/                   # API route handlers
│   ├── import_routes.py
│   ├── ai_routes.py
│   ├── export_routes.py
│   └── product_routes.py
├── services/              # Business logic
│   ├── import_service.py
│   ├── ai_service.py
│   └── export_service.py
├── workers/               # Background job workers
│   └── ai_worker.py
├── migrations/            # Database migrations
│   └── 001_initial_schema.sql
└── requirements.txt
```

## API Endpoints

### Import (n8n Webhook)

- `POST /api/import/webhook` - Receive products from n8n scraper
- `POST /api/import/product` - Import single product manually
- `POST /api/import/batch` - Import multiple products
- `GET /api/import/job/{job_id}` - Get import job status

### AI Optimization (Groq)

- `POST /api/ai/optimize/{product_id}` - Full optimization (title + description)
- `POST /api/ai/optimize-title/{product_id}` - Optimize title only
- `POST /api/ai/optimize-description/{product_id}` - Optimize description only
- `POST /api/ai/batch-optimize` - Optimize multiple products

### Export (Marketplaces)

- `POST /api/export/publish/{product_id}` - Publish single product
- `POST /api/export/bulk-publish` - Publish multiple products
- `GET /api/export/marketplaces` - List available marketplaces

### Products (CRUD)

- `GET /api/products` - List products (paginated)
- `GET /api/products/{product_id}` - Get single product
- `DELETE /api/products/{product_id}` - Delete product
- `GET /api/products/stats/summary` - Get statistics

### System

- `GET /` - API information
- `GET /health` - Health check

## Usage Examples

### 1. Import Product from n8n Webhook

```bash
curl -X POST http://localhost:8000/api/import/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -d '{
    "source": "allegro",
    "event_type": "product.import",
    "data": {
      "products": [
        {
          "source_id": "ALG-12345",
          "source_url": "https://allegro.pl/offer/12345",
          "title": "Premium Wireless Headphones",
          "description": "High quality wireless headphones with noise cancellation",
          "category": "Electronics",
          "brand": "AudioTech",
          "price": 299.99,
          "currency": "PLN",
          "images": ["https://example.com/img1.jpg"],
          "attributes": {"color": "black", "wireless": true}
        }
      ]
    }
  }'
```

### 2. Optimize Product with Groq AI

```bash
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon"
```

### 3. Publish to Amazon

```bash
curl -X POST "http://localhost:8000/api/export/publish/1?marketplace=amazon"
```

### 4. List Products

```bash
curl "http://localhost:8000/api/products?page=1&page_size=20&status=optimized"
```

### 5. Bulk Operations

```bash
# Optimize multiple products
curl -X POST http://localhost:8000/api/ai/batch-optimize \
  -H "Content-Type: application/json" \
  -d '{
    "product_ids": [1, 2, 3, 4, 5],
    "target_marketplace": "amazon"
  }'

# Publish multiple products
curl -X POST http://localhost:8000/api/export/bulk-publish \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "publish",
    "target_marketplace": "amazon",
    "product_ids": [1, 2, 3]
  }'
```

## Database Schema

### Products
- Core product entity with original + optimized content
- Status tracking (imported → optimizing → optimized → publishing → published)
- Marketplace data (ASIN, eBay ID, etc.)

### Import Jobs
- Track batch imports from scrapers
- Success/failure stats
- Error logging

### Bulk Jobs
- Track multi-product operations (publish, update, sync)
- Results per product
- Status monitoring

### Sync Logs
- Marketplace sync history
- Price/inventory updates
- Change tracking

### Webhooks
- Incoming webhook events log
- Processing status

## AI Optimization

Uses **Groq** (NOT OpenAI) for 10x faster optimization:

- **Model**: llama-3.3-70b-versatile
- **Speed**: ~500 tokens/sec (vs OpenAI ~50 tokens/sec)
- **Cost**: Free tier available
- **Quality**: Excellent for e-commerce content

### Optimization Features

1. **Title Optimization**
   - Marketplace-specific character limits
   - Keyword optimization
   - Brand preservation
   - Feature highlighting

2. **Description Optimization**
   - Bullet points format
   - Benefit-focused copy
   - Professional tone
   - Attribute integration

3. **Quality Scoring**
   - Title quality (30 points)
   - Description quality (30 points)
   - Image count (20 points)
   - Attributes completeness (20 points)
   - Total score: 0-100

## Marketplace Publishing

Currently provides **basic structure** for:

- **Amazon**: SP-API integration (TODO: implement)
- **eBay**: Trading API integration (TODO: implement)
- **Kaufland**: Seller API integration (TODO: implement)

Each marketplace handler returns standardized result format:

```json
{
  "status": "success",
  "marketplace": "amazon",
  "listing_id": "B08XXX...",
  "message": "Published successfully"
}
```

## Background Jobs

Uses **Dramatiq** with Redis for async processing:

### Start Worker

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Worker
dramatiq workers.ai_worker
```

### Send Job

```python
from workers.ai_worker import optimize_product_task

# Send to queue
optimize_product_task.send(product_id=123, target_marketplace="amazon")
```

## Testing

### Manual Testing

1. Start API: `uvicorn main:app --reload`
2. Open docs: http://localhost:8000/docs
3. Use interactive API docs to test endpoints

### Test Data

A test product is automatically inserted by the migration:
- Source ID: TEST-001
- Platform: allegro
- Status: imported

Use this for testing optimization and publishing.

## Production Deployment

### Railway / Render

```bash
# Install Railway CLI
npm install -g railway

# Login and deploy
railway login
railway init
railway up
```

### Environment Variables

Set in Railway/Render dashboard:
- All variables from .env.example
- Set `APP_ENV=production`
- Set `APP_DEBUG=False`

### Database

Use Supabase PostgreSQL:
1. Create project at supabase.com
2. Run migration SQL in SQL editor
3. Copy connection string to `DATABASE_URL`

### Redis

Use Railway Redis or external Redis:
- Railway: Add Redis service
- External: Redis Cloud (free tier available)

## Security

- Webhook endpoint requires `X-Webhook-Secret` header
- CORS configured for specific origins
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
- TODO: Add API key authentication for other endpoints

## Logging

Uses **structlog** for structured logging:

```python
logger.info("product_created", product_id=123, status="imported")
logger.error("optimization_failed", error=str(e), product_id=123)
```

Logs include:
- Request IDs
- Timestamps
- Context data
- Error traces

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Returns database connection status.

### Metrics Endpoint (TODO)

Add Prometheus metrics for:
- Request counts
- Response times
- Queue sizes
- Error rates

## Next Steps / TODOs

1. **Marketplace Integration**
   - Implement Amazon SP-API
   - Implement eBay Trading API
   - Implement Kaufland API

2. **Authentication**
   - Add API key auth
   - Supabase Auth integration
   - User management

3. **Advanced Features**
   - Image optimization
   - Keyword research
   - Competitor analysis
   - Price monitoring

4. **Testing**
   - Unit tests (pytest)
   - Integration tests
   - Load testing

5. **Monitoring**
   - Prometheus metrics
   - Sentry error tracking
   - Logging aggregation

## Support

For questions or issues:
- Check API docs: http://localhost:8000/docs
- Review code comments
- Check logs in console

## License

Private project - not for distribution.
