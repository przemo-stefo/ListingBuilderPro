#!/bin/bash
# deploy/anna130/healthcheck.sh
# Purpose: Self-healing monitor for n8n-marcin stack — auto-restart + Telegram alerts
# NOT for: Qdrant container itself (managed in inner_circle_rag)
# Cron: */5 * * * * /bin/bash /root/n8n-marcin/healthcheck.sh

# Read credentials from OpenClaw .env (same bot used by other monitors)
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN /root/.openclaw/.env 2>/dev/null | cut -d= -f2)
CHAT_ID=$(grep TELEGRAM_CHAT_ID /root/.openclaw/.env 2>/dev/null | cut -d= -f2)
COMPOSE_DIR="/root/n8n-marcin"
LOG="/tmp/n8n-marcin-health.log"
COOLDOWN_FILE="/tmp/n8n-marcin-alert-sent"
MAX_LOG_LINES=500

send_telegram() {
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="$CHAT_ID" \
        -d text="$1" \
        -d parse_mode="HTML" > /dev/null 2>&1
}

# Cooldown: max 1 alert per 30 min (avoid spam)
check_cooldown() {
    if [ -f "$COOLDOWN_FILE" ]; then
        last=$(stat -c %Y "$COOLDOWN_FILE" 2>/dev/null || stat -f %m "$COOLDOWN_FILE" 2>/dev/null)
        now=$(date +%s)
        diff=$((now - last))
        if [ "$diff" -lt 1800 ]; then
            return 1  # still in cooldown
        fi
    fi
    return 0  # can send
}

mark_cooldown() {
    touch "$COOLDOWN_FILE"
}

issues=""
fixes=""

# 1. Check Docker containers
for container in n8n-marcin n8n-postgres n8n-tunnel; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        issues="${issues}❌ Container ${container} DOWN\n"
        cd "$COMPOSE_DIR" && docker compose up -d 2>/dev/null
        sleep 5
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            fixes="${fixes}✅ ${container} auto-restarted\n"
        else
            fixes="${fixes}⚠️ ${container} FAILED to restart\n"
        fi
    fi
done

# 2. Check Qdrant (separate compose)
if ! docker ps --format '{{.Names}}' | grep -q "qdrant"; then
    issues="${issues}❌ Qdrant DOWN\n"
    cd /root/inner_circle_rag && docker compose up -d qdrant 2>/dev/null
    sleep 3
    if docker ps --format '{{.Names}}' | grep -q "qdrant"; then
        fixes="${fixes}✅ Qdrant auto-restarted\n"
    else
        fixes="${fixes}⚠️ Qdrant FAILED to restart\n"
    fi
fi

# 3. HTTP health — n8n
n8n_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://127.0.0.1:5678/healthz 2>/dev/null)
if [ "$n8n_status" != "200" ]; then
    issues="${issues}❌ n8n HTTP ${n8n_status:-timeout}\n"
    docker restart n8n-marcin 2>/dev/null
    sleep 10
    n8n_retry=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://127.0.0.1:5678/healthz 2>/dev/null)
    if [ "$n8n_retry" = "200" ]; then
        fixes="${fixes}✅ n8n HTTP restored after restart\n"
    else
        fixes="${fixes}⚠️ n8n still not responding (${n8n_retry})\n"
    fi
fi

# 4. HTTP health — Qdrant
qdrant_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://127.0.0.1:6333/healthz 2>/dev/null)
if [ "$qdrant_status" != "200" ]; then
    issues="${issues}❌ Qdrant HTTP ${qdrant_status:-timeout}\n"
fi

# 5. Workflow active status — check 3 core workflows via n8n API
N8N_KEY=$(docker exec n8n-postgres psql -U n8n -d n8n_marcin -t -c "SELECT \"apiKey\" FROM user_api_keys LIMIT 1;" 2>/dev/null | tr -d ' \n')
if [ -n "$N8N_KEY" ]; then
    for wf_id in 1hJYRL7dIocTYMZN yKdRPPkdrTmLWK11 cQBUCuz8SkHExoNm UpZPGjZ4qVBa7ams eioKMK3F9zmkfpQT BJevcP0tiQIgsPr3 kQLTVj1H5VxXX9ns VEkwyF3B4IIKHEFu; do
        wf_json=$(curl -s --max-time 10 "http://127.0.0.1:5678/api/v1/workflows/${wf_id}" -H "X-N8N-API-KEY: $N8N_KEY" 2>/dev/null)
        wf_name=$(echo "$wf_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('name','?'))" 2>/dev/null)
        wf_active=$(echo "$wf_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('active',False))" 2>/dev/null)
        if [ "$wf_active" != "True" ]; then
            issues="${issues}❌ Workflow '${wf_name}' (${wf_id}) INACTIVE\n"
            # Auto-activate
            curl -s -X POST "http://127.0.0.1:5678/api/v1/workflows/${wf_id}/activate" -H "X-N8N-API-KEY: $N8N_KEY" > /dev/null 2>&1
            sleep 2
            recheck=$(curl -s --max-time 10 "http://127.0.0.1:5678/api/v1/workflows/${wf_id}" -H "X-N8N-API-KEY: $N8N_KEY" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('active',False))" 2>/dev/null)
            if [ "$recheck" = "True" ]; then
                fixes="${fixes}✅ ${wf_name} auto-activated\n"
            else
                fixes="${fixes}⚠️ ${wf_name} FAILED to activate\n"
            fi
        fi
    done
fi

# 6. Report
ts=$(date '+%Y-%m-%d %H:%M')
if [ -n "$issues" ]; then
    echo "[$ts] ISSUES: $issues FIXES: $fixes" >> "$LOG"
    if check_cooldown; then
        msg="🚨 <b>n8n-marcin @ anna130</b>\n\n${issues}"
        if [ -n "$fixes" ]; then
            msg="${msg}\n🔧 <b>Auto-fix:</b>\n${fixes}"
        fi
        msg="${msg}\n🕐 ${ts}"
        send_telegram "$msg"
        mark_cooldown
    fi
else
    min=$(date '+%M')
    if [ "$min" -lt 5 ]; then
        echo "[$ts] OK" >> "$LOG"
    fi
    rm -f "$COOLDOWN_FILE"
fi

# Log rotation: keep last 500 lines
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt "$MAX_LOG_LINES" ]; then
    tail -n "$MAX_LOG_LINES" "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
fi
