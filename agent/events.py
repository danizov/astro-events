"""Ephemeral 'what's happening in the sky this week' lookup via Tavily.

A static catalogue can't know about a new bright comet, an aurora alert, or a
meteor-shower peak. Tavily surfaces those; we keep it best-effort and never let
a failure block the rest of the run.
"""

from __future__ import annotations

import datetime as dt

from . import config, http

_URL = "https://api.tavily.com/search"


def fetch_events(today: dt.date) -> list[dict]:
    """Return a list of {title, snippet, url} for time-sensitive sky events."""
    if not config.TAVILY_API_KEY:
        return []
    month = today.strftime("%B %Y")
    query = (
        f"notable astronomy events visible from the northern hemisphere in {month}: "
        f"bright comets, meteor shower peaks, aurora forecast, planetary conjunctions"
    )
    try:
        r = http.post(_URL, json={
            "api_key": config.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 6,
            "days": 10,
        }, timeout=30)
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception:
        return []
    out = []
    for res in results:
        out.append({
            "title": (res.get("title") or "").strip(),
            "snippet": (res.get("content") or "").strip()[:300],
            "url": res.get("url") or "",
        })
    return out
