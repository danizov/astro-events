"""Central configuration. Most values can be overridden with environment
variables so you can tweak behaviour from the GitHub Actions workflow without
editing code."""

import os

def _f(name: str, default: float) -> float:
    v = os.environ.get(name)
    return float(v) if v not in (None, "") else default

def _i(name: str, default: int) -> int:
    v = os.environ.get(name)
    return int(v) if v not in (None, "") else default

# --- Observer location -------------------------------------------------------
# Plus code WJR5+6QF Bevagna, Provincia di Perugia, Italy.
# Decoded to ~town level (lat/lon to arc-minute is more than enough — which
# objects are above the horizon does not change over a few hundred metres).
LAT = _f("ASTRO_LAT", 42.9325)          # degrees North
LON = _f("ASTRO_LON", 12.6106)          # degrees East
ELEVATION_M = _f("ASTRO_ELEVATION_M", 210.0)
TIMEZONE = os.environ.get("ASTRO_TIMEZONE", "Europe/Rome")  # handles CET/CEST automatically

# --- Telescope: Celestron Inspire 80AZ (80 mm f/11.25 refractor) -------------
TELESCOPE_NAME = os.environ.get("ASTRO_TELESCOPE", "Celestron Inspire 80AZ (80mm f/11 refractor)")
# Realistic visual reach for an 80 mm refractor under a decent suburban sky.
DSO_MAG_LIMIT = _f("ASTRO_DSO_MAG_LIMIT", 9.5)        # deep-sky objects worth a look
STAR_MAG_LIMIT = _f("ASTRO_STAR_MAG_LIMIT", 6.5)      # double stars / asterisms

# --- Visibility thresholds ---------------------------------------------------
MIN_ALT_DSO = _f("ASTRO_MIN_ALT_DSO", 25.0)           # min culmination altitude for DSOs (deg)
MIN_ALT_PLANET = _f("ASTRO_MIN_ALT_PLANET", 12.0)     # planets are bright; allow lower
DARK_SUN_ALT = _f("ASTRO_DARK_SUN_ALT", -18.0)        # astronomical night (deg)

# --- Weather (Open-Meteo) ----------------------------------------------------
# Mean cloud cover over the dark window, in percent.
CLOUD_CLEAR_PCT = _f("ASTRO_CLOUD_CLEAR_PCT", 30.0)   # <= this => "clear" => notify
CLOUD_PARTLY_PCT = _f("ASTRO_CLOUD_PARTLY_PCT", 60.0) # <= this => "partly cloudy" (context only)

# --- Countdown / scheduling --------------------------------------------------
# Each morning we look at tonight (index 0) plus the next 3 nights (index 1..3).
# A target good on night N is therefore announced on the mornings of N-3, N-2,
# N-1 and N itself -> a 4-step "in 3 nights / in 2 nights / tomorrow / tonight"
# countdown, exactly as requested.
LOOKAHEAD_NIGHTS = _i("ASTRO_LOOKAHEAD_NIGHTS", 4)
RUN_HOUR_LOCAL = _i("ASTRO_RUN_HOUR_LOCAL", 7)        # only act at 07:xx local (see main.py guard)
MAX_HIGHLIGHTS_PER_NIGHT = _i("ASTRO_MAX_HIGHLIGHTS", 7)

# --- Output ------------------------------------------------------------------
# Output language. Accepts an ISO code (en, it, es, fr, de, pt, ...) or a plain
# language name ("Swedish", "Português", "日本語"). Anything not in the table
# below is passed to the LLM verbatim, so any language the model speaks works.
LANG = os.environ.get("ASTRO_LANG", "en")

_LANG_NAMES = {
    "en": "English", "it": "Italian", "es": "Spanish", "fr": "French",
    "de": "German", "pt": "Portuguese", "nl": "Dutch", "ca": "Catalan",
    "ru": "Russian", "pl": "Polish", "ja": "Japanese", "zh": "Chinese",
    "el": "Greek", "sv": "Swedish", "ro": "Romanian", "tr": "Turkish",
}

def language_name() -> str:
    """Resolve LANG to a language name the LLM can write in."""
    key = LANG.strip().lower()
    return _LANG_NAMES.get(key, LANG.strip() or "English")

# --- LLM ---------------------------------------------------------------------
# Per Anthropic guidance, default to the most capable model. Override with
# ASTRO_MODEL (e.g. claude-haiku-4-5) if you want to trim cost.
#MODEL = os.environ.get("ASTRO_MODEL", "claude-opus-4-8")
MODEL = os.environ.get("ASTRO_MODEL", "claude-haiku-4-5")

# --- Secrets (read from environment / GitHub Actions secrets) ----------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- Paths -------------------------------------------------------------------
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent
STATE_PATH = ROOT / "state" / "seen.json"
EPHEMERIS_DIR = ROOT / ".skyfield-data"
EPHEMERIS_FILE = "de421.bsp"  # 1900-2050, Sun/Moon/planets; ~17 MB
