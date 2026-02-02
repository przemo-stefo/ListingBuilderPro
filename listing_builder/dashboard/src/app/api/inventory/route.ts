// src/app/api/inventory/route.ts
// Purpose: Mock API endpoint returning inventory data with filtering
// NOT for: Real inventory sync (replace with actual backend later)

import { NextResponse } from 'next/server';

const inventory = [
  {
    sku: 'AMZ-DE-1042',
    marketplace: 'amazon',
    title: 'Wireless Bluetooth Earbuds Pro - Noise Cancelling',
    quantity: 342,
    price: 29.99,
    asin: 'B0EXAMPLE01',
    fulfillment_channel: 'FBA',
    condition: 'New',
    last_updated: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
  },
  {
    sku: 'AMZ-UK-3391',
    marketplace: 'amazon',
    title: 'USB-C Charging Cable 2m (3-Pack)',
    quantity: 15,
    price: 12.99,
    asin: 'B0EXAMPLE02',
    fulfillment_channel: 'FBA',
    condition: 'New',
    last_updated: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
  },
  {
    sku: 'AMZ-FR-2210',
    marketplace: 'amazon',
    title: 'Silicone Kitchen Utensil Set (12pc)',
    quantity: 0,
    price: 24.99,
    asin: 'B0EXAMPLE03',
    fulfillment_channel: 'FBM',
    condition: 'New',
    last_updated: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
  },
  {
    sku: 'EB-PRC-0553',
    marketplace: 'ebay',
    title: 'Vintage Leather Wallet - Genuine Cowhide',
    quantity: 87,
    price: 34.50,
    listing_id: 'EBAY-29481',
    fulfillment_channel: 'Seller',
    condition: 'New',
    last_updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    sku: 'EB-ACC-1177',
    marketplace: 'ebay',
    title: 'Phone Stand Adjustable Aluminum Desktop Holder',
    quantity: 8,
    price: 15.99,
    listing_id: 'EBAY-39102',
    fulfillment_channel: 'Seller',
    condition: 'New',
    last_updated: new Date(Date.now() - 10 * 60 * 60 * 1000).toISOString(),
  },
  {
    sku: 'KL-WEEE-0087',
    marketplace: 'kaufland',
    title: 'LED Desk Lamp with USB Port - Dimmable',
    quantity: 53,
    price: 39.99,
    fulfillment_channel: 'Seller',
    condition: 'New',
    last_updated: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
  },
  {
    sku: 'KL-HOME-0214',
    marketplace: 'kaufland',
    title: 'Stainless Steel Water Bottle 750ml',
    quantity: 0,
    price: 18.99,
    fulfillment_channel: 'Seller',
    condition: 'New',
    last_updated: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    sku: 'AMZ-ES-4410',
    marketplace: 'amazon',
    title: 'Yoga Mat Extra Thick 10mm - Non Slip',
    quantity: 128,
    price: 22.99,
    asin: 'B0EXAMPLE04',
    fulfillment_channel: 'FBA',
    condition: 'New',
    last_updated: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },
  {
    sku: 'EB-TOOL-0821',
    marketplace: 'ebay',
    title: 'Precision Screwdriver Set 60-in-1 Magnetic',
    quantity: 4,
    price: 19.99,
    listing_id: 'EBAY-51003',
    fulfillment_channel: 'Seller',
    condition: 'New',
    last_updated: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
  },
  {
    sku: 'KL-ELEC-0399',
    marketplace: 'kaufland',
    title: 'Portable Bluetooth Speaker Waterproof IPX7',
    quantity: 210,
    price: 44.99,
    fulfillment_channel: 'Seller',
    condition: 'New',
    last_updated: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
  },
];

// Default threshold for "low stock"
const DEFAULT_LOW_STOCK_THRESHOLD = 20;

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const marketplace = searchParams.get('marketplace');
  const lowStock = searchParams.get('low_stock') === 'true';
  const threshold = parseInt(searchParams.get('threshold') || '', 10) || DEFAULT_LOW_STOCK_THRESHOLD;

  let filtered = inventory;

  if (marketplace) {
    filtered = filtered.filter(item => item.marketplace === marketplace);
  }

  if (lowStock) {
    filtered = filtered.filter(item => item.quantity <= threshold);
  }

  return NextResponse.json({
    items: filtered,
    total: filtered.length,
    limit: 50,
    offset: 0,
  });
}
