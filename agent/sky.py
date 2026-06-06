"""Astronomical visibility computation using Skyfield.

For each of the next N nights we:
  * find the astronomical-dark window (Sun below DARK_SUN_ALT),
  * compute the maximum altitude each catalogue target reaches in that window,
  * do the same for the Moon and the major planets,
  * report the Moon's illumination (matters for faint deep-sky objects).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

import numpy as np
from skyfield.api import Loader, Star, wgs84
from skyfield import almanac

from . import config
from .catalog import CATALOG

# Planets to consider, mapped to their ephemeris key in de421.
_PLANETS = [
    ("Moon", "moon"),
    ("Mercury", "mercury"),
    ("Venus", "venus"),
    ("Mars", "mars"),
    ("Jupiter", "jupiter barycenter"),
    ("Saturn", "saturn barycenter"),
    ("Uranus", "uranus barycenter"),
    ("Neptune", "neptune barycenter"),
]


@dataclass
class Target:
    id: str
    name: str
    kind: str            # planet | moon | nebula | cluster | galaxy | globular | planetary | double
    difficulty: str      # easy | moderate | challenge
    what: str
    max_alt: float       # degrees
    best_time: dt.datetime  # local, tz-aware
    mag: float | None = None


@dataclass
class Night:
    date: dt.date                 # the evening's calendar date (local)
    dark_start: dt.datetime | None = None
    dark_end: dt.datetime | None = None
    moon_illum: float = 0.0       # 0..1 fraction illuminated at local midnight
    moon_up: bool = False
    targets: list[Target] = field(default_factory=list)


class Sky:
    def __init__(self) -> None:
        config.EPHEMERIS_DIR.mkdir(parents=True, exist_ok=True)
        load = Loader(str(config.EPHEMERIS_DIR))
        self.ts = load.timescale()
        self.eph = load(config.EPHEMERIS_FILE)
        self.tz = ZoneInfo(config.TIMEZONE)
        self.site = wgs84.latlon(config.LAT, config.LON, elevation_m=config.ELEVATION_M)
        self.observer = self.eph["earth"] + self.site
        self.sun = self.eph["sun"]

    # -- helpers --------------------------------------------------------------
    def _grid(self, date: dt.date, step_min: int = 10) -> list[dt.datetime]:
        """Tz-aware datetimes from local noon of `date` to local noon next day."""
        start = dt.datetime(date.year, date.month, date.day, 12, 0, tzinfo=self.tz)
        n = (24 * 60) // step_min
        return [start + dt.timedelta(minutes=step_min * i) for i in range(n + 1)]

    def _altitudes(self, times, target) -> np.ndarray:
        alt, _, _ = self.observer.at(times).observe(target).apparent().altaz()
        return np.atleast_1d(alt.degrees)

    # -- public ---------------------------------------------------------------
    def compute_night(self, date: dt.date) -> Night:
        night = Night(date=date)
        grid = self._grid(date)
        times = self.ts.from_datetimes(grid)

        sun_alt = self._altitudes(times, self.sun)
        dark_mask = sun_alt < config.DARK_SUN_ALT
        if not dark_mask.any():
            return night  # no astronomical darkness (won't happen at Bevagna)

        dark_idx = np.where(dark_mask)[0]
        dark_dts = [grid[i] for i in dark_idx]
        night.dark_start = dark_dts[0]
        night.dark_end = dark_dts[-1]
        t_dark = self.ts.from_datetimes(dark_dts)

        # Moon illumination at local midnight (representative for the night).
        midnight = dt.datetime(date.year, date.month, date.day, 23, 59, tzinfo=self.tz) + dt.timedelta(minutes=1)
        t_mid = self.ts.from_datetimes([midnight])
        night.moon_illum = float(almanac.fraction_illuminated(self.eph, "moon", t_mid)[0])

        bright_moon = False  # set after we know if the Moon is up & bright

        # --- Planets & Moon ---
        for label, key in _PLANETS:
            tgt = self.eph[key]
            alt = self._altitudes(t_dark, tgt)
            i = int(np.argmax(alt))
            max_alt = float(alt[i])
            if label == "Moon":
                night.moon_up = max_alt > 0
            if max_alt < config.MIN_ALT_PLANET:
                continue
            mag = self._planet_mag(t_dark[i], tgt) if label != "Moon" else None
            night.targets.append(Target(
                id=label.lower(), name=label,
                kind="moon" if label == "Moon" else "planet",
                difficulty="easy", what=_planet_blurb(label),
                max_alt=max_alt, best_time=dark_dts[i], mag=mag,
            ))

        bright_moon = night.moon_up and night.moon_illum >= 0.6

        # --- Deep-sky & doubles ---
        for obj in CATALOG:
            mag_limit = config.STAR_MAG_LIMIT if obj["kind"] == "double" else config.DSO_MAG_LIMIT
            if obj["mag"] > mag_limit:
                continue
            if bright_moon and obj["difficulty"] == "challenge" and obj["kind"] != "double":
                continue  # faint fuzzies are washed out under a bright Moon
            star = Star(ra_hours=obj["ra_deg"] / 15.0, dec_degrees=obj["dec_deg"])
            alt = self._altitudes(t_dark, star)
            i = int(np.argmax(alt))
            max_alt = float(alt[i])
            if max_alt < config.MIN_ALT_DSO:
                continue
            night.targets.append(Target(
                id=obj["id"], name=obj["name"], kind=obj["kind"],
                difficulty=obj["difficulty"], what=obj["what"],
                max_alt=max_alt, best_time=dark_dts[i], mag=obj["mag"],
            ))

        return night

    def _planet_mag(self, t, target) -> float | None:
        try:
            from skyfield.magnitudelib import planetary_magnitude
            astrometric = self.observer.at(t).observe(target)
            return round(float(planetary_magnitude(astrometric)), 1)
        except Exception:
            return None


def _planet_blurb(label: str) -> str:
    return {
        "Moon": "craters and terminator detail",
        "Mercury": "elusive inner planet, low in twilight",
        "Venus": "brilliant; shows phases",
        "Mars": "ruddy disk, best near opposition",
        "Jupiter": "cloud belts and four Galilean moons",
        "Saturn": "the rings",
        "Uranus": "tiny greenish disk (challenge)",
        "Neptune": "faint bluish point (challenge)",
    }.get(label, "")
