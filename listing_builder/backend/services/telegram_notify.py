# backend/services/telegram_notify.py
# Purpose: Send business-critical alerts to Shawn's Telegram
# NOT for: User-facing notifications or chat features

import httpx
import structlog
from config import settings

logger = structlog.get_logger()

BOT_TOKEN = getattr(settings, "telegram_bot_token", "")
CHAT_ID = getattr(settings, "telegram_chat_id", "7002371113")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _escape_md(text: str) -> str:
    """Escape Markdown special chars in user-provided strings (emails, names)."""
    for ch in ("_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"):
        text = text.replace(ch, f"\\{ch}")
    return text


async def send_telegram(message: str) -> bool:
    """Fire-and-forget Telegram alert. Never raises — logs errors only."""
    if not BOT_TOKEN:
        logger.debug("telegram_skip_no_token")
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{BASE_URL}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": message,
                    "parse_mode": "Markdown",
                },
            )
            if r.status_code == 200:
                return True
            logger.warning("telegram_send_failed", status=r.status_code)
    except Exception as e:
        logger.warning("telegram_send_error", error=str(e))
    return False


async def notify_payment(email: str, plan_type: str):
    """New payment received — someone subscribed."""
    await send_telegram(
        f"💰 *Nowa płatność LBP!*\n"
        f"Email: `{email}`\n"
        f"Plan: {plan_type}\n"
        f"Kwota: 19,99 PLN/mies"
    )


async def notify_cancellation(email: str):
    """Subscription cancelled — customer leaving."""
    await send_telegram(
        f"⚠️ *Anulowana subskrypcja LBP*\n"
        f"Email: `{email}`"
    )


async def notify_signup(email: str):
    """New user registered (first API call)."""
    await send_telegram(
        f"👤 *Nowy użytkownik LBP*\n"
        f"Email: `{email}`"
    )


def send_telegram_sync(message: str) -> bool:
    """Sync version for calling from non-async contexts (e.g. Stripe webhooks).
    WHY: Runs in a thread to avoid blocking FastAPI's event loop."""
    if not BOT_TOKEN:
        return False
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(
                f"{BASE_URL}/sendMessage",
                json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"},
            )
            return r.status_code == 200
    except Exception as e:
        logger.warning("telegram_send_error", error=str(e))
        return False
