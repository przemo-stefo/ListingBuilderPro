# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/ai_service.py
# Purpose: AI optimization service using Groq (NOT OpenAI!)
# NOT for: Marketplace publishing or data import

from groq import Groq
from config import settings
from models import Product, ProductStatus
from sqlalchemy.orm import Session
import structlog
import json

logger = structlog.get_logger()


class AIService:
    """
    AI service for listing optimization using Groq.
    Uses llama-3.3-70b-versatile for speed and quality.
    """

    def __init__(self, db: Session = None):
        self.db = db
        self.client = Groq(api_key=settings.groq_api_key)
        # Use llama-3.3-70b-versatile - best balance of speed and quality
        self.model = "llama-3.3-70b-versatile"

    def optimize_title(self, product: Product, target_marketplace: str = "amazon") -> str:
        """
        Optimize product title for specific marketplace.

        Args:
            product: Product to optimize
            target_marketplace: Target marketplace (amazon, ebay, kaufland)

        Returns:
            Optimized title string
        """
        # Build prompt based on marketplace requirements
        marketplace_rules = {
            "amazon": "Max 200 chars, include brand, key features, no promotional words",
            "ebay": "Max 80 chars, front-load keywords, include condition if relevant",
            "kaufland": "Max 100 chars, clear and descriptive, include brand"
        }

        rules = marketplace_rules.get(target_marketplace, marketplace_rules["amazon"])

        prompt = f"""You are an expert e-commerce listing optimizer.

Original title: {product.title_original}
Category: {product.category or 'Unknown'}
Brand: {product.brand or 'Unknown'}
Target marketplace: {target_marketplace}
Marketplace rules: {rules}

Task: Create an optimized, SEO-friendly title that:
1. Follows marketplace character limits
2. Includes relevant keywords naturally
3. Is clear and customer-focused
4. Maintains brand name if present
5. Highlights key product features

Return ONLY the optimized title, no explanations."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=100,
            )

            optimized_title = response.choices[0].message.content.strip()
            logger.info("title_optimized", product_id=product.id, marketplace=target_marketplace)
            return optimized_title

        except Exception as e:
            logger.error("ai_optimization_failed", error=str(e), product_id=product.id)
            # Fallback to original title
            return product.title_original

    def optimize_description(self, product: Product, target_marketplace: str = "amazon") -> str:
        """
        Optimize product description with bullet points and formatting.

        Returns:
            Optimized description string
        """
        prompt = f"""You are an expert e-commerce copywriter.

Product: {product.title_original}
Original description: {product.description_original or 'No description provided'}
Category: {product.category or 'Unknown'}
Brand: {product.brand or 'Unknown'}
Attributes: {json.dumps(product.attributes, indent=2)}
Target: {target_marketplace}

Task: Create an optimized product description with:
1. Clear, benefit-focused bullet points (5-7 points)
2. Key features highlighted
3. Use cases and benefits
4. Professional tone
5. No exaggerations or false claims

Format as markdown with bullet points.
Return ONLY the description, no preamble."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500,
            )

            optimized_desc = response.choices[0].message.content.strip()
            logger.info("description_optimized", product_id=product.id)
            return optimized_desc

        except Exception as e:
            logger.error("description_optimization_failed", error=str(e))
            return product.description_original or ""

    def optimize_product(self, product_id: int, target_marketplace: str = "amazon") -> Product:
        """
        Full product optimization (title + description).
        Updates product in database with optimized content.

        Args:
            product_id: Product ID to optimize
            target_marketplace: Target marketplace

        Returns:
            Updated product with optimized content
        """
        if not self.db:
            raise ValueError("Database session required for optimize_product")

        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Update status to optimizing
        product.status = ProductStatus.OPTIMIZING
        self.db.commit()

        try:
            # Optimize title
            optimized_title = self.optimize_title(product, target_marketplace)
            product.title_optimized = optimized_title

            # Optimize description
            optimized_desc = self.optimize_description(product, target_marketplace)
            product.description_optimized = optimized_desc

            # Calculate quality score (simple heuristic)
            score = self._calculate_quality_score(product)
            product.optimization_score = score

            # Store optimization results
            product.optimized_data = {
                "marketplace": target_marketplace,
                "title": optimized_title,
                "description": optimized_desc,
                "score": score,
            }

            # Update status
            product.status = ProductStatus.OPTIMIZED
            self.db.commit()
            self.db.refresh(product)

            logger.info("product_fully_optimized", product_id=product_id, score=score)
            return product

        except Exception as e:
            product.status = ProductStatus.FAILED
            self.db.commit()
            logger.error("product_optimization_failed", error=str(e), product_id=product_id)
            raise

    def _calculate_quality_score(self, product: Product) -> float:
        """
        Simple quality score calculation.
        Checks: title length, description length, image count, attributes.

        Returns:
            Score from 0 to 100
        """
        score = 0.0

        # Title quality (30 points)
        if product.title_optimized:
            title_len = len(product.title_optimized)
            if 50 <= title_len <= 200:
                score += 30
            elif 30 <= title_len < 50 or 200 < title_len <= 250:
                score += 20
            else:
                score += 10

        # Description quality (30 points)
        if product.description_optimized:
            desc_len = len(product.description_optimized)
            if desc_len >= 200:
                score += 30
            elif desc_len >= 100:
                score += 20
            else:
                score += 10

        # Images (20 points)
        image_count = len(product.images) if product.images else 0
        if image_count >= 5:
            score += 20
        elif image_count >= 3:
            score += 15
        elif image_count >= 1:
            score += 10

        # Attributes (20 points)
        attr_count = len(product.attributes) if product.attributes else 0
        if attr_count >= 5:
            score += 20
        elif attr_count >= 3:
            score += 15
        elif attr_count >= 1:
            score += 10

        return round(score, 2)
