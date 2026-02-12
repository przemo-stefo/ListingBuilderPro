#!/bin/bash
# deploy/grzegorz152/deploy.sh
# Purpose: One-command deploy to grzegorz152 Mikrus server
# Usage: ./deploy.sh (run from this directory)

set -e

SERVER="grzegorz152"
REMOTE_DIR="/root/compliance-guard"

echo "=== Deploying Compliance Guard to $SERVER ==="

# Step 1: Sync code to server
echo "[1/4] Syncing code..."
ssh $SERVER "mkdir -p $REMOTE_DIR"
rsync -avz --exclude='node_modules' --exclude='.next' --exclude='__pycache__' \
  --exclude='.git' --exclude='venv' --exclude='.env' \
  -e "ssh" ../../backend/ $SERVER:$REMOTE_DIR/backend/

# Step 2: Sync docker-compose + env
echo "[2/4] Syncing config..."
scp docker-compose.yml $SERVER:$REMOTE_DIR/
scp .env $SERVER:$REMOTE_DIR/

# Step 3: Build and start
echo "[3/4] Building containers..."
ssh $SERVER "cd $REMOTE_DIR && docker compose build --no-cache"

echo "[4/4] Starting services..."
ssh $SERVER "cd $REMOTE_DIR && docker compose down && docker compose up -d"

# Step 4: Health check
echo "Waiting 15s for startup..."
sleep 15
ssh $SERVER "curl -sf http://localhost:8000/health && echo ' — Backend OK' || echo ' — Backend FAILED'"
ssh $SERVER "docker compose -f $REMOTE_DIR/docker-compose.yml ps"

echo "=== Deploy complete ==="
