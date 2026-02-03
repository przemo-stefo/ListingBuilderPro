#!/usr/bin/env python3
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/generate_secrets.py
# Purpose: Generate secure secrets for production deployment
# NOT for: Storing secrets (add to .env, not to git)

import secrets

print("=" * 60)
print("🔒 SECURE SECRET GENERATION")
print("=" * 60)
print()
print("Copy these to your .env file:")
print()
print("-" * 60)
print(f"API_SECRET_KEY={secrets.token_urlsafe(32)}")
print(f"WEBHOOK_SECRET={secrets.token_urlsafe(32)}")
print("-" * 60)
print()
print("⚠️  IMPORTANT:")
print("   1. Never commit .env to git (it's in .gitignore)")
print("   2. Use different secrets for dev/staging/production")
print("   3. Store production secrets in Railway/Vercel dashboard")
print("   4. Rotate secrets regularly (e.g., every 90 days)")
print()
print("=" * 60)
