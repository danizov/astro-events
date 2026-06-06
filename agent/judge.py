"""Turn the deterministic 'what to notify' payload into a nice Telegram message.

Selection of *what* to send is decided deterministically in main.py/state.py.
Here, Claude only writes the prose. If the API key is missing or the call
fails, we fall back to a plain formatter so the agent still notifies.
"""

from __future__ import annotations

import json
import html

from . import config

_SYSTEM = (
    "You are an amateur-astronomy assistant. You write a short, friendly "
    "Telegram message announcing tonight's and upcoming stargazing targets for "
    "a specific observer and telescope. Telegram HTML only: use <b>, <i>, "
    "<a href>, and line breaks. No markdown, no headings, no <ul>. Keep it "
    "scannable and concise. Lead with a one-line summary. If 'alerts' are "
    "present, show them prominently near the top (they warn that a previously "
    "announced clear night now looks cloudy). Group targets by the countdown "
    "label (TONIGHT first). For each target give its name, a few words on what "
    "it is, its peak altitude and best time. Mention the Moon phase if it "
    "matters for faint objects. End with any time-sensitive events. "
    "Do not invent targets or facts beyond the data provided."
)


def compose(payload: dict) -> str:
    if config.ANTHROPIC_API_KEY:
        try:
            return _compose_llm(payload)
        except Exception as e:  # never fail to notify because of the LLM
            print(f"[judge] LLM compose failed ({e}); using fallback formatter.")
    return _compose_fallback(payload)


def _compose_llm(payload: dict) -> str:
    import anthropic

    client = anthropic.Anthropic()
    lang = "Italian" if config.LANG.lower().startswith("it") else "English"
    prompt = (
        f"Write the message in {lang}. Observer location: {payload['location']}. "
        f"Telescope: {payload['telescope']}.\n\n"
        f"Here is the data (JSON). Times are local 24h. Altitude in degrees.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    resp = client.messages.create(
        model=config.MODEL,
        max_tokens=1600,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if not text:
        raise RuntimeError("empty LLM response")
    return text


def _compose_fallback(payload: dict) -> str:
    def esc(s: str) -> str:
        return html.escape(str(s))

    lines = [f"🔭 <b>Stargazing — {esc(payload['location'])}</b>"]
    if payload.get("alerts"):
        lines.append("")
        for a in payload["alerts"]:
            lines.append(f"⚠️ {esc(a)}")
    for night in payload["nights"]:
        w = night["weather"]
        moon = night["moon"]
        lines.append("")
        lines.append(
            f"<b>{esc(night['countdown'].upper())}</b> ({esc(night['date_str'])}) — "
            f"sky {esc(w['label'])} ({w['mean']}% cloud), "
            f"Moon {moon['illum_pct']}%{' up' if moon['up'] else ' down'}"
        )
        for t in night["highlights"]:
            mag = f", mag {t['mag']}" if t.get("mag") is not None else ""
            lines.append(
                f"• <b>{esc(t['name'])}</b> — {esc(t['what'])} "
                f"(up to {round(t['max_alt'])}°, best {esc(t['best_time'])}{mag})"
            )
    if payload.get("events"):
        lines.append("")
        lines.append("<b>Also happening</b>")
        for e in payload["events"]:
            if e.get("url"):
                lines.append(f"• <a href=\"{esc(e['url'])}\">{esc(e['title'])}</a>")
            else:
                lines.append(f"• {esc(e['title'])}")
    return "\n".join(lines)
