#!/usr/bin/env python3
# scripts/exchange_sp_api_code.py
# Purpose: Exchange SP-API authorization_code for refresh_token (one-time use)
# Usage: python3 exchange_sp_api_code.py <spapi_oauth_code>

import sys
import httpx

import os
CLIENT_ID = os.environ.get("AMAZON_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AMAZON_CLIENT_SECRET", "")
LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Set AMAZON_CLIENT_ID and AMAZON_CLIENT_SECRET env vars first")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: AMAZON_CLIENT_ID=... AMAZON_CLIENT_SECRET=... python3 exchange_sp_api_code.py <spapi_oauth_code>")
    print("  The code comes from Amazon redirect after seller authorization")
    sys.exit(1)

code = sys.argv[1]

resp = httpx.post(LWA_TOKEN_URL, data={
    "grant_type": "authorization_code",
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
})

if resp.status_code == 200:
    data = resp.json()
    print("=== SUCCESS ===")
    print(f"Refresh Token: {data['refresh_token']}")
    print(f"Access Token:  {data['access_token'][:20]}...")
    print(f"Expires in:    {data.get('expires_in', '?')}s")
    print()
    print("Add to .env:")
    print(f"AMAZON_REFRESH_TOKEN={data['refresh_token']}")
else:
    print(f"ERROR {resp.status_code}: {resp.text}")
