"""Shared HTTP session with automatic retries.

Free public endpoints (Open-Meteo, Tavily) occasionally drop a connection
mid-handshake or return a transient 5xx. A single bare request then crashes the
whole run. This session retries connection errors (including TLS EOF), read
errors and retryable status codes with exponential backoff, so a momentary blip
self-heals instead of failing the job.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def make_session(retries: int = 4, backoff: float = 1.0) -> requests.Session:
    retry = Retry(
        total=retries,
        connect=retries,   # retries TLS/connection failures like SSLEOFError
        read=retries,
        status=retries,
        backoff_factor=backoff,            # waits 0s, 2s, 4s, 8s between tries
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = make_session()


def get(url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", 30)
    return SESSION.get(url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", 30)
    return SESSION.post(url, **kwargs)
