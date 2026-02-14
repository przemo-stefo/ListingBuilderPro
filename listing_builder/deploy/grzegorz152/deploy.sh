#!/bin/bash
# deploy/grzegorz152/deploy.sh
# Purpose: One-command deploy to grzegorz152 Mikrus server
# Usage: ./deploy.sh (run from this directory)

set -e

SERVER="grzegorz152"
REMOTE_DIR="/root/compliance-guard"

echo "=== Deploying Compliance Guard to $SERVER ==="

# Step 1: Sync backend code
echo "[1/6] Syncing backend..."
ssh $SERVER "mkdir -p $REMOTE_DIR/backend"
rsync -avz --delete --exclude='node_modules' --exclude='.next' --exclude='__pycache__' \
  --exclude='.git' --exclude='venv' --exclude='.env' \
  -e "ssh" ../../backend/ $SERVER:$REMOTE_DIR/backend/

# Step 2: Sync frontend code
echo "[2/6] Syncing frontend..."
ssh $SERVER "mkdir -p $REMOTE_DIR/frontend"
rsync -avz --delete --exclude='node_modules' --exclude='.next' --exclude='.vercel' \
  --exclude='.git' --exclude='.env.local' \
  -e "ssh" ../../frontend/ $SERVER:$REMOTE_DIR/frontend/

# Step 3: Sync frontend Dockerfile (from deploy config, not source)
echo "[3/6] Syncing config..."
scp frontend/Dockerfile $SERVER:$REMOTE_DIR/frontend/Dockerfile
scp docker-compose.yml $SERVER:$REMOTE_DIR/
# WHY: Only overwrite .env if local copy exists (server may have its own)
if [ -f .env ]; then
  scp .env $SERVER:$REMOTE_DIR/
else
  echo "  (skipping .env — not found locally, using server copy)"
fi

# Step 4: Build containers
echo "[4/6] Building containers..."
ssh $SERVER "cd $REMOTE_DIR && docker compose build --no-cache"

# Step 5: Start services
echo "[5/6] Starting services..."
ssh $SERVER "cd $REMOTE_DIR && docker compose down && docker compose up -d"

# Step 6: Health checks
echo "[6/6] Waiting 30s for startup..."
sleep 30
ssh $SERVER "curl -sf http://localhost:8000/health && echo ' — Backend OK' || echo ' — Backend FAILED'"
ssh $SERVER "curl -sf http://localhost:3000 > /dev/null && echo 'Frontend OK' || echo 'Frontend FAILED'"
ssh $SERVER "docker compose -f $REMOTE_DIR/docker-compose.yml ps"

echo "=== Deploy complete ==="
