#!/bin/bash
# deploy/anna130/deploy-marcin.sh
# Purpose: Deploy n8n + PostgreSQL for Marcin Nastarowicz on anna130
# Usage: ./deploy-marcin.sh [--fresh]

set -e

SERVER="anna130"
REMOTE_DIR="/root/n8n-marcin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_DIR="$(cd "$SCRIPT_DIR/../../n8n-marcin" && pwd)"
BUILD_FLAG=""

if [ "$1" = "--fresh" ]; then
  BUILD_FLAG="--no-cache"
  echo "(--fresh: pulling latest images)"
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

echo "=== Deploying n8n-marcin to $SERVER ==="

# Step 0: Ensure qdrant_bridge Docker network exists (for n8n ↔ Qdrant)
echo "[0/6] Ensuring qdrant_bridge network..."
ssh $SERVER "docker network create qdrant_bridge 2>/dev/null || true"
# Connect Qdrant container if not already connected
ssh $SERVER "docker network connect qdrant_bridge qdrant 2>/dev/null || true"

# Step 1: Create remote dir
echo "[1/6] Preparing remote directory..."
ssh $SERVER "mkdir -p $REMOTE_DIR/workflows"

# Step 2: Sync docker-compose + workflows
echo "[2/6] Syncing files..."
scp "$SCRIPT_DIR/docker-compose.yml" $SERVER:$REMOTE_DIR/
rsync -avz "$WORKFLOW_DIR/"*.json $SERVER:$REMOTE_DIR/workflows/

# Step 3: Check .env exists on server
echo "[3/6] Checking .env..."
if ! ssh $SERVER "test -f $REMOTE_DIR/.env"; then
  echo "  ERROR: No .env file on server!"
  echo "  Run: scp env-template.txt $SERVER:$REMOTE_DIR/.env"
  echo "  Then edit the values on the server."
  exit 1
fi

# Step 4: Pull & start containers
echo "[4/6] Starting containers..."
ssh $SERVER "cd $REMOTE_DIR && docker compose pull $BUILD_FLAG && docker compose up -d"

# Step 5: Health check
echo "[5/6] Health check..."
check_health "http://localhost:5678/healthz" "n8n"

echo "[6/6] Verifying Qdrant connectivity..."
if ssh $SERVER "curl -sf http://localhost:6333/collections" > /dev/null 2>&1; then
  echo "  Qdrant OK"
else
  echo "  WARNING: Qdrant not reachable on localhost:6333 — check inner_circle_rag compose"
fi

ssh $SERVER "cd $REMOTE_DIR && docker compose ps"

echo ""
echo "=== Deploy complete ==="
echo "n8n UI: https://n8n-marcin.feedmasters.org"
echo "Qdrant: http://localhost:6333 (via qdrant_bridge network)"
echo "Workflows to import: $REMOTE_DIR/workflows/"
echo ""
echo "Next: Import workflows via n8n API:"
echo "  ssh $SERVER"
echo "  cd $REMOTE_DIR"
echo "  for f in workflows/*.json; do"
echo '    curl -X POST http://localhost:5678/api/v1/workflows \'
echo '      -H "Content-Type: application/json" \'
echo '      -d @"\$f"'
echo "  done"
