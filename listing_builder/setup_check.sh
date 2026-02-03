#!/bin/bash
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/setup_check.sh
# Purpose: Comprehensive system check - what works, what needs fixing
# NOT for: Auto-fixing (shows what YOU need to do)

set -e

PROJECT_DIR="/Users/shawn/Projects/ListingBuilderPro/listing_builder"
cd "$PROJECT_DIR"

echo "========================================================"
echo "🔍 SYSTEM SETUP VERIFICATION"
echo "========================================================"
echo ""

ISSUES=0
WARNINGS=0

# Function to show status
show_status() {
    local check_name=$1
    local status=$2
    local message=$3

    if [ "$status" = "OK" ]; then
        echo "✅ $check_name"
        [ -n "$message" ] && echo "   $message"
    elif [ "$status" = "WARN" ]; then
        echo "⚠️  $check_name"
        echo "   $message"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "❌ $check_name"
        echo "   $message"
        ISSUES=$((ISSUES + 1))
    fi
}

echo "### BACKEND CHECKS ###"
echo ""

# Check 1: Backend .env exists
if [ -f "backend/.env" ]; then
    show_status "Backend .env file" "OK" "File exists"
else
    show_status "Backend .env file" "FAIL" "File missing! Run: python backend/generate_secrets.py"
fi

# Check 2: Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ -n "$PYTHON_VERSION" ]; then
    show_status "Python 3.x installed" "OK" "Version: $PYTHON_VERSION"
else
    show_status "Python 3.x installed" "FAIL" "Python 3 not found"
fi

# Check 3: Backend venv
if [ -d "backend/venv" ]; then
    show_status "Backend virtual environment" "OK" "venv exists"
else
    show_status "Backend virtual environment" "FAIL" "Run: cd backend && python3 -m venv venv"
fi

# Check 4: Backend dependencies
if [ -f "backend/venv/bin/activate" ]; then
    source backend/venv/bin/activate
    if python -c "import fastapi" 2>/dev/null; then
        show_status "Backend dependencies" "OK" "FastAPI installed"
    else
        show_status "Backend dependencies" "FAIL" "Run: cd backend && pip install -r requirements.txt"
    fi
    deactivate
else
    show_status "Backend dependencies" "WARN" "Cannot check - venv not found"
fi

# Check 5: Supabase credentials
if [ -f "backend/.env" ]; then
    SUPABASE_URL=$(grep SUPABASE_URL backend/.env | cut -d'=' -f2)
    if [ -n "$SUPABASE_URL" ]; then
        show_status "Supabase URL configured" "OK" "$SUPABASE_URL"

        # Test DNS resolution
        SUPABASE_HOST=$(echo $SUPABASE_URL | sed 's|https://||' | sed 's|http://||')
        if nslookup $SUPABASE_HOST >/dev/null 2>&1; then
            show_status "Supabase DNS resolution" "OK" "Host resolves"
        else
            show_status "Supabase DNS resolution" "FAIL" "DNS failed - project may not exist. Create new Supabase project!"
        fi
    else
        show_status "Supabase URL configured" "FAIL" "Not set in .env"
    fi
else
    show_status "Supabase credentials" "FAIL" "backend/.env not found"
fi

# Check 6: Groq API key
if [ -f "backend/.env" ]; then
    GROQ_KEY=$(grep GROQ_API_KEY backend/.env | cut -d'=' -f2)
    if [ -n "$GROQ_KEY" ] && [ ${#GROQ_KEY} -gt 20 ]; then
        show_status "Groq API key" "OK" "Key configured (${#GROQ_KEY} chars)"
    else
        show_status "Groq API key" "FAIL" "Not set or too short in .env"
    fi
fi

# Check 7: API secrets
if [ -f "backend/.env" ]; then
    API_KEY=$(grep API_SECRET_KEY backend/.env | cut -d'=' -f2)
    if [ -n "$API_KEY" ] && [ ${#API_KEY} -ge 32 ]; then
        show_status "API Secret Key" "OK" "Strong secret (${#API_KEY} chars)"
    else
        show_status "API Secret Key" "FAIL" "Missing or weak. Run: python backend/generate_secrets.py"
    fi
fi

# Check 8: Redis (optional)
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping >/dev/null 2>&1; then
        show_status "Redis server" "OK" "Running and accessible"
    else
        show_status "Redis server" "WARN" "Installed but not running. Run: brew services start redis"
    fi
else
    show_status "Redis server" "WARN" "Not installed. Optional for background jobs. Install: brew install redis"
fi

echo ""
echo "### FRONTEND CHECKS ###"
echo ""

# Check 9: Node.js
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    show_status "Node.js installed" "OK" "Version: $NODE_VERSION"
else
    show_status "Node.js installed" "FAIL" "Node.js not found. Install from https://nodejs.org"
fi

# Check 10: Frontend .env.local
if [ -f "frontend/.env.local" ]; then
    show_status "Frontend .env.local" "OK" "File exists"

    # Check API key match
    if [ -f "backend/.env" ]; then
        BACKEND_KEY=$(grep API_SECRET_KEY backend/.env | cut -d'=' -f2)
        FRONTEND_KEY=$(grep NEXT_PUBLIC_API_KEY frontend/.env.local | cut -d'=' -f2)
        if [ "$BACKEND_KEY" = "$FRONTEND_KEY" ]; then
            show_status "API keys match" "OK" "Backend and frontend keys are identical"
        else
            show_status "API keys match" "FAIL" "Keys don't match! Copy API_SECRET_KEY from backend/.env to frontend/.env.local"
        fi
    fi
else
    show_status "Frontend .env.local" "FAIL" "File missing! Copy from .env.local.example"
fi

# Check 11: Frontend dependencies
if [ -d "frontend/node_modules" ]; then
    show_status "Frontend dependencies" "OK" "node_modules exists"
else
    show_status "Frontend dependencies" "FAIL" "Run: cd frontend && npm install"
fi

echo ""
echo "### DATABASE CHECKS ###"
echo ""

# Check 12: Database migration file
if [ -f "backend/migrations/001_initial_schema.sql" ]; then
    show_status "Database migration SQL" "OK" "Migration file exists"
else
    show_status "Database migration SQL" "FAIL" "Migration file missing"
fi

# Check 13: Test database connection (if backend running)
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    DB_STATUS=$(curl -s http://localhost:8000/health | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
    if [ "$DB_STATUS" = "connected" ]; then
        show_status "Database connection" "OK" "Backend can connect to database"
    else
        show_status "Database connection" "FAIL" "Backend cannot connect. Check Supabase credentials."
    fi
else
    show_status "Database connection" "WARN" "Cannot test - backend not running"
fi

echo ""
echo "### OPTIONAL COMPONENTS ###"
echo ""

# Check 14: Dramatiq worker
if [ -f "backend/workers/ai_worker.py" ]; then
    show_status "AI Worker file" "OK" "Worker exists"
else
    show_status "AI Worker file" "WARN" "Worker file missing (optional)"
fi

echo ""
echo "========================================================"
echo "SUMMARY"
echo "========================================================"
echo ""

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "🎉 PERFECT! Everything is configured correctly!"
    echo ""
    echo "Next step: ./start_all.sh"
elif [ $ISSUES -eq 0 ]; then
    echo "✅ GOOD! System is functional with $WARNINGS warnings."
    echo ""
    echo "Warnings are for optional components."
    echo "You can start the system: ./start_all.sh"
else
    echo "⚠️  ISSUES FOUND: $ISSUES critical, $WARNINGS warnings"
    echo ""
    echo "Fix the ❌ issues above before starting the system."
    echo "See SETUP_COMPLETE_GUIDE.md for detailed instructions."
fi

echo ""
echo "========================================================"
