# Backend Architecture - Marketplace Listing Automation

## System Overview

```
┌─────────────┐
│   n8n       │  Allegro Scraper
│   Scraper   │
└──────┬──────┘
       │ Webhook
       │ POST /api/import/webhook
       ▼
┌─────────────────────────────────────────────────┐
│           FastAPI Backend                        │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Import  │  │    AI    │  │  Export  │     │
│  │  Service │  │ Service  │  │ Service  │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │              │            │
│       ▼             ▼              ▼            │
│  ┌────────────────────────────────────┐        │
│  │      Database (Supabase)           │        │
│  │  - products                        │        │
│  │  - import_jobs                     │        │
│  │  - bulk_jobs                       │        │
│  └────────────────────────────────────┘        │
│                                                  │
│  ┌─────────────┐      ┌──────────────┐        │
│  │   Redis     │◄─────┤   Dramatiq   │        │
│  │   Queue     │      │   Workers    │        │
│  └─────────────┘      └──────────────┘        │
│                                                  │
└──────────┬──────────────────────┬───────────────┘
           │                      │
           │                      │
           ▼                      ▼
    ┌──────────┐          ┌──────────┐
    │  Groq    │          │Marketplace│
    │  AI      │          │  APIs     │
    │ (llama)  │          │ (Amazon)  │
    └──────────┘          │ (eBay)    │
                          │ (Kaufland)│
                          └──────────┘
```

## Data Flow

### 1. Import Flow

```
n8n Scraper
    │
    ├─ Scrapes Allegro
    │
    ├─ Formats data
    │
    └─ POST /api/import/webhook
        │
        ├─ Validates webhook secret
        │
        ├─ Creates ImportJob
        │
        ├─ For each product:
        │   ├─ Validate with Pydantic
        │   ├─ Check for duplicates (source_id)
        │   ├─ Insert or update in DB
        │   └─ Set status = "imported"
        │
        └─ Return job_id + stats
```

### 2. AI Optimization Flow

```
Client
    │
    └─ POST /api/ai/optimize/{id}
        │
        ├─ Get product from DB
        │
        ├─ Set status = "optimizing"
        │
        ├─ Call Groq API
        │   ├─ Generate optimized title
        │   └─ Generate optimized description
        │
        ├─ Calculate quality score
        │
        ├─ Update product in DB
        │   ├─ title_optimized
        │   ├─ description_optimized
        │   ├─ optimization_score
        │   └─ status = "optimized"
        │
        └─ Return updated product
```

### 3. Publishing Flow

```
Client
    │
    └─ POST /api/export/publish/{id}?marketplace=amazon
        │
        ├─ Get product from DB
        │
        ├─ Validate product is optimized
        │
        ├─ Set status = "publishing"
        │
        ├─ Call marketplace API
        │   ├─ Amazon SP-API
        │   ├─ eBay Trading API
        │   └─ Kaufland API
        │
        ├─ Update marketplace_data in DB
        │
        ├─ Set status = "published"
        │
        └─ Return result
```

### 4. Background Job Flow

```
API Endpoint
    │
    └─ Enqueue task to Redis
        │
        ├─ Task: optimize_product_task(product_id)
        │
        └─ Worker picks up task
            │
            ├─ Get product from DB
            │
            ├─ Run optimization
            │
            ├─ Update DB
            │
            └─ Mark task complete
```

## Database Schema

### Products Table

```sql
products
├── id (PK)
├── source_platform (allegro)
├── source_id (unique per platform)
├── source_url
├── title_original
├── title_optimized
├── description_original
├── description_optimized
├── category
├── brand
├── price
├── currency
├── images (JSONB array)
├── attributes (JSONB object)
├── optimized_data (JSONB)
├── optimization_score
├── status (enum)
├── marketplace_data (JSONB)
├── created_at
└── updated_at
```

### Import Jobs Table

```sql
import_jobs
├── id (PK)
├── source
├── status
├── total_products
├── processed_products
├── failed_products
├── raw_data (JSONB)
├── error_log (JSONB)
├── created_at
└── completed_at
```

### Bulk Jobs Table

```sql
bulk_jobs
├── id (PK)
├── job_type (publish, update, sync)
├── target_marketplace
├── status
├── product_ids (JSONB array)
├── total_count
├── success_count
├── failed_count
├── results (JSONB)
├── error_log (JSONB)
├── created_at
└── completed_at
```

### Sync Logs Table

```sql
sync_logs
├── id (PK)
├── product_id (FK)
├── marketplace
├── sync_type
├── old_value (JSONB)
├── new_value (JSONB)
├── status
├── error_message
└── synced_at
```

### Webhooks Table

```sql
webhooks
├── id (PK)
├── source
├── event_type
├── payload (JSONB)
├── headers (JSONB)
├── processed (boolean)
├── error_message
├── received_at
└── processed_at
```

## API Layer

### Route Structure

```
api/
├── import_routes.py
│   ├── POST /api/import/webhook
│   ├── POST /api/import/product
│   ├── POST /api/import/batch
│   └── GET  /api/import/job/{id}
│
├── ai_routes.py
│   ├── POST /api/ai/optimize/{id}
│   ├── POST /api/ai/optimize-title/{id}
│   ├── POST /api/ai/optimize-description/{id}
│   └── POST /api/ai/batch-optimize
│
├── export_routes.py
│   ├── POST /api/export/publish/{id}
│   ├── POST /api/export/bulk-publish
│   └── GET  /api/export/marketplaces
│
└── product_routes.py
    ├── GET    /api/products
    ├── GET    /api/products/{id}
    ├── DELETE /api/products/{id}
    └── GET    /api/products/stats/summary
```

## Service Layer

### Import Service

```python
class ImportService:
    def import_product(data) -> Product:
        # Check duplicates
        # Insert or update
        # Return product

    def import_batch(products) -> ImportJob:
        # Create job
        # Import each product
        # Track stats
        # Return job

    def get_job_status(job_id) -> ImportJob:
        # Return job details
```

### AI Service

```python
class AIService:
    def optimize_product(id, marketplace) -> Product:
        # Get product
        # Call Groq API
        # Update product
        # Return optimized

    def optimize_title(product, marketplace) -> str:
        # Generate prompt
        # Call Groq
        # Return title

    def optimize_description(product, marketplace) -> str:
        # Generate prompt
        # Call Groq
        # Return description

    def _calculate_quality_score(product) -> float:
        # Title quality (30 pts)
        # Description quality (30 pts)
        # Images (20 pts)
        # Attributes (20 pts)
        # Return 0-100
```

### Export Service

```python
class ExportService:
    def publish_product(id, marketplace) -> dict:
        # Get product
        # Validate optimized
        # Call marketplace API
        # Update marketplace_data
        # Return result

    def publish_to_amazon(product) -> dict:
        # SP-API call (TODO)

    def publish_to_ebay(product) -> dict:
        # Trading API call (TODO)

    def publish_to_kaufland(product) -> dict:
        # API call (TODO)

    def bulk_publish(ids, marketplace) -> BulkJob:
        # Create job
        # Publish each
        # Track results
        # Return job
```

## Worker Layer

### Dramatiq Workers

```python
# workers/ai_worker.py

@dramatiq.actor(max_retries=3, time_limit=300000)
def optimize_product_task(product_id, marketplace):
    # Get product from DB
    # Run optimization
    # Update DB
    # Return result

@dramatiq.actor(max_retries=3)
def batch_optimize_task(product_ids, marketplace):
    # For each product_id:
    #   Call optimize_product_task
    # Return results
```

## Model Layer

### Product Model

```python
class Product(Base):
    __tablename__ = "products"

    id: int
    source_platform: str
    source_id: str
    title_original: str
    title_optimized: str
    price: float
    images: List[str]  # JSONB
    attributes: Dict  # JSONB
    status: ProductStatus  # Enum
    marketplace_data: Dict  # JSONB
    created_at: datetime
    updated_at: datetime
```

### Status Enums

```python
class ProductStatus(enum.Enum):
    IMPORTED = "imported"
    OPTIMIZING = "optimizing"
    OPTIMIZED = "optimized"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"

class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

## Schema Layer (Pydantic)

### Request Schemas

```python
class ProductImport(BaseModel):
    source_id: str
    title: str
    price: float
    images: List[str]
    attributes: Dict

class ProductOptimizationRequest(BaseModel):
    product_id: int
    target_marketplace: str

class BulkJobCreate(BaseModel):
    job_type: str
    target_marketplace: str
    product_ids: List[int]
```

### Response Schemas

```python
class ProductResponse(BaseModel):
    id: int
    source_id: str
    title_original: str
    title_optimized: Optional[str]
    status: ProductStatusEnum
    optimization_score: Optional[float]
    marketplace_data: Dict
    created_at: datetime

    class Config:
        from_attributes = True  # ORM mode
```

## Security Architecture

### Authentication Flow

```
Client Request
    │
    ├─ /api/import/webhook
    │   └─ Check X-Webhook-Secret header
    │       ├─ Valid → Process
    │       └─ Invalid → 401 Unauthorized
    │
    └─ Other endpoints
        └─ TODO: Add API key auth
```

### Data Validation

```
Request → Pydantic Schema → Service → Database
                 ▲
                 │
            Validation
            ├─ Type checking
            ├─ Required fields
            ├─ Value ranges
            ├─ Format validation
            └─ Custom validators
```

## Error Handling

### Layers

```
1. Pydantic Validation
   └─ Invalid input → 422 Unprocessable Entity

2. Route Layer (try/except)
   └─ Catch errors → 400/404/500 with message

3. Service Layer (try/except)
   └─ Business logic errors → Raise HTTPException

4. Database Layer
   └─ Connection errors → Logged and raised

5. Worker Layer
   └─ Failed tasks → Retry (max 3) or dead letter queue
```

### Logging

```python
import structlog

logger = structlog.get_logger()

logger.info("product_created", product_id=123, status="imported")
logger.error("optimization_failed", error=str(e), product_id=123)
```

Output:
```json
{
  "event": "product_created",
  "product_id": 123,
  "status": "imported",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

## Configuration

### Environment Variables

```
# Database
DATABASE_URL → SQLAlchemy connection
SUPABASE_URL → Supabase API
SUPABASE_KEY → Auth token

# Queue
REDIS_URL → Redis connection

# AI
GROQ_API_KEY → Groq authentication

# Marketplaces
AMAZON_* → Amazon SP-API credentials
EBAY_* → eBay API credentials
KAUFLAND_* → Kaufland API credentials

# App
APP_ENV → production/development
CORS_ORIGINS → Allowed origins
WEBHOOK_SECRET → Webhook authentication
```

### Settings Class

```python
class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    redis_url: str
    # ...

    class Config:
        env_file = ".env"

settings = Settings()
```

## Deployment Architecture

### Production Setup

```
┌─────────────────────────────────────────┐
│         Load Balancer (Railway)         │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐      ┌─────────┐
│ API     │      │ Worker  │
│ Service │      │ Service │
└────┬────┘      └────┬────┘
     │                │
     ├────────────────┤
     │                │
     ▼                ▼
┌─────────────────────────┐
│   Redis (Railway)       │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ PostgreSQL (Supabase)   │
└─────────────────────────┘
```

## Performance Considerations

### Database Indexes

```sql
-- Fast product lookups
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_source_id ON products(source_id);

-- Fast job queries
CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_bulk_jobs_status ON bulk_jobs(status);

-- Fast sync logs
CREATE INDEX idx_sync_logs_product_id ON sync_logs(product_id);
```

### Caching Strategy (Future)

```
GET /api/products
    │
    ├─ Check Redis cache
    │   ├─ Hit → Return cached
    │   └─ Miss → Query DB → Cache result
    │
    └─ Return response
```

### Rate Limiting (Future)

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/import/webhook")
@limiter.limit("10/minute")
async def webhook(...):
    # Process request
```

## Monitoring & Observability

### Health Checks

```
GET /health
    │
    ├─ Check database connection
    ├─ Check Redis connection
    └─ Return status
```

### Metrics (Future)

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total requests')
request_duration = Histogram('api_request_duration_seconds', 'Request duration')
```

### Logging Levels

```
DEBUG: Development details
INFO: Normal operations
WARNING: Potential issues
ERROR: Failures requiring attention
CRITICAL: System failures
```

## Scalability

### Horizontal Scaling

```
Multiple API instances behind load balancer
Multiple worker instances processing queue
Shared Redis queue
Shared PostgreSQL database
```

### Vertical Scaling

```
Increase API service CPU/RAM
Increase worker service CPU/RAM
Increase database resources
Increase Redis memory
```

## Summary

This architecture provides:
- ✅ Clean separation of concerns
- ✅ Modular design (easy to extend)
- ✅ Type safety (Pydantic + SQLAlchemy)
- ✅ Async processing (Dramatiq workers)
- ✅ Scalability (horizontal + vertical)
- ✅ Maintainability (clear structure)
- ✅ Observability (structured logging)
- ✅ Security (validation, auth, error handling)

Ready for production deployment and future enhancements.
