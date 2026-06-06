"""One-off helper: print your Telegram chat id.

Usage:
  1. In Telegram, create a bot with @BotFather and copy its token.
  2. Send any message to your new bot (e.g. "hi").
  3. Run:  TELEGRAM_BOT_TOKEN=xxxx python -m agent.get_chat_id
     (PowerShell:  $env:TELEGRAM_BOT_TOKEN="xxxx"; python -m agent.get_chat_id)
  4. Copy the printed chat id into the TELEGRAM_CHAT_ID secret.
"""

import os
import sys
import requests


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Set TELEGRAM_BOT_TOKEN first.")
        return 1
    r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
    r.raise_for_status()
    updates = r.json().get("result", [])
    if not updates:
        print("No updates. Send a message to your bot first, then re-run.")
        return 1
    seen = {}
    for u in updates:
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat") or {}
        if "id" in chat:
            seen[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("first_name") or ""
    for cid, who in seen.items():
        print(f"chat_id = {cid}   ({who})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
