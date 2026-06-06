"""Persistent dedup state, committed back to the repo by the workflow.

Shape of seen.json:
{
  "notified": { "<object_id>|<event_date>": [offset, ...] },  # offsets already sent
  "weather":  { "<object_id>|<event_date>": "clear"|"partly cloudy"|... },
  "events":   ["normalised event title", ...]
}
"""

from __future__ import annotations

import datetime as dt
import json

from . import config


def _key(object_id: str, event_date: dt.date) -> str:
    return f"{object_id}|{event_date.isoformat()}"


class State:
    def __init__(self) -> None:
        self.notified: dict[str, list[int]] = {}
        self.weather: dict[str, str] = {}
        self.events: list[str] = []

    @classmethod
    def load(cls) -> "State":
        s = cls()
        if config.STATE_PATH.exists():
            try:
                data = json.loads(config.STATE_PATH.read_text(encoding="utf-8"))
                s.notified = data.get("notified", {})
                s.weather = data.get("weather", {})
                s.events = data.get("events", [])
            except (json.JSONDecodeError, OSError):
                pass
        return s

    def save(self) -> None:
        config.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        config.STATE_PATH.write_text(
            json.dumps(
                {"notified": self.notified, "weather": self.weather, "events": self.events},
                indent=2, sort_keys=True,
            ),
            encoding="utf-8",
        )

    # -- countdown dedup ------------------------------------------------------
    def already_notified(self, object_id: str, event_date: dt.date, offset: int) -> bool:
        return offset in self.notified.get(_key(object_id, event_date), [])

    def mark_notified(self, object_id: str, event_date: dt.date, offset: int) -> None:
        self.notified.setdefault(_key(object_id, event_date), []).append(offset)

    # -- weather change tracking ---------------------------------------------
    def weather_flipped_to_cloudy(self, object_id: str, event_date: dt.date, label: str) -> bool:
        prev = self.weather.get(_key(object_id, event_date))
        return prev == "clear" and label != "clear"

    def set_weather(self, object_id: str, event_date: dt.date, label: str) -> None:
        self.weather[_key(object_id, event_date)] = label

    # -- ephemeral events -----------------------------------------------------
    def new_events(self, events: list[dict]) -> list[dict]:
        seen = set(self.events)
        fresh = [e for e in events if e["title"] and e["title"].lower() not in seen]
        return fresh

    def mark_events(self, events: list[dict]) -> None:
        for e in events:
            if e["title"]:
                self.events.append(e["title"].lower())
        self.events = self.events[-300:]  # keep the list bounded

    # -- housekeeping ---------------------------------------------------------
    def prune(self, today: dt.date) -> None:
        def keep(k: str) -> bool:
            try:
                d = dt.date.fromisoformat(k.split("|", 1)[1])
            except (IndexError, ValueError):
                return True
            return d >= today
        self.notified = {k: v for k, v in self.notified.items() if keep(k)}
        self.weather = {k: v for k, v in self.weather.items() if keep(k)}
