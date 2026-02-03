# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/workers/ai_worker.py
# Purpose: Background worker for AI optimization tasks
# NOT for: Synchronous API operations

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from services.ai_service import AIService
from database import SessionLocal
from config import settings
import structlog

logger = structlog.get_logger()

# Setup Redis broker
redis_broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(redis_broker)


@dramatiq.actor(max_retries=3, time_limit=300000)  # 5 min timeout
def optimize_product_task(product_id: int, target_marketplace: str = "amazon"):
    """
    Background task to optimize a product listing.
    This runs in a separate worker process.

    Usage:
        optimize_product_task.send(product_id=123, target_marketplace="amazon")
    """
    logger.info("ai_worker_started", product_id=product_id, marketplace=target_marketplace)

    db = SessionLocal()
    try:
        service = AIService(db)
        product = service.optimize_product(product_id, target_marketplace)
        logger.info("ai_worker_completed", product_id=product_id, score=product.optimization_score)
        return {"status": "success", "product_id": product_id, "score": product.optimization_score}
    except Exception as e:
        logger.error("ai_worker_failed", error=str(e), product_id=product_id)
        raise
    finally:
        db.close()


@dramatiq.actor(max_retries=3)
def batch_optimize_task(product_ids: list, target_marketplace: str = "amazon"):
    """
    Background task to optimize multiple products.
    Can be slow for large batches - consider splitting.
    """
    logger.info("batch_ai_worker_started", count=len(product_ids))

    results = []
    for product_id in product_ids:
        try:
            # Call the single product optimization task
            result = optimize_product_task(product_id, target_marketplace)
            results.append(result)
        except Exception as e:
            results.append({"status": "failed", "product_id": product_id, "error": str(e)})

    success_count = sum(1 for r in results if r.get("status") == "success")
    logger.info("batch_ai_worker_completed", total=len(product_ids), success=success_count)

    return results


if __name__ == "__main__":
    # Run worker with: python -m workers.ai_worker
    # Or use dramatiq CLI: dramatiq workers.ai_worker
    logger.info("ai_worker_ready")
