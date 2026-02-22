// frontend/src/app/api/health/route.ts
// Purpose: Health check endpoint for monitoring (Telegram bot, uptime checks)
// NOT for: Backend health — that's at api-listing.feedmasters.org/health

import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ status: "ok", service: "frontend" });
}
