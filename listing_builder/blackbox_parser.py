# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/blackbox_parser.py
# Purpose: Parse Helium 10 Black Box CSV exports for product research analysis
# NOT for: Other CSV formats - designed specifically for Black Box output

import csv
from typing import List, Dict


def parse_blackbox_csv(csv_path: str) -> List[Dict]:
    """
    Parse Helium 10 Black Box CSV export.
    WHY: Extracts product opportunity data for automated analysis.

    Returns list of products with:
    - ASIN
    - Title
    - Monthly Revenue
    - Review Count
    - Review Rating
    - BSR (Best Seller Rank)
    - Price
    - Category
    """
    products = []

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # WHY: Black Box has multiple possible column names depending on export type
            for row in reader:
                product = {}

                # WHY: Extract ASIN
                product['asin'] = (
                    row.get('ASIN') or
                    row.get('Asin') or
                    row.get('asin') or
                    ''
                )

                # WHY: Extract Title
                product['title'] = (
                    row.get('Title') or
                    row.get('Product Title') or
                    row.get('Product Name') or
                    ''
                )

                # WHY: Extract Monthly Revenue (multiple possible formats)
                revenue_str = (
                    row.get('Monthly Revenue') or
                    row.get('Revenue') or
                    row.get('Est. Monthly Revenue') or
                    row.get('Estimated Revenue') or
                    row.get('ASIN Revenue') or
                    row.get('Parent Level Revenue') or
                    '0'
                )
                # WHY: Remove $, €, commas, spaces
                revenue_str = revenue_str.replace('$', '').replace('€', '').replace(',', '').replace(' ', '').strip()
                try:
                    product['monthly_revenue'] = float(revenue_str)
                except:
                    product['monthly_revenue'] = 0

                # WHY: Extract Review Count
                reviews_str = (
                    row.get('Reviews') or
                    row.get('Review Count') or
                    row.get('Number of Reviews') or
                    row.get('# Reviews') or
                    row.get('Reviews Count') or
                    '0'
                )
                reviews_str = reviews_str.replace(',', '').strip()
                try:
                    product['review_count'] = int(float(reviews_str))
                except:
                    product['review_count'] = 0

                # WHY: Extract Rating (1-5 stars)
                rating_str = (
                    row.get('Rating') or
                    row.get('Review Rating') or
                    row.get('Reviews Rating') or
                    row.get('Star Rating') or
                    row.get('Stars') or
                    '0'
                )
                rating_str = rating_str.replace(' stars', '').replace('stars', '').strip()
                try:
                    product['review_rating'] = float(rating_str)
                except:
                    product['review_rating'] = 0

                # WHY: Extract BSR (Best Seller Rank)
                bsr_str = (
                    row.get('BSR') or
                    row.get('Best Seller Rank') or
                    row.get('Best Sellers Rank') or
                    row.get('Amazon Best Sellers Rank') or
                    row.get('Rank') or
                    '999999'
                )
                # WHY: Remove commas, # symbol, spaces
                bsr_str = bsr_str.replace(',', '').replace('#', '').replace(' ', '').strip()
                # WHY: Sometimes format is "1,234 in Category" - extract just number
                if ' in ' in bsr_str:
                    bsr_str = bsr_str.split(' in ')[0]
                try:
                    product['bsr_rank'] = int(float(bsr_str))
                except:
                    product['bsr_rank'] = 999999

                # WHY: Extract Price
                price_str = (
                    row.get('Price') or
                    row.get('Product Price') or
                    row.get('Current Price') or
                    '0'
                )
                price_str = price_str.replace('$', '').replace('€', '').replace(',', '').strip()
                try:
                    product['price'] = float(price_str)
                except:
                    product['price'] = 0

                # WHY: Extract Category
                product['category'] = (
                    row.get('Category') or
                    row.get('Product Category') or
                    row.get('Main Category') or
                    'Unknown'
                )

                # WHY: Only include products with valid data
                if product['asin'] and product['monthly_revenue'] > 0:
                    products.append(product)

        return products

    except Exception as e:
        print(f"Error parsing Black Box CSV: {e}")
        return []


def estimate_competitors(products: List[Dict]) -> int:
    """
    Estimate number of competitors based on product list.
    WHY: If we have multiple products from Black Box, count = competitors in niche.
    """
    return len(products)


def get_top_product(products: List[Dict]) -> Dict:
    """
    Get top product by monthly revenue.
    WHY: Top seller = benchmark for analysis.
    """
    if not products:
        return {}

    # WHY: Sort by revenue descending
    sorted_products = sorted(products, key=lambda x: x['monthly_revenue'], reverse=True)
    return sorted_products[0]


def analyze_niche_from_csv(csv_path: str) -> Dict:
    """
    Analyze entire niche from Black Box CSV.
    WHY: Provides comprehensive niche analysis with all products.

    Returns:
    - top_product: Best seller data
    - num_competitors: Total products in niche
    - avg_revenue: Average monthly revenue
    - avg_rating: Average review rating
    - all_products: List of all products for detailed view
    """
    products = parse_blackbox_csv(csv_path)

    if not products:
        return {
            'error': 'Nie udało się sparsować CSV. Sprawdź czy plik jest z Helium 10 Black Box.',
            'products': []
        }

    # WHY: Calculate niche-level metrics
    total_revenue = sum(p['monthly_revenue'] for p in products)
    total_rating = sum(p['review_rating'] for p in products if p['review_rating'] > 0)
    products_with_rating = len([p for p in products if p['review_rating'] > 0])

    top_product = get_top_product(products)

    analysis = {
        'top_product': top_product,
        'num_competitors': len(products),
        'avg_revenue': total_revenue / len(products) if products else 0,
        'avg_rating': total_rating / products_with_rating if products_with_rating > 0 else 0,
        'total_niche_revenue': total_revenue,
        'all_products': products,
        'error': None
    }

    return analysis
