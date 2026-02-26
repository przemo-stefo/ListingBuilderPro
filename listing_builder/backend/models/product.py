# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/models/product.py
# Purpose: Product database model (core entity)
# NOT for: Business logic or validation schemas

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Text, Enum, UniqueConstraint
from sqlalchemy.sql import func
from database import Base
import enum


class ProductStatus(str, enum.Enum):
    """Product processing status"""
    IMPORTED = "imported"  # Just received from scraper
    OPTIMIZING = "optimizing"  # AI optimization in progress
    OPTIMIZED = "optimized"  # Ready to publish
    PUBLISHING = "publishing"  # Being published to marketplaces
    PUBLISHED = "published"  # Live on marketplaces
    FAILED = "failed"  # Something went wrong


class Product(Base):
    """
    Core product entity.
    Stores scraped product data + optimized listings + marketplace info.
    """
    __tablename__ = "products"
    # WHY: Same source_id can exist for different users and platforms
    __table_args__ = (
        UniqueConstraint('user_id', 'source_platform', 'source_id', name='uq_user_platform_source'),
    )

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # WHY: Multi-tenant isolation — each user sees only their own products
    user_id = Column(String(255), nullable=False, default="default", index=True)

    # Source Data (from Allegro scraper)
    source_platform = Column(String(50), default="allegro")
    source_id = Column(String(255), index=True)  # Original listing ID
    source_url = Column(Text)

    # Product Details
    title_original = Column(Text, nullable=False)
    title_optimized = Column(Text)  # AI-optimized version
    description_original = Column(Text)
    description_optimized = Column(Text)
    category = Column(String(255))
    brand = Column(String(255))

    # Pricing
    price = Column(Float)
    currency = Column(String(3), default="PLN")

    # Images (JSON array of URLs)
    images = Column(JSON, default=list)

    # Product Attributes (JSON object)
    # Example: {"size": "XL", "color": "black", "material": "cotton"}
    attributes = Column(JSON, default=dict)

    # AI Optimization Results
    optimized_data = Column(JSON)  # Stores all AI-generated variations
    optimization_score = Column(Float)  # Quality score from AI

    # Status & Workflow
    status = Column(Enum(ProductStatus), default=ProductStatus.IMPORTED, index=True)

    # Marketplace Publishing Info (JSON)
    # Example: {"amazon": {"asin": "B08XXX", "status": "live"}, "ebay": {...}}
    marketplace_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Product {self.id}: {self.title_original[:50]}>"
