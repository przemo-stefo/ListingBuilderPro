#!/bin/bash
# deploy/izabela166/deploy.sh
# Purpose: Deploy LBP Demo to izabela166 (Michał Lasocki demo)
# Usage: bash deploy.sh [--fresh]

set -e

SERVER="izabela166"
REMOTE_DIR="/root/lbp-demo"
LBP_BACKEND_SRC="$(cd "$(dirname "$0")/../../backend" && pwd)"
LBP_FRONTEND_SRC="$(cd "$(dirname "$0")/../../frontend" && pwd)"
DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_FLAG=""
if [ "$1" = "--fresh" ]; then
  BUILD_FLAG="--no-cache"
  echo "(--fresh: building without Docker cache)"
fi

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

echo "=== Deploying LBP Demo to $SERVER ==="

# Step 1: Sync LBP backend
echo "[1/6] Syncing LBP backend..."
ssh $SERVER "mkdir -p $REMOTE_DIR/lbp-backend"
rsync -avz --delete --exclude='node_modules' --exclude='__pycache__' \
  --exclude='.git' --exclude='venv' --exclude='.env' --exclude='tests' \
  -e "ssh" "$LBP_BACKEND_SRC/" $SERVER:$REMOTE_DIR/lbp-backend/

# Step 2: Sync LBP frontend
echo "[2/6] Syncing LBP frontend..."
ssh $SERVER "mkdir -p $REMOTE_DIR/lbp-frontend"
rsync -avz --delete --exclude='node_modules' --exclude='.next' --exclude='.vercel' \
  --exclude='.git' --exclude='.env.local' \
  -e "ssh" "$LBP_FRONTEND_SRC/" $SERVER:$REMOTE_DIR/lbp-frontend/

# Step 3: Sync config (Dockerfiles, compose, env)
echo "[3/6] Syncing config..."
scp "$DEPLOY_DIR/docker-compose.yml" $SERVER:$REMOTE_DIR/
# WHY: Reuse grzegorz152 Dockerfile (same build)
scp "$(dirname "$0")/../grzegorz152/lbp-frontend/Dockerfile" $SERVER:$REMOTE_DIR/lbp-frontend/Dockerfile

# Copy .env-lbp from grzegorz152 if we don't have local copy
if [ -f "$DEPLOY_DIR/.env-lbp" ]; then
  scp "$DEPLOY_DIR/.env-lbp" $SERVER:$REMOTE_DIR/
elif ssh $SERVER "test -f $REMOTE_DIR/.env-lbp"; then
  echo "  (using server copy of .env-lbp)"
else
  echo "  Copying .env-lbp from grzegorz152..."
  ssh grzegorz152 "cat /root/compliance-guard/.env-lbp" | ssh $SERVER "cat > $REMOTE_DIR/.env-lbp"
fi

# Step 4: Prune
echo "[4/6] Pruning Docker images..."
ssh $SERVER "docker image prune -f" || true

# Step 5: Build + start
echo "[5/6] Building${BUILD_FLAG:+ (no-cache)} and starting..."
ssh $SERVER "cd $REMOTE_DIR && docker compose --env-file .env-lbp build $BUILD_FLAG"
ssh $SERVER "cd $REMOTE_DIR && docker compose --env-file .env-lbp down 2>/dev/null; docker compose --env-file .env-lbp up -d"

# Step 6: Health checks
echo "[6/6] Health checks..."
FAILED=0
check_health "http://localhost:8003/health" "LBP Backend" || FAILED=1
check_health "http://localhost:3004" "LBP Frontend" || FAILED=1

ssh $SERVER "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

if [ "$FAILED" -eq 1 ]; then
  echo "=== DEPLOY FAILED — check: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs --tail 50' ==="
  exit 1
fi

echo "=== Deploy complete (2 LBP containers on $SERVER) ==="
echo "  Backend:  http://localhost:8003/health"
echo "  Frontend: http://localhost:3004"
echo "  Public:   https://demo.automatyzacja-ai.pl (after cloudflared config)"
