"""Telegram delivery.

Sends the message with HTML formatting. If Telegram rejects the HTML (its
parser is strict — an unescaped & / < / > or a tag outside its allowed set
returns 400 "can't parse entities"), we automatically retry as plain text so a
formatting hiccup never costs you the notification. Telegram's actual error
`description` is always logged.
"""

from __future__ import annotations

import html as _html
import re

import requests

from . import config

_MAX_LEN = 4096  # Telegram hard limit per message


def _describe(resp: requests.Response) -> str:
    try:
        return resp.json().get("description", resp.text)
    except ValueError:
        return resp.text


def _strip_html(text: str) -> str:
    """Reduce Telegram-HTML to plain text: keep link text, drop tags, unescape."""
    text = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return _html.unescape(text)


def _post(text: str, parse_mode: str | None) -> requests.Response:
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text[:_MAX_LEN],
        "disable_web_page_preview": False,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return requests.post(url, json=payload, timeout=30)


def send(text: str) -> bool:
    """Send to the configured chat. Returns True on success."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[notify] Telegram not configured; message below:\n")
        print(text)
        return False

    # 1) Try HTML.
    try:
        resp = _post(text, "HTML")
        if resp.ok:
            return True
        desc = _describe(resp)
        print(f"[notify] HTML send rejected ({resp.status_code}): {desc}")
    except requests.RequestException as e:
        print(f"[notify] HTML send failed: {e}")

    # 2) Fall back to plain text (handles 'can't parse entities').
    try:
        resp = _post(_strip_html(text), None)
        if resp.ok:
            print("[notify] Sent as plain text after HTML was rejected.")
            return True
        print(f"[notify] Plain-text send failed ({resp.status_code}): {_describe(resp)}")
    except requests.RequestException as e:
        print(f"[notify] Plain-text send failed: {e}")

    return False
