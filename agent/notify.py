"""Telegram delivery."""

from __future__ import annotations

import requests

from . import config


def send(text: str) -> bool:
    """Send an HTML message to the configured chat. Returns True on success."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[notify] Telegram not configured; message below:\n")
        print(text)
        return False
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }, timeout=30)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[notify] Telegram send failed: {e}")
        return False
