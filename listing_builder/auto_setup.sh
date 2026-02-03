#!/bin/bash
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/auto_setup.sh
# Purpose: Automatically fix all setup issues (except database migration)
# NOT for: Database setup (requires manual SQL execution)

set -e

PROJECT_DIR="/Users/shawn/Projects/ListingBuilderPro/listing_builder"
cd "$PROJECT_DIR"

echo "========================================================"
echo "🤖 AUTOMATIC SETUP - Fixing Everything"
echo "========================================================"
echo ""

# Function to show progress
show_step() {
    echo ""
    echo "▶️  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Step 1: Backend venv
show_step "STEP 1/3: Setting up Backend Virtual Environment"

if [ ! -d "backend/venv" ]; then
    echo "Creating venv..."
    cd backend
    python3 -m venv venv
    echo "✅ venv created"

    echo ""
    echo "Installing dependencies (this may take 2-3 minutes)..."
    source venv/bin/activate
    pip install --quiet -r requirements.txt
    echo "✅ Dependencies installed"
    deactivate
    cd ..
else
    echo "✅ venv already exists"

    # Check if dependencies installed
    source backend/venv/bin/activate
    if python -c "import fastapi" 2>/dev/null; then
        echo "✅ Dependencies already installed"
    else
        echo "Installing missing dependencies..."
        pip install --quiet -r backend/requirements.txt
        echo "✅ Dependencies installed"
    fi
    deactivate
fi

# Step 2: Frontend dependencies
show_step "STEP 2/3: Installing Frontend Dependencies"

if [ ! -d "frontend/node_modules" ]; then
    echo "Installing npm packages (this may take 2-3 minutes)..."
    cd frontend
    npm install --silent
    echo "✅ Frontend dependencies installed"
    cd ..
else
    echo "✅ node_modules already exists"
fi

# Step 3: Database info
show_step "STEP 3/3: Database Setup (Manual Step Required)"

echo "⚠️  DATABASE REQUIRES MANUAL SETUP"
echo ""
echo "You need to run the SQL migration manually:"
echo ""
echo "1. Open: https://supabase.com/dashboard/project/ajbpzkmhvryfsiphoysu"
echo "2. Click: 'SQL Editor' in left menu"
echo "3. Click: 'New query'"
echo "4. Copy/paste file: backend/migrations/001_initial_schema.sql"
echo "5. Click: 'Run'"
echo ""
echo "This creates 6 tables: products, import_jobs, bulk_jobs, sync_logs, webhooks, webhook_logs"
echo ""

read -p "Press ENTER after you've completed the SQL migration..."

echo ""
echo "========================================================"
echo "✅ AUTOMATIC SETUP COMPLETE"
echo "========================================================"
echo ""
echo "Running verification check..."
echo ""

# Run verification
./setup_check.sh

echo ""
echo "========================================================"
echo "🎯 NEXT STEPS"
echo "========================================================"
echo ""
echo "If all checks passed, start the system:"
echo ""
echo "   ./start_all.sh"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "========================================================"
