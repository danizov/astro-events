"""Daily entry point.

Run order:
  1. Time guard (only act at 07:xx Europe/Rome unless forced).
  2. Compute the next N nights of visibility + weather.
  3. Decide what to notify using the -3/-2/-1/tonight countdown + dedup state.
  4. Compose (Claude) and send (Telegram). Persist state.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from zoneinfo import ZoneInfo

from . import config, events, judge, notify
from .sky import Sky, Night
from .state import State
from .weather import Weather

# When set (manual runs), re-send even if a target was already notified today,
# i.e. ignore the dedup state. Scheduled runs leave this empty so dedup applies.
_FORCE = os.environ.get("ASTRO_FORCE", "").lower() in ("1", "true", "yes")

_COUNTDOWN = {0: "tonight", 1: "tomorrow night", 2: "in 2 nights", 3: "in 3 nights"}


def _countdown_label(offset: int) -> str:
    return _COUNTDOWN.get(offset, f"in {offset} nights")


def _score(t) -> float:
    """Deterministic 'how interesting' score for ranking highlights."""
    planet_scores = {
        "saturn": 100, "jupiter": 98, "moon": 95, "mars": 92, "venus": 90,
        "mercury": 60, "uranus": 30, "neptune": 28,
    }
    if t.kind in ("planet", "moon"):
        return planet_scores.get(t.id, 50) + t.max_alt * 0.1
    diff_bonus = {"easy": 30, "moderate": 18, "challenge": 6}.get(t.difficulty, 0)
    limit = config.STAR_MAG_LIMIT if t.kind == "double" else config.DSO_MAG_LIMIT
    brightness = max(0.0, (limit - (t.mag or limit))) * 5
    return diff_bonus + brightness + t.max_alt * 0.15


def _select(night: Night) -> list:
    ranked = sorted(night.targets, key=_score, reverse=True)
    return ranked[: config.MAX_HIGHLIGHTS_PER_NIGHT]


def _target_dict(t) -> dict:
    return {
        "name": t.name,
        "what": t.what,
        "kind": t.kind,
        "max_alt": t.max_alt,
        "best_time": t.best_time.strftime("%H:%M"),
        "mag": t.mag,
    }


def run() -> int:
    # Windows consoles default to cp1252 and choke on emoji when dry-running.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    # No wall-clock guard: GitHub's scheduler is best-effort and may start the
    # job late. We just run whenever invoked; the dedup state guarantees a
    # single notification per day even though two crons fire (and gives us
    # redundancy if GitHub delays or drops one of them).
    tz = ZoneInfo(config.TIMEZONE)
    now = dt.datetime.now(tz)
    today = now.date()
    print(f"[main] Running at {now:%Y-%m-%d %H:%M %Z} for {today}"
          f"{' (FORCE: ignoring dedup)' if _FORCE else ''}.")

    sky = Sky()
    weather = Weather()
    weather.load(days=config.LOOKAHEAD_NIGHTS + 2)
    state = State.load()
    state.prune(today)

    payload_nights: list[dict] = []
    alerts: list[str] = []
    notified_any = False

    for offset in range(config.LOOKAHEAD_NIGHTS):
        night_date = today + dt.timedelta(days=offset)
        night = sky.compute_night(night_date)
        if night.dark_start is None or not night.targets:
            continue

        verdict = weather.verdict(night.dark_start, night.dark_end)

        # Weather downgrade alert for a night we previously announced as clear.
        if state.weather_flipped_to_cloudy("__night__", night_date, verdict.label):
            alerts.append(
                f"Heads up: {_countdown_label(offset)} ({night_date:%a %d %b}) is now "
                f"{verdict.label} ({verdict.mean}% cloud) — earlier it looked clear."
            )
        state.set_weather("__night__", night_date, verdict.label)

        if not verdict.is_clear:
            continue  # only notify targets when the sky is actually clear

        highlights = _select(night)
        to_send = []
        for t in highlights:
            if not _FORCE and state.already_notified(t.id, night_date, offset):
                continue
            state.mark_notified(t.id, night_date, offset)
            to_send.append(t)

        if not to_send:
            continue

        notified_any = True
        payload_nights.append({
            "countdown": _countdown_label(offset),
            "date_str": night_date.strftime("%a %d %b %Y"),
            "weather": {"label": verdict.label, "mean": verdict.mean},
            "moon": {"illum_pct": round(night.moon_illum * 100), "up": night.moon_up},
            "highlights": [_target_dict(t) for t in to_send],
        })

    # Ephemeral events (comets / aurora / meteor peaks).
    raw_events = events.fetch_events(today)
    fresh_events = state.new_events(raw_events)
    if fresh_events:
        state.mark_events(fresh_events)

    if not (payload_nights or fresh_events or alerts):
        print("[main] Nothing new to report.")
        state.save()
        return 0

    payload = {
        "location": "Bevagna (PG), Italy",
        "telescope": config.TELESCOPE_NAME,
        "lang": config.LANG,
        "alerts": alerts,
        "nights": payload_nights,
        "events": [{"title": e["title"], "snippet": e["snippet"], "url": e["url"]} for e in fresh_events],
    }

    message = judge.compose(payload)
    ok = notify.send(message)
    print(f"[main] Notification {'sent' if ok else 'NOT sent'}; "
          f"{len(payload_nights)} night(s), {len(fresh_events)} event(s), {len(alerts)} alert(s).")

    # Persist state only after a successful send so a transient failure retries.
    if ok or not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        state.save()
    return 0


if __name__ == "__main__":
    sys.exit(run())
