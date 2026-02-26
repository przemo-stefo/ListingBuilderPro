# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/monitor_scheduler.py
# Purpose: Lightweight background scheduler that polls marketplaces and compares snapshots
# NOT for: Alert logic (see alert_service.py), API routes, or scraper implementations

from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
import structlog

from config import settings
from models.monitoring import TrackedProduct, MonitoringSnapshot
from services.alert_service import get_alert_service

logger = structlog.get_logger()

_scheduler: Optional[AsyncIOScheduler] = None


async def poll_marketplace(session_factory, marketplace: str) -> list:
    """Poll all enabled tracked products for a given marketplace.

    Returns list of dicts with product_id, status, and error (if any).
    """
    results = []
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
            return results

        logger.info("poll_start", marketplace=marketplace, count=len(products))

        for product in products:
            try:
                result = await _poll_single_product(db, product)
                results.append(result)
            except Exception as e:
                logger.error(
                    "poll_product_failed",
                    marketplace=marketplace,
                    product_id=product.product_id,
                    error=str(e),
                )
                results.append({"product_id": product.product_id, "status": "error", "error": str(e)})

        logger.info("poll_complete", marketplace=marketplace, count=len(products))
    finally:
        db.close()
    return results


async def _poll_single_product(db: Session, product: TrackedProduct) -> dict:
    """Scrape/fetch one product, save snapshot, compare with previous."""
    new_data = await _fetch_product_data(product.marketplace, product.product_id, product.product_url)

    if not new_data or new_data.get("error"):
        error_msg = new_data.get("error") if new_data else "no data"
        logger.warning(
            "poll_fetch_failed",
            marketplace=product.marketplace,
            product_id=product.product_id,
            error=error_msg,
        )
        return {"product_id": product.product_id, "status": "fetch_failed", "error": error_msg}

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

    return {"product_id": product.product_id, "status": "ok", "title": new_data.get("title", "")[:60]}


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
        # WHY: Keepa for price/BSR/reviews + SP-API for content (title, bullets, images)
        data = {}
        try:
            from services.keepa_service import get_product, KEEPA_API_KEY
            if KEEPA_API_KEY:
                result = await get_product(product_id, "amazon.de")
                if result:
                    data = {
                        "title": result.get("title"),
                        "price": result.get("current_price"),
                        "buybox_price": result.get("buybox_price"),
                        "buy_box_owner": "fba" if result.get("offers_fba", 0) > 0 else "fbm",
                        "stock": None,
                        "listing_active": result.get("is_alive", False),
                        "rating": result.get("rating"),
                        "review_count": result.get("review_count"),
                        "offers_fba": result.get("offers_fba", 0),
                        "offers_fbm": result.get("offers_fbm", 0),
                    }
                elif not data:
                    return {"error": f"Keepa: product {product_id} not found"}
        except Exception as e:
            if not data:
                return {"error": str(e)}

        # WHY: SP-API adds content fields (bullets, description, images, brand)
        # that Keepa doesn't provide — needed for listing change detection
        try:
            from services.sp_api_auth import credentials_configured
            if credentials_configured():
                from services.sp_api_catalog import fetch_catalog_item
                sp_data = await fetch_catalog_item(product_id)
                if not sp_data.get("error"):
                    # Merge SP-API content into Keepa data (SP-API title wins if available)
                    if sp_data.get("title"):
                        data["title"] = sp_data["title"]
                    data["bullets"] = sp_data.get("bullets", [])
                    data["description"] = sp_data.get("description", "")
                    data["images"] = sp_data.get("images", [])
                    data["brand"] = sp_data.get("brand", "")
        except Exception as e:
            logger.warning("sp_api_content_fetch_failed", product_id=product_id, error=str(e)[:100])

        if not data:
            return {"error": "No Keepa API key and no Amazon SP-API credentials"}
        return data

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

    # WHY: Listing content diff — only if SP-API data present (bullets key = SP-API enriched)
    if "bullets" in old_data and "bullets" in new_data:
        try:
            from services.listing_diff_service import compare_listing_snapshots
            diffs = compare_listing_snapshots(old_data, new_data)
            if diffs:
                _save_listing_changes(db, product, diffs)
        except Exception as e:
            logger.error("listing_diff_failed", product_id=product.product_id, error=str(e)[:100])


def _save_listing_changes(db: Session, product: TrackedProduct, diffs: list[dict]) -> None:
    """Persist field-level listing changes to DB."""
    from models.listing_change import ListingChange
    for diff in diffs:
        change = ListingChange(
            tracked_product_id=product.id,
            user_id=product.user_id,
            marketplace=product.marketplace,
            product_id=product.product_id,
            change_type=diff["change_type"],
            field_name=diff.get("field_name"),
            old_value=diff.get("old_value"),
            new_value=diff.get("new_value"),
        )
        db.add(change)
    db.commit()
    logger.info("listing_changes_saved", product_id=product.product_id, count=len(diffs))


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

    # WHY: Only start BaseLinker sync if token configured — empty = disabled
    if settings.baselinker_api_token:
        from services.baselinker_sync import sync_bol_orders
        _scheduler.add_job(
            sync_bol_orders, "interval", minutes=15,
            args=[session_factory],
            id="bol_baselinker_sync", replace_existing=True,
            max_instances=1, misfire_grace_time=300,
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
