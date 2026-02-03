# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/schemas/jobs.py
# Purpose: Pydantic schemas for job-related operations
# NOT for: Database models

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class JobStatusEnum(str, Enum):
    """Job status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportJobResponse(BaseModel):
    """Import job status"""
    id: int
    source: str
    status: JobStatusEnum
    total_products: int
    processed_products: int
    failed_products: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class BulkJobCreate(BaseModel):
    """Create bulk operation"""
    job_type: str = Field(..., description="publish, update, or sync")
    target_marketplace: str = Field(..., description="amazon, ebay, or kaufland")
    product_ids: List[int] = Field(..., min_items=1)


class BulkJobResponse(BaseModel):
    """Bulk job status"""
    id: int
    job_type: str
    target_marketplace: str
    status: JobStatusEnum
    total_count: int
    success_count: int
    failed_count: int
    results: List[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    """Generic webhook payload from n8n"""
    data: Dict[str, Any]
    source: str = "allegro"
    event_type: str = "product.import"
