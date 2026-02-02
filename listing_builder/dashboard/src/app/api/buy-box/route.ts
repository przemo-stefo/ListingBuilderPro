// src/app/api/buy-box/route.ts
// Purpose: Mock API endpoint returning buy box status data
// NOT for: Real buy box monitoring (replace with actual backend later)

import { NextResponse } from 'next/server';

const buyBoxItems = [
  {
    asin: 'B0EXAMPLE01',
    sku: 'AMZ-DE-1042',
    title: 'Wireless Bluetooth Earbuds Pro - Noise Cancelling',
    has_buy_box: true,
    your_price: 29.99,
    buy_box_price: 29.99,
    competitor_price: 31.49,
    price_difference: 0,
    last_checked: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
  },
  {
    asin: 'B0EXAMPLE02',
    sku: 'AMZ-UK-3391',
    title: 'USB-C Charging Cable 2m (3-Pack)',
    has_buy_box: false,
    your_price: 14.99,
    buy_box_price: 12.49,
    competitor_price: 12.49,
    price_difference: 2.50,
    last_checked: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },
  {
    asin: 'B0EXAMPLE03',
    sku: 'AMZ-FR-2210',
    title: 'Silicone Kitchen Utensil Set (12pc)',
    has_buy_box: true,
    your_price: 24.99,
    buy_box_price: 24.99,
    competitor_price: 26.99,
    price_difference: 0,
    last_checked: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
  },
  {
    asin: 'B0EXAMPLE04',
    sku: 'AMZ-ES-4410',
    title: 'Yoga Mat Extra Thick 10mm - Non Slip',
    has_buy_box: true,
    your_price: 22.99,
    buy_box_price: 22.99,
    competitor_price: 24.50,
    price_difference: 0,
    last_checked: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
  },
  {
    asin: 'B0EXAMPLE05',
    sku: 'AMZ-DE-5580',
    title: 'Stainless Steel Insulated Travel Mug 500ml',
    has_buy_box: false,
    your_price: 19.99,
    buy_box_price: 17.49,
    competitor_price: 17.49,
    price_difference: 2.50,
    last_checked: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
  },
  {
    asin: 'B0EXAMPLE06',
    sku: 'AMZ-UK-6621',
    title: 'Bamboo Cutting Board Set (3-Pack)',
    has_buy_box: true,
    your_price: 18.99,
    buy_box_price: 18.99,
    competitor_price: 19.99,
    price_difference: 0,
    last_checked: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
  },
  {
    asin: 'B0EXAMPLE07',
    sku: 'AMZ-FR-7734',
    title: 'LED Night Light Motion Sensor (2-Pack)',
    has_buy_box: false,
    your_price: 15.99,
    buy_box_price: 13.99,
    competitor_price: 13.99,
    price_difference: 2.00,
    last_checked: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
  {
    asin: 'B0EXAMPLE08',
    sku: 'AMZ-DE-8847',
    title: 'Microfiber Cleaning Cloth Set (12-Pack)',
    has_buy_box: true,
    your_price: 9.99,
    buy_box_price: 9.99,
    competitor_price: 11.49,
    price_difference: 0,
    last_checked: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
  },
];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const lostOnly = searchParams.get('lost_only') === 'true';

  let filtered = buyBoxItems;
  if (lostOnly) {
    filtered = filtered.filter(item => !item.has_buy_box);
  }

  const winning = filtered.filter(i => i.has_buy_box).length;
  const losing = filtered.filter(i => !i.has_buy_box).length;

  return NextResponse.json({
    items: filtered,
    total: filtered.length,
    winning_count: winning,
    losing_count: losing,
  });
}
