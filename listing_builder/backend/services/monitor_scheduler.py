# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/monitor_scheduler.py
# Purpose: Lightweight background scheduler that polls marketplaces and compares snapshots
# NOT for: Alert logic (see alert_service.py), API routes, or scraper implementations

from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
import structlog

from models.monitoring import TrackedProduct, MonitoringSnapshot
from services.alert_service import get_alert_service

logger = structlog.get_logger()

_scheduler: Optional[AsyncIOScheduler] = None


async def poll_marketplace(session_factory, marketplace: str) -> None:
    """Poll all enabled tracked products for a given marketplace."""
    db: Session = session_factory()
    try:
        products = (
            db.query(TrackedProduct)
            .filter(
                TrackedProduct.marketplace == marketplace,
                TrackedProduct.enabled == True,
            )
            .all()
        )

        if not products:
            return

        logger.info("poll_start", marketplace=marketplace, count=len(products))

        for product in products:
            try:
                await _poll_single_product(db, product)
            except Exception as e:
                logger.error(
                    "poll_product_failed",
                    marketplace=marketplace,
                    product_id=product.product_id,
                    error=str(e),
                )

        logger.info("poll_complete", marketplace=marketplace, count=len(products))
    finally:
        db.close()


async def _poll_single_product(db: Session, product: TrackedProduct) -> None:
    """Scrape/fetch one product, save snapshot, compare with previous."""
    new_data = await _fetch_product_data(product.marketplace, product.product_id, product.product_url)

    if not new_data or new_data.get("error"):
        logger.warning(
            "poll_fetch_failed",
            marketplace=product.marketplace,
            product_id=product.product_id,
            error=new_data.get("error") if new_data else "no data",
        )
        return

    # Save snapshot
    snapshot = MonitoringSnapshot(
        tracked_product_id=product.id,
        marketplace=product.marketplace,
        product_id=product.product_id,
        ean=new_data.get("ean"),
        snapshot_data=new_data,
    )
    db.add(snapshot)
    db.commit()

    # Get previous snapshot for comparison
    previous = (
        db.query(MonitoringSnapshot)
        .filter(
            MonitoringSnapshot.tracked_product_id == product.id,
            MonitoringSnapshot.id != snapshot.id,
        )
        .order_by(MonitoringSnapshot.created_at.desc())
        .first()
    )

    if previous:
        _compare_and_alert(db, product, previous.snapshot_data, new_data)


async def _fetch_product_data(marketplace: str, product_id: str, product_url: Optional[str]) -> Optional[dict]:
    """Fetch current product data from the appropriate marketplace service."""

    if marketplace == "allegro" and product_url:
        try:
            from services.scraper.allegro_scraper import scrape_allegro_product
            result = await scrape_allegro_product(product_url)
            if result.error:
                return {"error": result.error}
            return {
                "title": result.title,
                "price": float(result.price) if result.price else None,
                "currency": result.currency,
                "ean": result.ean,
                "stock": None,  # Allegro doesn't expose stock in public pages
                "listing_active": bool(result.title),
                "images_count": len(result.images),
            }
        except Exception as e:
            return {"error": str(e)}

    if marketplace == "amazon":
        # WHY guard: Amazon SP-API credentials come from Mateusz (blocked)
        try:
            from config import settings
            if not settings.amazon_client_id:
                return {"error": "Amazon credentials not configured"}
            # Future: call amazon_sp_api service here
            return {"error": "Amazon polling not yet implemented"}
        except Exception as e:
            return {"error": str(e)}

    if marketplace == "kaufland":
        try:
            from config import settings
            if not settings.kaufland_client_key:
                return {"error": "Kaufland credentials not configured"}
            return {"error": "Kaufland polling not yet implemented"}
        except Exception as e:
            return {"error": str(e)}

    if marketplace == "ebay":
        try:
            from services.ebay_service import fetch_ebay_product
            return await fetch_ebay_product(product_id)
        except ImportError:
            return {"error": "eBay service not available"}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown marketplace: {marketplace}"}


def _compare_and_alert(
    db: Session,
    product: TrackedProduct,
    old_data: dict,
    new_data: dict,
) -> None:
    """Compare two snapshots and fire alerts on significant changes."""
    try:
        alert_svc = get_alert_service()
    except RuntimeError:
        logger.warning("alert_service_not_initialized")
        return

    # Price change
    old_price = old_data.get("price")
    new_price = new_data.get("price")
    if old_price and new_price and old_price != new_price:
        alert_svc.check_price_change(
            db, product.user_id, product.marketplace,
            product.product_id, float(old_price), float(new_price),
        )

    # Buy Box (Amazon only)
    old_bb = old_data.get("buy_box_owner")
    new_bb = new_data.get("buy_box_owner")
    if old_bb and new_bb and old_bb != new_bb:
        alert_svc.check_buy_box_lost(
            db, product.user_id, product.product_id, old_bb, new_bb,
        )

    # Stock level
    old_stock = old_data.get("stock")
    new_stock = new_data.get("stock")
    if old_stock is not None and new_stock is not None:
        alert_svc.check_stock_level(
            db, product.user_id, product.marketplace,
            product.product_id, int(old_stock), int(new_stock),
        )

    # Listing deactivated
    old_active = old_data.get("listing_active", True)
    new_active = new_data.get("listing_active", True)
    if old_active != new_active:
        alert_svc.check_listing_deactivated(
            db, product.user_id, product.marketplace,
            product.product_id, old_active, new_active,
        )


def start_scheduler(session_factory) -> AsyncIOScheduler:
    """Start the monitoring scheduler. Called from main.py lifespan."""
    global _scheduler
    _scheduler = AsyncIOScheduler()

    # WHY separate jobs per marketplace: different poll intervals + rate limits
    _scheduler.add_job(
        poll_marketplace, "interval", hours=6,
        args=[session_factory, "allegro"],
        id="poll_allegro", replace_existing=True,
    )
    _scheduler.add_job(
        poll_marketplace, "interval", hours=4,
        args=[session_factory, "amazon"],
        id="poll_amazon", replace_existing=True,
    )
    _scheduler.add_job(
        poll_marketplace, "interval", hours=4,
        args=[session_factory, "kaufland"],
        id="poll_kaufland", replace_existing=True,
    )
    _scheduler.add_job(
        poll_marketplace, "interval", hours=6,
        args=[session_factory, "ebay"],
        id="poll_ebay", replace_existing=True,
    )

    _scheduler.start()
    logger.info("monitor_scheduler_started", jobs=len(_scheduler.get_jobs()))
    return _scheduler


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("monitor_scheduler_stopped")
    _scheduler = None
