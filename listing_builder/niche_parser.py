# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/niche_parser.py
# Purpose: Parse niche analysis CSV exports (isolbau.csv format) for product research
# NOT for: Black Box CSV - use blackbox_parser.py instead

import csv
from typing import List, Dict


def parse_niche_csv(csv_path: str) -> List[Dict]:
    """
    Parse niche analysis CSV (isolbau.csv format).
    WHY: Alternative data source to Black Box with different metrics.

    Returns list of products with:
    - ASIN
    - Title (Product Details)
    - Brand
    - Monthly Revenue (Rev, €)
    - Sales (monthly units)
    - Review Count (Reviews)
    - Review Rating (Rating)
    - BSR (Root BSR)
    - Price (Price, €)
    """
    products = []

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                product = {}

                # WHY: Extract ASIN
                product['asin'] = (
                    row.get('ASINs') or
                    row.get('ASIN') or
                    row.get('asin') or
                    ''
                )

                # WHY: Extract Title
                product['title'] = (
                    row.get('Product Details') or
                    row.get('Title') or
                    row.get('Product Name') or
                    ''
                )

                # WHY: Extract Brand
                product['brand'] = (
                    row.get('Brand') or
                    row.get('brand') or
                    ''
                )

                # WHY: Extract Monthly Revenue
                revenue_str = (
                    row.get('Rev, €') or
                    row.get('Rev') or
                    row.get('Revenue') or
                    '0'
                )
                revenue_str = revenue_str.replace('€', '').replace(',', '').replace(' ', '').strip()
                try:
                    product['monthly_revenue'] = float(revenue_str)
                except:
                    product['monthly_revenue'] = 0

                # WHY: Extract Sales (monthly units)
                sales_str = (
                    row.get('Sales') or
                    row.get('sales') or
                    row.get('Units Sold') or
                    '0'
                )
                sales_str = sales_str.replace(',', '').strip()
                try:
                    product['monthly_sales'] = int(float(sales_str))
                except:
                    product['monthly_sales'] = 0

                # WHY: Extract Review Count
                reviews_str = (
                    row.get('Reviews') or
                    row.get('Review Count') or
                    row.get('reviews') or
                    '0'
                )
                reviews_str = reviews_str.replace(',', '').strip()
                try:
                    product['review_count'] = int(float(reviews_str))
                except:
                    product['review_count'] = 0

                # WHY: Extract Rating
                rating_str = (
                    row.get('Rating') or
                    row.get('rating') or
                    row.get('Review Rating') or
                    '0'
                )
                rating_str = rating_str.replace(' stars', '').strip()
                try:
                    product['review_rating'] = float(rating_str)
                except:
                    product['review_rating'] = 0

                # WHY: Extract BSR
                bsr_str = (
                    row.get('Root BSR') or
                    row.get('BSR') or
                    row.get('Best Seller Rank') or
                    '999999'
                )
                bsr_str = bsr_str.replace(',', '').replace('#', '').replace(' ', '').strip()
                if ' in ' in bsr_str:
                    bsr_str = bsr_str.split(' in ')[0]
                try:
                    product['bsr_rank'] = int(float(bsr_str))
                except:
                    product['bsr_rank'] = 999999

                # WHY: Extract Price
                price_str = (
                    row.get('Price, €') or
                    row.get('Price') or
                    row.get('price') or
                    '0'
                )
                price_str = price_str.replace('€', '').replace(',', '').strip()
                try:
                    product['price'] = float(price_str)
                except:
                    product['price'] = 0

                # WHY: Extract Category
                product['category'] = (
                    row.get('Category') or
                    row.get('category') or
                    'Unknown'
                )

                # WHY: Only include products with valid data
                if product['asin'] and product['monthly_revenue'] > 0:
                    products.append(product)

        return products

    except Exception as e:
        print(f"Error parsing niche CSV: {e}")
        return []


def compare_datasets(niche_products: List[Dict], blackbox_products: List[Dict]) -> Dict:
    """
    Compare niche analysis CSV with Black Box CSV data.
    WHY: Shows overlap, differences, and combined insights.

    Returns:
    - niche_only: Products only in niche CSV
    - blackbox_only: Products only in Black Box
    - overlap: Products in both (with comparison)
    - combined_total_revenue: Total revenue from all unique products
    """
    # WHY: Create ASIN sets for comparison
    niche_asins = {p['asin'] for p in niche_products}
    blackbox_asins = {p['asin'] for p in blackbox_products}

    # WHY: Find overlaps and differences
    overlap_asins = niche_asins & blackbox_asins
    niche_only_asins = niche_asins - blackbox_asins
    blackbox_only_asins = blackbox_asins - niche_asins

    # WHY: Create lookup dictionaries
    niche_dict = {p['asin']: p for p in niche_products}
    blackbox_dict = {p['asin']: p for p in blackbox_products}

    # WHY: Build comparison results
    niche_only = [niche_dict[asin] for asin in niche_only_asins]
    blackbox_only = [blackbox_dict[asin] for asin in blackbox_only_asins]

    # WHY: For overlap, show both datasets side-by-side
    overlap = []
    for asin in overlap_asins:
        overlap.append({
            'asin': asin,
            'niche_data': niche_dict[asin],
            'blackbox_data': blackbox_dict[asin]
        })

    # WHY: Calculate combined metrics
    all_unique_products = list({**niche_dict, **blackbox_dict}.values())
    combined_total_revenue = sum(p['monthly_revenue'] for p in all_unique_products)

    return {
        'niche_count': len(niche_products),
        'blackbox_count': len(blackbox_products),
        'overlap_count': len(overlap_asins),
        'niche_only_count': len(niche_only_asins),
        'blackbox_only_count': len(blackbox_only_asins),
        'total_unique_products': len(all_unique_products),
        'niche_only': niche_only,
        'blackbox_only': blackbox_only,
        'overlap': overlap,
        'all_unique_products': all_unique_products,
        'combined_total_revenue': combined_total_revenue
    }
