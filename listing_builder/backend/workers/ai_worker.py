# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/workers/ai_worker.py
# Purpose: Background task functions for AI optimization (FastAPI BackgroundTasks)
# NOT for: Dramatiq/Redis — we use in-process background tasks to stay on free tier

from services.ai_service import AIService
from models import BulkJob, JobStatus
from database import SessionLocal
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger()


def run_batch_optimize(job_id: int, product_ids: list, target_marketplace: str):
    """
    Background function for batch AI optimization.
    Called by FastAPI BackgroundTasks — runs in same process, no Redis needed.

    WHY not Dramatiq: Saves $7/mo Render Background Worker cost.
    Tradeoff: No retries, no persistence across restarts. Good enough for now.
    """
    db = SessionLocal()
    try:
        # Mark job as running
        job = db.query(BulkJob).filter(BulkJob.id == job_id).first()
        if not job:
            logger.error("batch_job_not_found", job_id=job_id)
            return
        job.status = JobStatus.RUNNING
        db.commit()

        logger.info("batch_optimize_started", job_id=job_id, count=len(product_ids))

        results = []
        service = AIService(db)

        for product_id in product_ids:
            try:
                product = service.optimize_product(product_id, target_marketplace)
                results.append({
                    "product_id": product_id,
                    "status": "success",
                    "score": product.optimization_score,
                })
                job.success_count += 1
            except Exception as e:
                results.append({
                    "product_id": product_id,
                    "status": "failed",
                    "error": str(e),
                })
                job.failed_count += 1
                logger.warning("batch_item_failed", product_id=product_id, error=str(e))

            # Update progress after each product
            job.results = results
            db.commit()

        # Mark completed
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.results = results
        db.commit()

        logger.info(
            "batch_optimize_completed",
            job_id=job_id,
            success=job.success_count,
            failed=job.failed_count,
        )

    except Exception as e:
        logger.error("batch_optimize_crashed", job_id=job_id, error=str(e))
        try:
            job = db.query(BulkJob).filter(BulkJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_log = [{"error": str(e)}]
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
