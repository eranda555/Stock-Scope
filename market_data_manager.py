"""Smart market data manager for CSE live data.

Manages the lifecycle of CSE trade-summary and market-summary data using
Streamlit session state (not ``@st.cache_data``) so that a user-clicked
"Refresh" button actually invalidates the cache immediately.

Graceful degradation:
- On API failure the last-valid dataset is preserved.
- Missing/None values are never replaced with 0 or random data.
- Status indicators tell the user whether data is Live, Delayed, or Last Close.
"""

from __future__ import annotations

import datetime
from typing import Any

import streamlit as st

from cse_data import fetch_live_trade_summary
from market_status import (
    get_cse_market_status,
    get_data_freshness_status,
    get_market_session,
    get_refresh_interval_seconds,
    is_cse_market_open,
)

# ---------------------------------------------------------------------------
# Session-state keys  (exported so get_data_freshness_status can read it)
# ---------------------------------------------------------------------------

_SESSION_KEY = "_cse_market_data"


def _default_data_dict() -> dict:
    return {
        "companies": [],
        "market_summary": {},
        "last_updated": None,  # ISO-formatted string
        "market_status": "Unknown",
        "data_status": "Unknown",
        "source_available": False,
        "fetch_error": None,
    }


def _make_data_dict(
    companies: list[dict],
    market_summary: dict,
    source_available: bool,
    fetch_error: str | None,
) -> dict:
    status_info = get_cse_market_status()
    is_open = status_info["is_open"]
    data_status = status_info["data_status"]

    return {
        "companies": companies,
        "market_summary": market_summary,
        "last_updated": status_info["current_time_sl"],
        "market_status": "Open" if is_open else "Closed",
        "data_status": data_status,
        "source_available": source_available,
        "fetch_error": fetch_error,
        "_market_status_info": status_info,
    }


# ---------------------------------------------------------------------------
# Manager class
# ---------------------------------------------------------------------------


class CseMarketDataManager:
    """Manages CSE live market data with session-state caching.

    Usage in app.py
    ---------------
    .. code-block:: python

        manager = CseMarketDataManager.get_instance()
        data = manager.get_cached_market_data()

        if manager.is_stale():
            with st.spinner("Refreshing market data..."):
                manager.refresh_if_needed()
    """

    @staticmethod
    def get_instance() -> CseMarketDataManager:
        """Return the singleton manager, initialising session state if needed."""
        if _SESSION_KEY not in st.session_state:
            st.session_state[_SESSION_KEY] = {
                "data": _default_data_dict(),
                "last_fetch_time": None,  # datetime.datetime (UTC) or None
            }
        return CseMarketDataManager()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_cached_market_data(self) -> dict:
        """Return the current cached market data dict (never raises)."""
        return st.session_state[_SESSION_KEY]["data"]

    def get_last_fetch_time(self) -> datetime.datetime | None:
        """Return the UTC datetime of the last successful fetch, or None."""
        return st.session_state[_SESSION_KEY]["last_fetch_time"]

    def is_stale(self) -> bool:
        """Check whether the cached data has expired based on market session.

        Refresh intervals by session:
          - OPEN:       120 seconds  (2 min)
          - PRE_OPEN:   300 seconds  (5 min)
          - CLOSED/
            WEEKEND/
            HOLIDAY:    900 seconds  (15 min)

        If no data has ever been fetched, returns True.
        """
        state = st.session_state[_SESSION_KEY]
        last_time = state["last_fetch_time"]
        if last_time is None:
            return True

        interval = get_refresh_interval_seconds()
        elapsed = (datetime.datetime.now(datetime.timezone.utc) - last_time).total_seconds()
        return elapsed > interval

    def refresh_if_needed(self) -> bool:
        """Check staleness and fetch fresh data if required.

        On MARKET HOLIDAY or WEEKEND, does NOT call the CSE API (avoids
        unnecessary requests).  Returns True if data was refreshed, False
        if still fresh or if refresh was skipped due to market status.

        Does NOT raise on API failure — preserves last valid data.
        """
        session = get_market_session()

        # Skip network calls on weekends and holidays
        if session in ("WEEKEND", "MARKET_HOLIDAY", "UNKNOWN"):
            return False

        if not self.is_stale():
            return False

        self._fetch()
        return True

    def force_refresh(self) -> None:
        """Unconditionally fetch fresh data from the CSE API.

        Always performs a network call. Preserves last valid data on failure.
        """
        self._fetch()

    def _fetch(self) -> None:
        """Internal fetch — wraps CSE API with timeout, retry, and graceful fallback."""
        import time

        companies: list[dict] = []
        market_summary: dict = {}
        source_available = False
        fetch_error: str | None = None

        # --- Retry loop (1 retry, 1s backoff) ---
        for attempt in range(2):
            try:
                companies, market_summary = fetch_live_trade_summary()
                source_available = True
                fetch_error = None
                break  # success
            except Exception as exc:
                fetch_error = str(exc)
                if attempt == 0:
                    time.sleep(1.0)  # backoff before retry

        # --- Build data dict ---
        if source_available:
            new_data = _make_data_dict(
                companies=companies,
                market_summary=market_summary,
                source_available=True,
                fetch_error=None,
            )
            st.session_state[_SESSION_KEY]["data"] = new_data
            st.session_state[_SESSION_KEY]["last_fetch_time"] = (
                datetime.datetime.now(datetime.timezone.utc)
            )
        else:
            # API failed — preserve last valid data, update error status
            existing = st.session_state[_SESSION_KEY]["data"]
            existing["source_available"] = False
            existing["fetch_error"] = fetch_error
            # Keep last_updated, market_status, data_status from previous fetch
            st.session_state[_SESSION_KEY]["data"] = existing
            # Do NOT update last_fetch_time — we keep the old timestamp

    # ------------------------------------------------------------------
    # Convenience helpers for the UI layer
    # ------------------------------------------------------------------

    def get_companies(self) -> list[dict]:
        """Return the companies list from cache (empty list if never fetched)."""
        return self.get_cached_market_data().get("companies", [])

    def get_market_summary(self) -> dict:
        """Return the market summary dict from cache (empty dict if never fetched)."""
        return self.get_cached_market_data().get("market_summary", {})

    def get_trading_companies(self) -> list[dict]:
        """Return only trading (status==0) companies."""
        return [
            c for c in self.get_companies()
            if c.get("status") == 0
        ]

    def get_data_display_status(self) -> dict:
        """Return a dict for UI display with keys:

        - ``market_status_label`` — "Open" / "Closed"
        - ``data_status_label`` — "Live" / "Delayed" / "Last Close"
        - ``last_updated`` — formatted timestamp string
        - ``source_available`` — bool
        - ``fetch_error`` — str or None
        - ``is_open`` — bool
        - ``session`` — market session string
        - ``freshness`` — data freshness dict
        """
        data = self.get_cached_market_data()
        freshness = get_data_freshness_status(data)
        return {
            "market_status_label": data.get("market_status", "Unknown"),
            "data_status_label": data.get("data_status", "Unknown"),
            "last_updated": data.get("last_updated", "Never"),
            "source_available": data.get("source_available", False),
            "fetch_error": data.get("fetch_error"),
            "is_open": data.get("_market_status_info", {}).get("is_open", False),
            "session": data.get("_market_status_info", {}).get("session", "UNKNOWN"),
            "freshness": freshness,
        }
