#!/usr/bin/env python3
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/verify_setup.py
# Purpose: Verify backend setup and dependencies
# NOT for: Production use

import sys
import os

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        return False
    print("✅ .env file exists")
    return True


def check_dependencies():
    """Check if all required packages are installed"""
    required = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "supabase",
        "groq",
        "pydantic",
        "structlog",
    ]

    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✅ {pkg}")
        except ImportError:
            print(f"❌ {pkg} not installed")
            missing.append(pkg)

    if missing:
        print("\n❌ Missing packages. Run: pip install -r requirements.txt")
        return False

    return True


def check_database():
    """Check database connection"""
    try:
        from database import check_db_connection
        if check_db_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            print("   Check DATABASE_URL in .env")
            return False
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False


def check_groq():
    """Check Groq API key"""
    try:
        from config import settings
        if settings.groq_api_key and settings.groq_api_key != "":
            print("✅ Groq API key configured")
            return True
        else:
            print("⚠️  Groq API key not set")
            print("   Set GROQ_API_KEY in .env")
            return False
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False


def main():
    print("🔍 Verifying Backend Setup...\n")

    checks = [
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("Groq API", check_groq),
    ]

    results = []
    for name, check_fn in checks:
        print(f"\n{name}:")
        result = check_fn()
        results.append(result)

    print("\n" + "="*50)
    if all(results):
        print("✅ All checks passed! Ready to start.")
        print("\nRun: ./start.sh")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Fix issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
