# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/schemas/product.py
# Purpose: Pydantic schemas for product validation and serialization
# NOT for: Database models or business logic

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProductStatusEnum(str, Enum):
    """Product status enum for API"""
    IMPORTED = "imported"
    OPTIMIZING = "optimizing"
    OPTIMIZED = "optimized"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class ProductImport(BaseModel):
    """
    Schema for importing product from scraper.
    This is what n8n webhook sends.
    """
    source_platform: str = Field(default="allegro")
    source_id: str = Field(..., description="Original listing ID")
    source_url: Optional[str] = None

    title: str = Field(..., min_length=1, max_length=1000)
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None

    # WHY: Optional price — batch CSV imports from Allegro may not always include price
    price: Optional[float] = Field(default=None)
    currency: str = Field(default="PLN", max_length=3)

    images: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ProductOptimizationRequest(BaseModel):
    """Request to optimize product listing with AI"""
    product_id: int
    target_marketplace: str = Field(..., description="amazon, ebay, or kaufland")
    optimization_level: str = Field(default="standard", description="basic, standard, or premium")


class ProductResponse(BaseModel):
    """Product data returned by API"""
    id: int
    source_platform: str
    source_id: str
    source_url: Optional[str]

    title_original: str
    title_optimized: Optional[str]
    description_original: Optional[str]
    description_optimized: Optional[str]

    category: Optional[str]
    brand: Optional[str]

    price: Optional[float]
    currency: str

    images: List[str]
    attributes: Dict[str, Any]

    status: ProductStatusEnum
    optimization_score: Optional[float]

    marketplace_data: Dict[str, Any]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # Enable ORM mode


class ProductUpdate(BaseModel):
    """Schema for updating product fields — only provided fields are changed"""
    title_original: Optional[str] = None
    title_optimized: Optional[str] = None
    description_original: Optional[str] = None
    description_optimized: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class ProductList(BaseModel):
    """Paginated list of products"""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
