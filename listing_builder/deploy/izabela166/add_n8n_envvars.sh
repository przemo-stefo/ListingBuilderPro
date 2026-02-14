#!/bin/bash
# deploy/izabela166/add_n8n_envvars.sh
# Purpose: Restart n8n container on izabela166 with additional env vars
# NOT for: Deploying the workflow itself (already imported)
#
# Usage: bash add_n8n_envvars.sh <SCRAPE_DO_TOKEN> <WEBHOOK_SECRET>
# Values: Get from Render dashboard → LBP service → Environment

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <SCRAPE_DO_TOKEN> <WEBHOOK_SECRET>"
  echo ""
  echo "Get values from: https://dashboard.render.com/web/srv-d644kr0gjchc739fjdq0/env"
  echo "  SCRAPE_DO_TOKEN = Scrape.do API key"
  echo "  WEBHOOK_SECRET  = LBP webhook authentication"
  exit 1
fi

SCRAPE_DO_TOKEN="$1"
WEBHOOK_SECRET="$2"

echo "=== Restarting n8n on izabela166 with new env vars ==="

ssh izabela166 bash -s <<REMOTE_SCRIPT
set -euo pipefail

echo "[1/4] Stopping n8n container..."
docker stop n8n

echo "[2/4] Removing old container (data preserved in /root/n8n-data)..."
docker rm n8n

echo "[3/4] Starting n8n with SCRAPE_DO_TOKEN + WEBHOOK_SECRET..."
docker run -d \
  --name n8n \
  --restart unless-stopped \
  -p 30166:5678 \
  -v /root/n8n-data:/home/node/.n8n \
  -e GENERIC_TIMEZONE=Europe/Warsaw \
  -e N8N_EDITOR_BASE_URL=https://n8n.feedmasters.org/ \
  -e N8N_PORT=5678 \
  -e N8N_PROTOCOL=https \
  -e N8N_DISABLE_PRODUCTION_MAIN_PROCESS=false \
  -e EXECUTIONS_MODE=regular \
  -e WEBHOOK_URL=https://n8n.feedmasters.org/ \
  -e N8N_HOST=0.0.0.0 \
  -e N8N_SECURE_COOKIE=false \
  -e SCRAPE_DO_TOKEN="${SCRAPE_DO_TOKEN}" \
  -e WEBHOOK_SECRET="${WEBHOOK_SECRET}" \
  n8nio/n8n:latest

echo "[4/4] Waiting for n8n to start..."
sleep 10

# Verify
if docker exec n8n env | grep -q SCRAPE_DO_TOKEN; then
  echo "✅ SCRAPE_DO_TOKEN: set"
else
  echo "❌ SCRAPE_DO_TOKEN: missing!"
fi

if docker exec n8n env | grep -q WEBHOOK_SECRET; then
  echo "✅ WEBHOOK_SECRET: set"
else
  echo "❌ WEBHOOK_SECRET: missing!"
fi

echo ""
echo "=== n8n status ==="
docker ps --filter name=n8n --format "{{.Status}}"

echo ""
echo "Done! Open https://n8n.feedmasters.org to verify."
REMOTE_SCRIPT
