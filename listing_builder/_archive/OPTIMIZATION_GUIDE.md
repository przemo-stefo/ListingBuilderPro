# Performance Optimization Guide
# Marketplace Listing Automation System

**Version:** 1.0.0
**Last Updated:** 2026-01-23
**Focus:** Backend, Frontend, Database, Infrastructure Optimization

---

## Table of Contents

1. [Performance Targets](#performance-targets)
2. [Backend Optimization](#backend-optimization)
3. [Database Optimization](#database-optimization)
4. [Frontend Optimization](#frontend-optimization)
5. [Redis Caching Strategy](#redis-caching-strategy)
6. [API Response Time Optimization](#api-response-time-optimization)
7. [Background Job Optimization](#background-job-optimization)
8. [Infrastructure Optimization](#infrastructure-optimization)
9. [Cost vs Performance Tradeoffs](#cost-vs-performance-tradeoffs)
10. [Monitoring Performance](#monitoring-performance)

---

## Performance Targets

### Current Baseline (After Initial Deployment)

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| **Backend API Response** | <200ms | <500ms | >1000ms |
| **Frontend Page Load** | <1s | <2s | >3s |
| **Database Queries** | <50ms | <100ms | >500ms |
| **AI Optimization Time** | <5s | <10s | >20s |
| **Batch Optimization (10)** | <30s | <60s | >120s |
| **Health Check** | <50ms | <100ms | >200ms |
| **Product List API** | <300ms | <600ms | >1000ms |

### Performance Goals After Optimization

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| API Response (p95) | 500ms | 200ms | **60% faster** |
| Page Load | 2.5s | 1.0s | **60% faster** |
| Database Queries | 150ms | 40ms | **73% faster** |
| AI Optimization | 8s | 5s | **37% faster** |
| Concurrent Users | 10 | 50 | **5x capacity** |

---

## Backend Optimization

### 1. Database Connection Pooling

**Problem:** Each API request creates new database connection (slow).

**Solution:** Use SQLAlchemy connection pooling.

**File:** `backend/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# BEFORE (Slow)
engine = create_engine(DATABASE_URL)

# AFTER (Optimized)
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,              # Max 10 connections
    max_overflow=20,           # Allow 20 overflow connections
    pool_timeout=30,           # Wait 30s for connection
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Test connection before using
    echo=False                 # Disable SQL logging in production
)
```

**Expected improvement:** 50-100ms faster per query

### 2. Async Route Handlers

**Problem:** Blocking I/O operations (database, Redis, Groq API) slow down requests.

**Solution:** Use async/await for all I/O operations.

**File:** `backend/api/product_routes.py`

```python
# BEFORE (Blocking)
@router.get("/api/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

# AFTER (Async)
@router.get("/api/products")
async def list_products(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Product).limit(100))
    products = result.scalars().all()
    return products
```

**Expected improvement:** 2-3x more concurrent requests

### 3. Prevent N+1 Query Problem

**Problem:** Loading 100 products triggers 100+ database queries.

**Solution:** Use eager loading with `joinedload`.

**File:** `backend/api/product_routes.py`

```python
from sqlalchemy.orm import joinedload

# BEFORE (N+1 Problem - Slow)
def get_products(db: Session):
    products = db.query(Product).all()
    for product in products:
        # Each product.category triggers separate query
        print(product.category.name)  # N+1!
    return products

# AFTER (Eager Loading - Fast)
def get_products(db: Session):
    products = (
        db.query(Product)
        .options(joinedload(Product.category))  # Load in 1 query
        .all()
    )
    return products
```

**Expected improvement:** 200-500ms faster for 100 products

### 4. Response Compression (Gzip)

**Problem:** Large JSON responses slow down API.

**Solution:** Enable gzip compression in FastAPI.

**File:** `backend/main.py`

```python
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

# Add gzip compression
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses >1KB
    compresslevel=5     # Balance between speed and size
)
```

**Expected improvement:** 60-80% smaller responses, faster transfers

### 5. Request Validation Caching

**Problem:** Pydantic validation repeats for similar requests.

**Solution:** Cache validated schemas for common requests.

**File:** `backend/schemas/product.py`

```python
from functools import lru_cache
from pydantic import BaseModel

class ProductImport(BaseModel):
    source_id: str
    title: str
    price: float
    currency: str

    class Config:
        # Cache validation results
        validate_assignment = True
        use_enum_values = True
```

**Expected improvement:** 10-20ms faster per request

### 6. Batch API Endpoints

**Problem:** Frontend makes 100 separate API calls to get product data.

**Solution:** Create batch endpoints that return multiple items.

**File:** `backend/api/product_routes.py`

```python
# BEFORE (100 requests)
# GET /api/products/1
# GET /api/products/2
# ... 100 times

# AFTER (1 request)
@router.post("/api/products/batch")
async def get_products_batch(
    product_ids: List[int],
    db: AsyncSession = Depends(get_async_db)
):
    """Get multiple products in one request"""
    result = await db.execute(
        select(Product).where(Product.id.in_(product_ids))
    )
    return result.scalars().all()
```

**Expected improvement:** 95% reduction in API calls

### 7. Background Task Offloading

**Problem:** Heavy operations (AI optimization) block API responses.

**Solution:** Offload to background workers (Dramatiq).

**File:** `backend/api/ai_routes.py`

```python
import dramatiq

# BEFORE (Blocking - 8 seconds)
@router.post("/api/ai/optimize/{product_id}")
def optimize_product(product_id: int):
    result = groq_optimize(product_id)  # Blocks for 8s
    return result

# AFTER (Non-blocking - 50ms)
@router.post("/api/ai/optimize/{product_id}")
def optimize_product(product_id: int):
    # Queue job (returns immediately)
    optimize_product_task.send(product_id)
    return {"status": "queued", "job_id": task_id}

# Worker processes in background
@dramatiq.actor
def optimize_product_task(product_id: int):
    result = groq_optimize(product_id)
    save_to_db(result)
```

**Expected improvement:** API returns in 50ms vs 8 seconds

---

## Database Optimization

### 1. Create Indexes

**Problem:** Full table scans on every query.

**Solution:** Add indexes on frequently queried columns.

**File:** `backend/migrations/002_add_indexes.sql`

```sql
-- Index on status (most common filter)
CREATE INDEX idx_products_status ON products(status);

-- Index on source_marketplace (filter by source)
CREATE INDEX idx_products_source ON products(source_marketplace);

-- Index on created_at (sorting by date)
CREATE INDEX idx_products_created_at ON products(created_at DESC);

-- Composite index for common query: status + created_at
CREATE INDEX idx_products_status_created
ON products(status, created_at DESC);

-- Partial index for active products only
CREATE INDEX idx_products_active
ON products(id) WHERE status != 'deleted';
```

**Run migration:**
```bash
psql $DATABASE_URL < migrations/002_add_indexes.sql
```

**Expected improvement:** 10-50x faster queries

### 2. Query Optimization

**Problem:** SELECT * returns unnecessary data.

**Solution:** Select only needed columns.

```python
# BEFORE (Returns all columns - slow)
products = db.query(Product).all()

# AFTER (Returns only needed columns - fast)
products = db.query(
    Product.id,
    Product.title_original,
    Product.status,
    Product.price
).all()
```

**Expected improvement:** 30-50% faster queries

### 3. Pagination Optimization

**Problem:** Loading 10,000 products at once crashes app.

**Solution:** Use cursor-based pagination.

**File:** `backend/api/product_routes.py`

```python
# BEFORE (Offset pagination - slow for large offsets)
@router.get("/api/products")
def list_products(page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size
    products = db.query(Product).offset(offset).limit(page_size).all()
    return products

# AFTER (Cursor pagination - fast for any offset)
@router.get("/api/products")
def list_products(cursor: Optional[int] = None, page_size: int = 20):
    query = db.query(Product)

    if cursor:
        # Get products after cursor
        query = query.filter(Product.id > cursor)

    products = query.order_by(Product.id).limit(page_size).all()

    next_cursor = products[-1].id if products else None

    return {
        "items": products,
        "next_cursor": next_cursor,
        "has_more": len(products) == page_size
    }
```

**Expected improvement:** Constant time regardless of offset

### 4. Database Statistics

**Problem:** PostgreSQL query planner makes bad decisions.

**Solution:** Update statistics regularly.

```sql
-- Update statistics for query planner
ANALYZE products;

-- Update specific table
ANALYZE products;

-- Check last analyze time
SELECT schemaname, tablename, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename = 'products';
```

**Schedule:** Run `ANALYZE` weekly or after bulk imports.

### 5. Query Result Caching

**Problem:** Same queries run repeatedly (e.g., dashboard stats).

**Solution:** Cache query results in Redis.

```python
import redis
import json

redis_client = redis.from_url(REDIS_URL)

@router.get("/api/products/stats")
async def get_stats():
    # Try cache first
    cached = redis_client.get("stats:products")
    if cached:
        return json.loads(cached)

    # Query database
    total = db.query(Product).count()
    by_status = db.query(
        Product.status,
        func.count(Product.id)
    ).group_by(Product.status).all()

    stats = {
        "total": total,
        "by_status": dict(by_status)
    }

    # Cache for 5 minutes
    redis_client.setex(
        "stats:products",
        300,  # 5 minutes TTL
        json.dumps(stats)
    )

    return stats
```

**Expected improvement:** 200ms → 5ms for cached queries

---

## Frontend Optimization

### 1. Code Splitting

**Problem:** Large JavaScript bundle (5MB) slow to download.

**Solution:** Split code by routes.

**File:** `frontend/next.config.js`

```javascript
module.exports = {
  // Enable code splitting
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: 10
          },
          common: {
            minChunks: 2,
            priority: 5,
            reuseExistingChunk: true
          }
        }
      }
    }
    return config
  }
}
```

**Expected improvement:** Initial load 3MB → 300KB (10x smaller)

### 2. Image Optimization

**Problem:** Large product images (2MB each) slow page load.

**Solution:** Use Next.js Image component with optimization.

**File:** `frontend/components/ProductCard.tsx`

```typescript
// BEFORE (Slow)
<img src={product.image_url} alt={product.title} />

// AFTER (Optimized)
import Image from 'next/image'

<Image
  src={product.image_url}
  alt={product.title}
  width={300}
  height={300}
  loading="lazy"           // Lazy load off-screen images
  placeholder="blur"       // Show blur while loading
  blurDataURL={product.thumbnail}
  quality={75}             // Balance quality vs size
/>
```

**Expected improvement:** 80-90% smaller images

### 3. Client-Side Caching (TanStack Query)

**Problem:** Same API requests repeat on every page visit.

**Solution:** Use TanStack Query for intelligent caching.

**File:** `frontend/hooks/useProducts.ts`

```typescript
import { useQuery } from '@tanstack/react-query'

// BEFORE (No caching)
const [products, setProducts] = useState([])
useEffect(() => {
  fetch('/api/products').then(r => r.json()).then(setProducts)
}, [])

// AFTER (Smart caching)
const { data: products, isLoading } = useQuery({
  queryKey: ['products', { page, status }],
  queryFn: () => fetch('/api/products').then(r => r.json()),
  staleTime: 5 * 60 * 1000,      // Consider fresh for 5 minutes
  cacheTime: 30 * 60 * 1000,     // Keep in cache for 30 minutes
  refetchOnWindowFocus: false,   // Don't refetch on tab switch
})
```

**Expected improvement:** 500ms → 0ms for cached data

### 4. Lazy Loading Components

**Problem:** All components load on initial page load.

**Solution:** Lazy load heavy components.

**File:** `frontend/app/products/page.tsx`

```typescript
import dynamic from 'next/dynamic'

// BEFORE (Loads immediately)
import ProductTable from '@/components/ProductTable'

// AFTER (Loads only when needed)
const ProductTable = dynamic(
  () => import('@/components/ProductTable'),
  {
    loading: () => <p>Loading products...</p>,
    ssr: false  // Don't render on server
  }
)
```

**Expected improvement:** 1-2s faster initial page load

### 5. API Request Batching

**Problem:** Frontend makes 10 separate API calls for dashboard.

**Solution:** Batch requests into single call.

**File:** `frontend/hooks/useDashboard.ts`

```typescript
// BEFORE (10 separate requests - slow)
const { data: totalProducts } = useQuery(['products', 'count'])
const { data: pendingCount } = useQuery(['products', 'pending'])
const { data: optimizedCount } = useQuery(['products', 'optimized'])
// ... 7 more queries

// AFTER (1 batched request - fast)
const { data: dashboardData } = useQuery({
  queryKey: ['dashboard'],
  queryFn: () => fetch('/api/dashboard/stats').then(r => r.json()),
  staleTime: 60000  // Cache for 1 minute
})

// Backend endpoint returns all stats in one response
```

**Expected improvement:** 10 requests → 1 request (10x faster)

### 6. Prefetching

**Problem:** User waits for data to load when navigating.

**Solution:** Prefetch data on hover.

**File:** `frontend/components/ProductList.tsx`

```typescript
import { useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'

const queryClient = useQueryClient()

function ProductRow({ product }) {
  // Prefetch product details on hover
  const handleMouseEnter = () => {
    queryClient.prefetchQuery({
      queryKey: ['product', product.id],
      queryFn: () => fetch(`/api/products/${product.id}`).then(r => r.json())
    })
  }

  return (
    <Link
      href={`/products/${product.id}`}
      onMouseEnter={handleMouseEnter}  // Prefetch on hover
    >
      {product.title}
    </Link>
  )
}
```

**Expected improvement:** Instant navigation (data already loaded)

### 7. Virtual Scrolling for Large Lists

**Problem:** Rendering 1000 products crashes browser.

**Solution:** Use virtual scrolling (only render visible items).

**File:** `frontend/components/ProductList.tsx`

```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

function ProductList({ products }) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: products.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,  // Estimated row height
    overscan: 5               // Render 5 extra rows for smooth scrolling
  })

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <ProductRow
            key={virtualRow.index}
            product={products[virtualRow.index]}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualRow.start}px)`
            }}
          />
        ))}
      </div>
    </div>
  )
}
```

**Expected improvement:** 60 FPS even with 10,000 items

---

## Redis Caching Strategy

### 1. Cache Frequently Accessed Data

```python
import redis
import json
from functools import wraps

redis_client = redis.from_url(REDIS_URL)

def cache_result(ttl_seconds: int = 300):
    """Decorator to cache function results in Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(result)
            )

            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl_seconds=300)  # Cache for 5 minutes
async def get_product_stats():
    # Expensive query
    return db.query(Product).count()
```

### 2. Cache Invalidation Strategy

```python
# When product is updated, invalidate related caches
@router.put("/api/products/{product_id}")
async def update_product(product_id: int, data: ProductUpdate):
    # Update database
    product = db.query(Product).filter(Product.id == product_id).first()
    product.update(data)
    db.commit()

    # Invalidate caches
    redis_client.delete(f"product:{product_id}")
    redis_client.delete(f"products:list:*")  # Invalidate all list caches
    redis_client.delete("stats:products")

    return product
```

### 3. Cache Warming

```python
# Pre-populate cache on app startup
@app.on_event("startup")
async def warm_cache():
    """Warm cache with frequently accessed data"""
    # Cache product stats
    stats = await get_product_stats()
    redis_client.setex("stats:products", 300, json.dumps(stats))

    # Cache top 100 products
    products = db.query(Product).limit(100).all()
    redis_client.setex("products:top100", 300, json.dumps(products))
```

### 4. Rate Limiting with Redis

```python
from fastapi import HTTPException

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Rate limit decorator using Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get client IP
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}"

            # Increment counter
            current = redis_client.incr(key)

            # Set expiry on first request
            if current == 1:
                redis_client.expire(key, window_seconds)

            # Check limit
            if current > max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s"
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.post("/api/ai/optimize/{product_id}")
@rate_limit(max_requests=10, window_seconds=60)  # Max 10 optimizations per minute
async def optimize_product(product_id: int):
    # ... optimization logic
    pass
```

---

## API Response Time Optimization

### 1. Response Streaming

For large responses, stream data instead of buffering.

```python
from fastapi.responses import StreamingResponse
import json

@router.get("/api/products/export")
async def export_products():
    """Stream products as JSONL (JSON Lines)"""

    async def generate_products():
        # Stream products one by one
        async for product in db.stream(select(Product)):
            yield json.dumps(product.dict()) + "\n"

    return StreamingResponse(
        generate_products(),
        media_type="application/x-ndjson"
    )
```

### 2. Parallel Processing

Process multiple items concurrently.

```python
import asyncio

@router.post("/api/ai/batch-optimize")
async def batch_optimize(product_ids: List[int]):
    """Optimize multiple products in parallel"""

    # BEFORE (Sequential - 50 seconds for 10 products)
    results = []
    for product_id in product_ids:
        result = await optimize_product(product_id)
        results.append(result)

    # AFTER (Parallel - 5 seconds for 10 products)
    tasks = [optimize_product(pid) for pid in product_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results
```

### 3. Response Compression

Already covered in Backend Optimization #4.

### 4. Reduce Response Size

Return only necessary fields.

```python
from pydantic import BaseModel

class ProductListItem(BaseModel):
    """Lightweight product schema for lists"""
    id: int
    title: str
    status: str
    price: float

    class Config:
        orm_mode = True

@router.get("/api/products", response_model=List[ProductListItem])
async def list_products():
    """Return minimal product data"""
    # Only select needed columns
    products = db.query(
        Product.id,
        Product.title_original.label('title'),
        Product.status,
        Product.price_original.label('price')
    ).all()

    return products
```

---

## Background Job Optimization

### 1. Worker Concurrency

Increase concurrent workers for faster processing.

**File:** `backend/workers/ai_worker.py`

```python
# Start multiple worker processes
# Command: dramatiq workers.ai_worker --processes 4 --threads 8
```

**Railway Configuration:**
```bash
# In Railway → Worker service → Settings
# Start Command:
dramatiq workers.ai_worker --processes 4 --threads 8
```

**Expected improvement:** 4x throughput

### 2. Priority Queues

Prioritize important jobs.

```python
import dramatiq

# High priority queue (e.g., user-initiated optimizations)
@dramatiq.actor(queue_name="high_priority", priority=10)
def optimize_single_product(product_id: int):
    # Process immediately
    pass

# Low priority queue (e.g., bulk background optimizations)
@dramatiq.actor(queue_name="low_priority", priority=1)
def optimize_bulk_products(product_ids: List[int]):
    # Process when resources available
    pass
```

### 3. Job Batching

Batch similar jobs together.

```python
@dramatiq.actor
def optimize_products_batch(product_ids: List[int]):
    """Optimize multiple products in one worker"""
    # Process 10 products in single worker call
    # Reduces overhead compared to 10 separate jobs

    for product_id in product_ids:
        optimize_product(product_id)
```

### 4. Retry Strategy

Configure smart retries for failed jobs.

```python
from dramatiq.middleware import Retries

@dramatiq.actor(
    max_retries=3,               # Retry up to 3 times
    min_backoff=15000,           # Wait 15s before first retry
    max_backoff=300000,          # Max wait 5 minutes
    throws=(TimeoutError,)       # Only retry on timeout
)
def optimize_product(product_id: int):
    # May fail due to Groq rate limits
    # Will retry with exponential backoff
    pass
```

---

## Infrastructure Optimization

### 1. CDN Configuration

Use Vercel's global CDN for static assets.

**File:** `frontend/next.config.js`

```javascript
module.exports = {
  images: {
    domains: ['your-cdn-domain.com'],
    loader: 'custom',
    loaderFile: './imageLoader.js',
  },

  // Enable static optimization
  output: 'standalone',

  // Compress assets
  compress: true,

  // PWA for offline support
  pwa: {
    dest: 'public',
    disable: process.env.NODE_ENV === 'development'
  }
}
```

### 2. Database Read Replicas

For high read volumes, use Supabase read replicas.

**Setup:**
1. Upgrade to Supabase Pro plan ($25/month)
2. Enable read replicas in dashboard
3. Use replica for read-only queries:

```python
# Write to primary
primary_db = create_engine(DATABASE_URL)

# Read from replica
replica_db = create_engine(DATABASE_READ_REPLICA_URL)

# Use replica for reads
products = replica_db.query(Product).all()

# Use primary for writes
new_product = Product(...)
primary_db.add(new_product)
primary_db.commit()
```

### 3. Horizontal Scaling (Railway)

Scale backend horizontally for high traffic.

**Railway Dashboard:**
1. Go to Backend service → Settings
2. Change **Instances:** 1 → 3
3. Railway auto-balances load across instances

**Cost:** $20/month per instance (3 instances = $60/month)

### 4. Asset Optimization

Optimize static assets before deployment.

```bash
# Compress images
npm install -g imagemin-cli
imagemin frontend/public/images/* --out-dir=frontend/public/images

# Minify CSS/JS
npm run build  # Next.js auto-minifies

# Tree-shaking (remove unused code)
# Automatic with Next.js production build
```

---

## Cost vs Performance Tradeoffs

### Free Tier (Development)

| Service | Free Tier | Performance | Limitations |
|---------|-----------|-------------|-------------|
| Railway | $5 credit/month | Good | 500 hours/month |
| Vercel | Unlimited | Excellent | 100GB bandwidth |
| Supabase | 500MB DB | Good | 2GB bandwidth |
| Groq | 14,400 req/day | Excellent | Rate limits |

**Total cost:** $0-5/month
**Performance:** Good for development, low traffic (<100 users/day)

### Starter Plan (Small Business)

| Service | Plan | Cost | Performance |
|---------|------|------|-------------|
| Railway | Hobby | $20/month | Good |
| Vercel | Pro | $20/month | Excellent |
| Supabase | Pro | $25/month | Excellent |
| Groq | Free | $0 | Excellent |

**Total cost:** $65/month
**Performance:** Excellent for startups (1,000-10,000 users/day)

### Growth Plan (Scaling Business)

| Service | Plan | Cost | Performance |
|---------|------|------|-------------|
| Railway | Pro (3 instances) | $60/month | Excellent |
| Vercel | Pro | $20/month | Excellent |
| Supabase | Pro + Read Replica | $50/month | Excellent |
| Groq | Pay-as-you-go | ~$20/month | Excellent |
| Redis Cloud | 250MB | $5/month | Good |

**Total cost:** $155/month
**Performance:** Handles 50,000+ users/day

### Optimization Priority

**Focus on (Free improvements):**
1. ✅ Database indexes (0 cost, 10x speed up)
2. ✅ Redis caching (included in Railway)
3. ✅ Code splitting (0 cost, 3x faster load)
4. ✅ Lazy loading (0 cost, 2x faster)
5. ✅ Query optimization (0 cost, 5x faster)

**Upgrade when needed:**
1. 💰 Horizontal scaling (traffic >10k/day)
2. 💰 Read replicas (database slow)
3. 💰 CDN for images (bandwidth limits hit)

---

## Monitoring Performance

### 1. Backend Metrics

Track these metrics in Railway:

- **Response Time (p50, p95, p99)**
- **Request Rate** (requests/second)
- **Error Rate** (4xx, 5xx)
- **Database Connection Pool** (active vs idle)
- **Worker Queue Length** (jobs pending)

### 2. Frontend Metrics

Use Vercel Analytics:

- **Core Web Vitals:**
  - LCP (Largest Contentful Paint) - target <2.5s
  - FID (First Input Delay) - target <100ms
  - CLS (Cumulative Layout Shift) - target <0.1

### 3. Database Metrics

Monitor in Supabase:

- **Query Performance** (slow query log)
- **Connection Count** (max 100 on free tier)
- **Database Size** (500MB free tier limit)
- **Cache Hit Rate** (should be >90%)

### 4. Set Performance Budgets

**Create alerts when metrics exceed targets:**

```python
# backend/monitoring/performance.py
from structlog import get_logger

logger = get_logger()

PERFORMANCE_BUDGETS = {
    "api_response_time_p95": 500,  # ms
    "database_query_time_p95": 100,  # ms
    "frontend_page_load": 2000,  # ms
    "error_rate": 0.01  # 1%
}

def check_performance_budget(metric_name, value):
    budget = PERFORMANCE_BUDGETS.get(metric_name)
    if budget and value > budget:
        logger.warning(
            "Performance budget exceeded",
            metric=metric_name,
            value=value,
            budget=budget
        )
        # Send alert to Slack/email
```

---

## Quick Wins (Implement First)

### Priority 1 (Biggest Impact, Easiest Implementation)

1. ✅ **Add database indexes** (002_add_indexes.sql)
   - 10x faster queries, 5 minutes to implement

2. ✅ **Enable gzip compression** (main.py)
   - 60% smaller responses, 2 minutes to implement

3. ✅ **Configure connection pooling** (database.py)
   - 50ms faster per query, 5 minutes to implement

4. ✅ **Cache dashboard stats** (Redis)
   - 200ms → 5ms, 10 minutes to implement

### Priority 2 (Good Impact, Medium Effort)

5. ✅ **Implement code splitting** (next.config.js)
   - 10x smaller initial bundle, 30 minutes

6. ✅ **Add query result caching** (Redis decorator)
   - 5x faster repeated queries, 30 minutes

7. ✅ **Optimize images** (Next.js Image component)
   - 80% smaller images, 30 minutes

8. ✅ **Prevent N+1 queries** (joinedload)
   - 5-10x faster for lists, 1 hour

### Priority 3 (Advanced Optimizations)

9. ✅ **Virtual scrolling** (react-virtual)
   - Handle 10,000+ items, 2 hours

10. ✅ **Background job optimization** (Dramatiq concurrency)
    - 4x faster batch processing, 1 hour

---

## Testing Performance Improvements

### Before & After Benchmarks

```bash
# 1. Baseline (before optimization)
ab -n 1000 -c 10 https://your-api.railway.app/api/products

# Record:
# - Requests per second
# - Time per request (mean)
# - Time per request (p95)

# 2. Apply optimization

# 3. Benchmark again (after optimization)
ab -n 1000 -c 10 https://your-api.railway.app/api/products

# Compare results
```

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_products(self):
        self.client.get("/api/products?page_size=20")

    @task(2)
    def get_product(self):
        self.client.get("/api/products/1")

    @task(1)
    def get_stats(self):
        self.client.get("/api/products/stats")
EOF

# Run load test
locust -f locustfile.py --host=https://your-api.railway.app

# Open http://localhost:8089 to see real-time results
# Test with 100 concurrent users
```

---

## Next Steps

1. ✅ Implement Priority 1 optimizations (1 hour)
2. ✅ Benchmark before/after (30 minutes)
3. ✅ Deploy to staging and verify (30 minutes)
4. ✅ Monitor for 24 hours (see MONITORING_GUIDE.md)
5. ✅ Implement Priority 2 optimizations (3 hours)
6. ✅ Load test with 100 concurrent users (1 hour)
7. ✅ Plan Priority 3 based on bottlenecks found

**See also:**
- [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) - Track performance metrics
- [SCALING_GUIDE.md](./SCALING_GUIDE.md) - Scale infrastructure as you grow
