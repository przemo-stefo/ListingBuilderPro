# Deploy Listing Builder Gradio to Mikrus VPS

**Server:** izabela166.mikrus.xyz
**Port:** 10166
**User:** root
**Password:** (stored in CLAUDE.md)

---

## 📋 Prerequisites

- Mikrus VPS server running
- SSH access configured
- Python 3.12+ installed on server
- PM2 for process management

---

## 🚀 Deployment Steps

### 1. Prepare Files for Upload

```bash
cd /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder

# Create deployment package
tar -czf listing-builder-deploy.tar.gz \
  *.py \
  requirements.txt \
  README.md \
  PRODUCTION_README.md \
  --exclude="__pycache__" \
  --exclude="*.log" \
  --exclude="*.pyc" \
  --exclude="venv"
```

### 2. Upload to Server

```bash
# Using sshpass for automated upload
sshpass -p '768ed99431' scp -P 10166 \
  listing-builder-deploy.tar.gz \
  root@izabela166.mikrus.xyz:/root/listing-builder/
```

### 3. SSH into Server & Setup

```bash
# Connect to server
sshpass -p '768ed99431' ssh -p 10166 root@izabela166.mikrus.xyz

# On server:
cd /root/listing-builder
tar -xzf listing-builder-deploy.tar.gz

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Gradio for Production

Create `gradio_config.py`:
```python
# Gradio production configuration
import os

GRADIO_SERVER_NAME = "0.0.0.0"
GRADIO_SERVER_PORT = 7860
GRADIO_SHARE = False  # We use Cloudflare Tunnel instead
GRADIO_AUTH = None  # Optional: add basic auth later
```

### 5. Start with PM2

```bash
# Install PM2 if not installed
npm install -g pm2

# Start Gradio app with PM2
pm2 start python --name listing-builder \
  -- venv/bin/python gradio_app_pro.py

# Save PM2 config
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

### 6. Setup Cloudflare Tunnel

**Tunnel already configured:**
- Tunnel ID: `9af336f2-83f8-440e-b17b-97f6a383ff4c`
- Tunnel Name: `social-agent-tunnel`
- Domain: `social.amzniche.online`

**Update tunnel config to point to Gradio:**

```bash
# Create/update tunnel config
cat > /root/.cloudflared/config.yml <<EOF
tunnel: 9af336f2-83f8-440e-b17b-97f6a383ff4c
credentials-file: /root/.cloudflared/9af336f2-83f8-440e-b17b-97f6a383ff4c.json

ingress:
  - hostname: social.amzniche.online
    service: http://localhost:7860
  - service: http_status:404
EOF

# Restart cloudflared
pm2 restart cloudflared
```

---

## 🔧 Maintenance Commands

### Check Status
```bash
pm2 status
pm2 logs listing-builder
```

### Restart
```bash
pm2 restart listing-builder
```

### Stop
```bash
pm2 stop listing-builder
```

### Update Code
```bash
# On local machine:
cd /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder
tar -czf listing-builder-deploy.tar.gz *.py requirements.txt

# Upload
sshpass -p '768ed99431' scp -P 10166 \
  listing-builder-deploy.tar.gz \
  root@izabela166.mikrus.xyz:/root/listing-builder/

# On server:
cd /root/listing-builder
tar -xzf listing-builder-deploy.tar.gz
pm2 restart listing-builder
```

---

## 🌐 Access

**Public URL:** https://social.amzniche.online

**Health Check:** `curl https://social.amzniche.online`

---

## 🐛 Troubleshooting

### Gradio won't start
```bash
# Check logs
pm2 logs listing-builder --lines 100

# Check if port is in use
lsof -i :7860

# Restart
pm2 restart listing-builder
```

### Cloudflare Tunnel issues
```bash
# Check tunnel status
pm2 logs cloudflared

# Restart tunnel
pm2 restart cloudflared

# Test local connection
curl http://localhost:7860
```

### Python dependencies missing
```bash
cd /root/listing-builder
source venv/bin/activate
pip install -r requirements.txt
pm2 restart listing-builder
```

---

## 📊 Resource Usage

**Expected:**
- RAM: ~500MB (Gradio app)
- CPU: Low (<10%) when idle
- Storage: ~200MB (app + venv)

**Limits:**
- Total RAM: 2.3GB
- Total Disk: 30GB

---

## 🔒 Security

- Basic auth can be added via Gradio's `auth` parameter
- Cloudflare provides DDoS protection
- HTTPS via Cloudflare Tunnel
- Server firewall via Mikrus panel

---

**Status:** Ready for deployment
**Updated:** Nov 2025
