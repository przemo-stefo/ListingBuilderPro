# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/__init__.py
# Purpose: Package initialization for listing_builder
# NOT for: Direct execution or business logic

"""
Amazon Listing Builder Package
Complete listing optimization based on Seller Systems intelligence + David's code philosophy.
"""

from .listing_optimizer import optimize_listing, save_listing_to_file

__version__ = "1.0.0"
__all__ = ["optimize_listing", "save_listing_to_file"]
