#!/bin/bash
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/start_all.sh
# Purpose: Start backend and frontend in parallel
# NOT for: Production deployment (use separate processes)

set -e

PROJECT_DIR="/Users/shawn/Projects/ListingBuilderPro/listing_builder"

echo "========================================================"
echo "🚀 Starting Marketplace Automation System"
echo "========================================================"
echo ""

# Check if backend/.env exists
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
    echo "❌ Error: backend/.env not found!"
    echo "   Run: cd backend && python generate_secrets.py"
    echo "   Then create .env file with credentials"
    exit 1
fi

# Check if frontend/.env.local exists
if [ ! -f "$PROJECT_DIR/frontend/.env.local" ]; then
    echo "❌ Error: frontend/.env.local not found!"
    echo "   Copy frontend/.env.local.example to .env.local"
    echo "   And set NEXT_PUBLIC_API_KEY"
    exit 1
fi

echo "✅ Configuration files found"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "========================================================"
    echo "🛑 Stopping services..."
    echo "========================================================"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Start Backend
echo "▶️  Starting Backend (http://localhost:8000)..."
cd "$PROJECT_DIR/backend"

# Activate venv and start backend
if [ -d "venv" ]; then
    source venv/bin/activate
    python main.py &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
else
    echo "⚠️  Warning: venv not found in backend/"
    python3 main.py &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
fi

# Wait for backend to start
echo "   Waiting for backend to start..."
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ Backend is running!"
else
    echo "   ⚠️  Backend may not be ready yet (still starting...)"
fi

echo ""

# Start Frontend
echo "▶️  Starting Frontend (http://localhost:3000)..."
cd "$PROJECT_DIR/frontend"

npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "========================================================"
echo "✅ System Started!"
echo "========================================================"
echo ""
echo "📍 URLs:"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Frontend:     http://localhost:3000"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "🔑 API Key (X-API-Key header):"
echo "   $(grep API_SECRET_KEY backend/.env | cut -d'=' -f2)"
echo ""
echo "⌨️  Press Ctrl+C to stop both services"
echo "========================================================"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
