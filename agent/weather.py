"""Cloud-cover forecast from Open-Meteo (free, no API key).

We fetch hourly cloud cover for the observer's location and, for a given dark
window, return the mean/min/max cover plus a simple verdict.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import requests

from . import config

_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class CloudVerdict:
    mean: float          # percent
    minimum: float
    maximum: float
    label: str           # "clear" | "partly cloudy" | "cloudy" | "unknown"

    @property
    def is_clear(self) -> bool:
        return self.label == "clear"


class Weather:
    def __init__(self) -> None:
        self.tz = ZoneInfo(config.TIMEZONE)
        self._hourly: dict[dt.datetime, float] = {}
        self._loaded = False

    def load(self, days: int = 5) -> None:
        params = {
            "latitude": config.LAT,
            "longitude": config.LON,
            "hourly": "cloud_cover",
            "timezone": config.TIMEZONE,
            "forecast_days": days,
        }
        r = requests.get(_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()["hourly"]
        for iso, cover in zip(data["time"], data["cloud_cover"]):
            # Open-Meteo returns local naive ISO timestamps when timezone is set.
            ts = dt.datetime.fromisoformat(iso).replace(tzinfo=self.tz)
            self._hourly[ts] = float(cover) if cover is not None else float("nan")
        self._loaded = True

    def verdict(self, start: dt.datetime, end: dt.datetime) -> CloudVerdict:
        if not self._loaded or start is None or end is None:
            return CloudVerdict(0, 0, 0, "unknown")
        covers = [c for t, c in self._hourly.items() if start <= t <= end and c == c]  # c==c drops NaN
        if not covers:
            return CloudVerdict(0, 0, 0, "unknown")
        mean = sum(covers) / len(covers)
        if mean <= config.CLOUD_CLEAR_PCT:
            label = "clear"
        elif mean <= config.CLOUD_PARTLY_PCT:
            label = "partly cloudy"
        else:
            label = "cloudy"
        return CloudVerdict(round(mean), round(min(covers)), round(max(covers)), label)
