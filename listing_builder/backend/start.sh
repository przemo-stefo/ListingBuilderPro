#!/bin/bash
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/start.sh
# Purpose: Quick start script for development
# NOT for: Production deployment

set -e

echo "🚀 Starting Marketplace Listing Automation Backend..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your credentials before continuing."
    exit 1
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check database connection
echo "🔍 Checking database connection..."
python -c "from database import check_db_connection; import sys; sys.exit(0 if check_db_connection() else 1)" || {
    echo "❌ Database connection failed. Check your DATABASE_URL in .env"
    exit 1
}

echo "✅ Database connected"

# Start API server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

uvicorn main:app --reload --host 0.0.0.0 --port 8000
