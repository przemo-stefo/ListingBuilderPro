# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/models/jobs.py
# Purpose: Job tracking models (import, bulk operations, sync logs)
# NOT for: Worker implementation or business logic

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class JobStatus(str, enum.Enum):
    """Generic job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportJob(Base):
    """
    Tracks batch imports from scrapers.
    One job = one webhook call with N products.
    """
    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True, index=True)
    # WHY: user_id scopes jobs to owners — prevents IDOR across tenants
    user_id = Column(String(255), index=True, default="webhook")
    source = Column(String(50), default="allegro")  # Which scraper
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True)

    # Stats
    total_products = Column(Integer, default=0)
    processed_products = Column(Integer, default=0)
    failed_products = Column(Integer, default=0)

    # Data
    raw_data = Column(JSON)  # Original webhook payload
    error_log = Column(JSON, default=list)  # List of errors

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<ImportJob {self.id}: {self.status}>"


class BulkJob(Base):
    """
    Tracks bulk operations (publish, update, sync).
    Example: "Publish 100 products to Amazon"
    """
    __tablename__ = "bulk_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50))  # 'publish', 'update', 'sync'
    target_marketplace = Column(String(50))  # 'amazon', 'ebay', 'kaufland'
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True)

    # Product IDs involved
    product_ids = Column(JSON, default=list)
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # Results
    results = Column(JSON, default=list)  # Detailed results per product
    error_log = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<BulkJob {self.id}: {self.job_type} to {self.target_marketplace}>"


class SyncLog(Base):
    """
    Marketplace sync operation logs.
    Tracks inventory/price updates from marketplace back to our DB.
    """
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    marketplace = Column(String(50))  # 'amazon', 'ebay', 'kaufland'

    sync_type = Column(String(50))  # 'inventory', 'price', 'status'
    old_value = Column(JSON)
    new_value = Column(JSON)

    status = Column(String(20))  # 'success', 'failed'
    error_message = Column(Text)

    synced_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    product = relationship("Product", backref="sync_logs")

    def __repr__(self):
        return f"<SyncLog {self.id}: {self.marketplace} {self.sync_type}>"


class Webhook(Base):
    """
    Webhook configuration and logs.
    For receiving events from marketplaces (order updates, etc).
    """
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), index=True)  # 'amazon', 'ebay', etc
    event_type = Column(String(100))  # 'order.created', 'price.changed', etc

    # Request details
    payload = Column(JSON)
    headers = Column(JSON)

    # Processing
    processed = Column(Integer, default=0)  # Boolean as int
    error_message = Column(Text)

    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Webhook {self.id}: {self.source} {self.event_type}>"
