#!/bin/bash
# deploy/grzegorz152/deploy.sh
# Purpose: One-command deploy to grzegorz152 Mikrus server (Compliance Guard + LBP)
# Usage: ./deploy.sh [--fresh] (run from this directory)
# --fresh: Force rebuild without Docker cache (default: use cache)

set -e

SERVER="grzegorz152"
REMOTE_DIR="/root/compliance-guard"
LBP_BACKEND_SRC="$(cd "$(dirname "$0")/../../backend" && pwd)"
BUILD_FLAG=""
if [ "$1" = "--fresh" ]; then
  BUILD_FLAG="--no-cache"
  echo "(--fresh: building without Docker cache)"
fi

# WHY function: Polling loop instead of fixed sleep — detects failures reliably
check_health() {
  local url=$1 label=$2
  for i in {1..12}; do
    if ssh $SERVER "curl -sf $url" > /dev/null 2>&1; then
      echo "  $label OK"
      return 0
    fi
    sleep 5
  done
  echo "  FATAL: $label failed after 60s"
  return 1
}

echo "=== Deploying Compliance Guard + LBP to $SERVER ==="

# Step 1: Sync Compliance Guard backend code
echo "[1/7] Syncing Compliance Guard backend..."
ssh $SERVER "mkdir -p $REMOTE_DIR/backend"
rsync -avz --delete --exclude='node_modules' --exclude='.next' --exclude='__pycache__' \
  --exclude='.git' --exclude='venv' --exclude='.env' \
  -e "ssh" ../../backend/ $SERVER:$REMOTE_DIR/backend/

# Step 2: Sync Compliance Guard frontend code
echo "[2/7] Syncing Compliance Guard frontend..."
ssh $SERVER "mkdir -p $REMOTE_DIR/frontend"
rsync -avz --delete --exclude='node_modules' --exclude='.next' --exclude='.vercel' \
  --exclude='.git' --exclude='.env.local' \
  -e "ssh" ../../frontend/ $SERVER:$REMOTE_DIR/frontend/

# Step 3: Sync LBP backend code
echo "[3/7] Syncing LBP backend..."
ssh $SERVER "mkdir -p $REMOTE_DIR/lbp-backend"
rsync -avz --delete --exclude='node_modules' --exclude='__pycache__' \
  --exclude='.git' --exclude='venv' --exclude='.env' \
  -e "ssh" "$LBP_BACKEND_SRC/" $SERVER:$REMOTE_DIR/lbp-backend/

# Step 4: Sync config files (never overwrite server .env — secrets live there)
echo "[4/7] Syncing config..."
scp frontend/Dockerfile $SERVER:$REMOTE_DIR/frontend/Dockerfile
scp docker-compose.yml $SERVER:$REMOTE_DIR/
if [ -f .env ]; then
  scp .env $SERVER:$REMOTE_DIR/
else
  echo "  (skipping .env — using server copy)"
fi
if [ -f .env-lbp ]; then
  scp .env-lbp $SERVER:$REMOTE_DIR/
else
  echo "  (skipping .env-lbp — using server copy)"
fi

# Step 5: Build containers
echo "[5/7] Building containers${BUILD_FLAG:+ (no-cache)}..."
ssh $SERVER "cd $REMOTE_DIR && docker compose build $BUILD_FLAG"

# Step 6: Restart services
echo "[6/7] Restarting services..."
ssh $SERVER "cd $REMOTE_DIR && docker compose down && docker compose up -d"

# Step 7: Health checks (polling with 60s timeout, exit 1 on failure)
echo "[7/7] Health checks..."
FAILED=0
check_health "http://localhost:8000/health" "Compliance Guard" || FAILED=1
check_health "http://localhost:3000" "Compliance Frontend" || FAILED=1
check_health "http://localhost:8001/health" "LBP Backend" || FAILED=1

ssh $SERVER "docker compose -f $REMOTE_DIR/docker-compose.yml ps"

if [ "$FAILED" -eq 1 ]; then
  echo "=== DEPLOY FAILED — check logs: ssh $SERVER 'docker compose -f $REMOTE_DIR logs --tail 50' ==="
  exit 1
fi

echo "=== Deploy complete ==="
