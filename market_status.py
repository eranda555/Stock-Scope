"""CSE (Colombo Stock Exchange) market status — trading hours detection.

Sri Lanka Standard Time (SLST) is UTC+5:30.
CSE official trading hours (confirmed):
  - Pre-open session:  9:00 AM –  9:30 AM SLST
  - Regular trading:   9:30 AM –  2:30 PM SLST
  - Post-close:        2:30 PM onwards
  - Weekends:          Saturday & Sunday CLOSED
  - Market holidays:    Fixed-date holidays defined below.

This module has zero external dependencies beyond the Python standard library.
"""

from __future__ import annotations

import datetime
from typing import Any
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SLST = ZoneInfo("Asia/Colombo")  # UTC+5:30, no DST

# ── Single source of truth for trading hours ──────────────────────────────
TRADING_HOURS_CONFIG: dict[str, Any] = {
    "pre_open_start": datetime.time(9, 0, 0),    # 9:00 AM
    "pre_open_end": datetime.time(9, 30, 0),      # 9:30 AM
    "open_start": datetime.time(9, 30, 0),         # 9:30 AM
    "close_time": datetime.time(14, 30, 0),        # 2:30 PM
    "weekdays": (0, 1, 2, 3, 4),                  # Monday=0 … Friday=4
    "timezone_name": "Asia/Colombo",
}

# ── Fixed-date market holidays ────────────────────────────────────────────
# Poya days (lunar) are not included because they vary year-to-year and
# require a lunar calendar library.  The application handles missing Poya
# data gracefully by never falsely displaying MARKET OPEN on those days;
# instead the holiday data-source failure returns STATUS UNKNOWN.
#
# Known fixed-date CSE holidays (month, day):
HOLIDAYS: set[tuple[int, int]] = {
    (1, 1),    # New Year
    (4, 13),   # Sinhala & Tamil New Year
    (4, 14),   # Sinhala & Tamil New Year
    (12, 25),  # Christmas
}

# ---------------------------------------------------------------------------
# Session constants
# ---------------------------------------------------------------------------

SESSION_PRE_OPEN = "PRE_OPEN"
SESSION_OPEN = "OPEN"
SESSION_CLOSED = "CLOSED"
SESSION_WEEKEND = "WEEKEND"
SESSION_MARKET_HOLIDAY = "MARKET_HOLIDAY"
SESSION_UNKNOWN = "UNKNOWN"

# ---------------------------------------------------------------------------
# Core session detection (single source of truth)
# ---------------------------------------------------------------------------


def get_slst_now() -> datetime.datetime:
    """Return the current datetime in SLST (Asia/Colombo)."""
    return datetime.datetime.now(SLST)


def is_market_holiday(dt: datetime.date) -> bool:
    """Return True if *dt* is a known fixed-date CSE market holiday.

    Note: Poya days (lunar) are not computed here.  The caller is expected
    to handle *UNKNOWN* gracefully when holiday data cannot be determined.
    """
    return (dt.month, dt.day) in HOLIDAYS


def get_market_session(
    now: datetime.datetime | None = None,
) -> str:
    """Determine the current CSE market session.

    Returns one of:
      - ``PRE_OPEN``      — pre-open session (9:00–9:30 AM weekdays, not holiday)
      - ``OPEN``           — regular trading (9:30 AM–2:30 PM weekdays, not holiday)
      - ``CLOSED``         — outside trading hours on a weekday
      - ``WEEKEND``        — Saturday or Sunday
      - ``MARKET_HOLIDAY`` — known fixed-date holiday
      - ``UNKNOWN``        — could not determine (holiday data failure etc.)

    Parameters
    ----------
    now : datetime.datetime, optional
        Reference time (defaults to ``get_slst_now()``).
    """
    if now is None:
        now = get_slst_now()
    else:
        now = _ensure_slst(now)

    # ── Weekend check ──────────────────────────────────────────────────
    if now.weekday() not in TRADING_HOURS_CONFIG["weekdays"]:
        return SESSION_WEEKEND

    # ── Market holiday check ───────────────────────────────────────────
    try:
        if is_market_holiday(now.date()):
            return SESSION_MARKET_HOLIDAY
    except Exception:
        # If holiday data source fails, return UNKNOWN rather than falsely
        # reporting MARKET OPEN.
        return SESSION_UNKNOWN

    market_time = now.time()
    pre_open_start = TRADING_HOURS_CONFIG["pre_open_start"]
    pre_open_end = TRADING_HOURS_CONFIG["pre_open_end"]
    open_start = TRADING_HOURS_CONFIG["open_start"]
    close_time = TRADING_HOURS_CONFIG["close_time"]

    if pre_open_start <= market_time < pre_open_end:
        return SESSION_PRE_OPEN
    elif open_start <= market_time < close_time:
        return SESSION_OPEN
    else:
        return SESSION_CLOSED


# ---------------------------------------------------------------------------
# Public API (kept for backward compatibility — delegate to core functions)
# ---------------------------------------------------------------------------


def is_cse_market_open(now: datetime.datetime | None = None) -> bool:
    """Return ``True`` if the CSE market is currently open for trading.

    Parameters
    ----------
    now : datetime.datetime, optional
        The reference time (defaults to ``get_slst_now()``).
    """
    return get_market_session(now) == SESSION_OPEN


def get_cse_market_status(now: datetime.datetime | None = None) -> dict:
    """Return a detailed dict with CSE market status information.

    Parameters
    ----------
    now : datetime.datetime, optional
        Reference time (defaults to now SLST).

    Returns
    -------
    dict with keys:
        - ``is_open`` (bool)
        - ``next_open`` (str — ISO datetime of next market open, or "N/A")
        - ``next_close`` (str — ISO datetime of next market close, or "N/A")
        - ``current_time_sl`` (str — current time formatted as ``YYYY-MM-DD HH:MM:SS SLST``)
        - ``trading_day_remaining`` (str — readable remaining time, or "N/A")
        - ``data_status`` (str — ``"Live"`` if open, ``"Delayed"`` if closed today, ``"Last Close"`` if weekend)
        - ``session`` (str — one of the SESSION_* constants)
        - ``session_label`` (str — human-readable label)
        - ``next_transition`` (str — countdown to next status change)
    """
    if now is None:
        now = get_slst_now()
    else:
        now = _ensure_slst(now)

    session = get_market_session(now)
    is_open = session == SESSION_OPEN
    current_time_sl = now.strftime("%Y-%m-%d %H:%M:%S") + " SLST"

    today_date = now.date()
    today_open = datetime.datetime.combine(today_date, TRADING_HOURS_CONFIG["open_start"], tzinfo=SLST)
    today_close = datetime.datetime.combine(today_date, TRADING_HOURS_CONFIG["close_time"], tzinfo=SLST)

    next_open_dt = get_next_market_open(now)
    next_close_dt = get_next_market_close(now)

    if is_open:
        remaining = today_close - now
        trading_day_remaining = _format_timedelta(remaining)
        data_status = "Live"
        next_open = "N/A (market is open)"
        next_close = today_close.isoformat()
    else:
        trading_day_remaining = "N/A"
        data_status = _compute_data_status(now, session)
        next_open = next_open_dt.isoformat() if next_open_dt else "N/A"
        next_close = next_close_dt.isoformat() if next_close_dt else "N/A"

    return {
        "is_open": is_open,
        "next_open": next_open,
        "next_close": next_close,
        "current_time_sl": current_time_sl,
        "trading_day_remaining": trading_day_remaining,
        "data_status": data_status,
        "session": session,
        "session_label": get_market_status_label(session),
        "next_transition": get_time_until_status_change(now),
    }


def get_refresh_interval_seconds(now: datetime.datetime | None = None) -> int:
    """Return a sensible auto-refresh interval based on market session.

    - OPEN:       120 seconds  (2 min)
    - PRE_OPEN:   300 seconds  (5 min)
    - Other:      900 seconds  (15 min)
    """
    session = get_market_session(now)
    return _refresh_interval_for_session(session)


# ---------------------------------------------------------------------------
# New public API
# ---------------------------------------------------------------------------


def get_market_status_label(session: str) -> str:
    """Return a human-readable label for a session constant."""
    labels = {
        SESSION_PRE_OPEN: "Pre-Open Session",
        SESSION_OPEN: "Open",
        SESSION_CLOSED: "Closed",
        SESSION_WEEKEND: "Weekend",
        SESSION_MARKET_HOLIDAY: "Market Holiday",
        SESSION_UNKNOWN: "Unknown",
    }
    return labels.get(session, "Unknown")


def format_slst_time(dt: datetime.datetime) -> str:
    """Format a datetime as a human-readable SLST time string.

    Examples: ``"11:25 AM SLST"``, ``"2:30 PM SLST"``
    """
    slst_dt = _ensure_slst(dt)
    return slst_dt.strftime("%I:%M %p").lstrip("0") + " SLST"


def format_slst_date(dt: datetime.datetime) -> str:
    """Format a datetime as a short date + time string.

    Examples: ``"Tue 9:30 AM SLST"``, ``"Mon 2:30 PM SLST"``
    """
    slst_dt = _ensure_slst(dt)
    day_abbr = slst_dt.strftime("%a")
    time_str = slst_dt.strftime("%I:%M %p").lstrip("0")
    return f"{day_abbr} {time_str} SLST"


def get_next_market_open(
    from_dt: datetime.datetime | None = None,
) -> datetime.datetime | None:
    """Return the datetime of the next market open in SLST.

    Returns None only if no valid open can be determined (should not happen
    under normal circumstances).
    """
    if from_dt is None:
        from_dt = get_slst_now()
    else:
        from_dt = _ensure_slst(from_dt)

    session = get_market_session(from_dt)
    today_open = datetime.datetime.combine(
        from_dt.date(), TRADING_HOURS_CONFIG["open_start"], tzinfo=SLST
    )

    # If before pre-open on a trading day → opens today
    if session in (SESSION_CLOSED, SESSION_PRE_OPEN) and from_dt.time() < TRADING_HOURS_CONFIG["open_start"]:
        # If currently in pre-open, the open is today_open
        # If currently closed before pre-open, the open is today_open
        if session == SESSION_PRE_OPEN or from_dt.time() < TRADING_HOURS_CONFIG["pre_open_start"]:
            return today_open

    # If during open → next open is tomorrow
    if session == SESSION_OPEN:
        candidate = from_dt + datetime.timedelta(days=1)
        return _next_valid_open(candidate)

    # After close today, weekend, or holiday → find next trading day
    candidate = from_dt + datetime.timedelta(days=1)
    # If in pre-open and we got here (shouldn't), but just in case:
    return _next_valid_open(candidate)


def _next_valid_open(candidate: datetime.datetime) -> datetime.datetime | None:
    """Walk forward day-by-day to find the next valid market open."""
    for _ in range(365):  # safety limit — should never iterate this far
        if candidate.weekday() in TRADING_HOURS_CONFIG["weekdays"]:
            try:
                if not is_market_holiday(candidate.date()):
                    return candidate.replace(
                        hour=TRADING_HOURS_CONFIG["open_start"].hour,
                        minute=TRADING_HOURS_CONFIG["open_start"].minute,
                        second=0, microsecond=0,
                    )
            except Exception:
                # If holiday detection fails, assume it's a trading day
                return candidate.replace(
                    hour=TRADING_HOURS_CONFIG["open_start"].hour,
                    minute=TRADING_HOURS_CONFIG["open_start"].minute,
                    second=0, microsecond=0,
                )
        candidate += datetime.timedelta(days=1)
    return None  # pragma: no cover (should never happen)


def get_next_market_close(
    from_dt: datetime.datetime | None = None,
) -> datetime.datetime | None:
    """Return the datetime of the next market close in SLST."""
    if from_dt is None:
        from_dt = get_slst_now()
    else:
        from_dt = _ensure_slst(from_dt)

    session = get_market_session(from_dt)
    today_close = datetime.datetime.combine(
        from_dt.date(), TRADING_HOURS_CONFIG["close_time"], tzinfo=SLST
    )

    if session == SESSION_OPEN:
        return today_close

    # Market not open — find the next trading day's close
    next_open = get_next_market_open(from_dt)
    if next_open is None:
        return None
    return next_open.replace(
        hour=TRADING_HOURS_CONFIG["close_time"].hour,
        minute=TRADING_HOURS_CONFIG["close_time"].minute,
        second=0, microsecond=0,
    )


def get_time_until_status_change(
    from_dt: datetime.datetime | None = None,
) -> str:
    """Return a human-readable countdown to the next market status change.

    Examples:
      - ``"Closes in 02:14:36"``
      - ``"Opens in 13h 30m"``
      - ``"Opens in 15m"``
      - ``"Market is open"``  (if already open — fallback)
    """
    if from_dt is None:
        from_dt = get_slst_now()
    else:
        from_dt = _ensure_slst(from_dt)

    session = get_market_session(from_dt)

    if session == SESSION_OPEN:
        # Countdown to today's close
        today_close = datetime.datetime.combine(
            from_dt.date(), TRADING_HOURS_CONFIG["close_time"], tzinfo=SLST
        )
        remaining = today_close - from_dt
        total_secs = int(remaining.total_seconds())
        if total_secs <= 0:
            return "Closes now"
        hours, remainder = divmod(total_secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"Closes in {hours:02d}:{minutes:02d}:{seconds:02d}"

    elif session == SESSION_PRE_OPEN:
        # Countdown to market open
        today_open = datetime.datetime.combine(
            from_dt.date(), TRADING_HOURS_CONFIG["open_start"], tzinfo=SLST
        )
        remaining = today_open - from_dt
        total_secs = int(remaining.total_seconds())
        if total_secs <= 0:
            return "Opening now"
        minutes, seconds = divmod(total_secs, 60)
        if minutes >= 60:
            hours, minutes = divmod(minutes, 60)
            return f"Opens in {hours}h {minutes}m"
        return f"Opens in {minutes}m"

    else:
        # Countdown to next market open
        next_open = get_next_market_open(from_dt)
        if next_open is None:
            return "Unknown"
        remaining = next_open - from_dt
        total_secs = int(remaining.total_seconds())
        if total_secs <= 0:
            return "Opening now"

        total_minutes = total_secs // 60
        if total_minutes >= 60:
            hours, minutes = divmod(total_minutes, 60)
            days = hours // 24
            hours = hours % 24
            if days > 0:
                return f"Opens in {days}d {hours}h {minutes}m"
            return f"Opens in {hours}h {minutes}m"
        return f"Opens in {total_minutes}m"


# ---------------------------------------------------------------------------
# Data freshness
# ---------------------------------------------------------------------------


def get_data_freshness_status(data_dict: dict) -> dict:
    """Evaluate data freshness based on market session and data age.

    Parameters
    ----------
    data_dict : dict
        Market data dict (as produced by ``CseMarketDataManager``).

    Returns
    -------
    dict with keys:
        - ``label`` (str) — one of LIVE, DELAYED, STALE, LATEST AVAILABLE, CACHED, UNKNOWN
        - ``source_timestamp`` (str) — formatted source timestamp
        - ``fetched_time`` (str) — formatted fetch time
        - ``age_seconds`` (int) — age in seconds (or -1 if unknown)
        - ``color`` (str) — CSS color name: green, amber, red, grey
    """
    from datetime import datetime, timezone

    session = get_market_session()
    last_updated = data_dict.get("last_updated")
    source_available = data_dict.get("source_available", False)
    fetch_error = data_dict.get("fetch_error")

    # Determine fetched time from session state
    import streamlit as st
    from market_data_manager import _SESSION_KEY

    state = st.session_state.get(_SESSION_KEY, {})
    fetched_dt = state.get("last_fetch_time")  # UTC datetime or None

    age_seconds = -1
    if fetched_dt is not None and isinstance(fetched_dt, datetime):
        age_seconds = int((datetime.now(timezone.utc) - fetched_dt).total_seconds())

    fetched_formatted = ""
    if fetched_dt is not None and isinstance(fetched_dt, datetime):
        slst_dt = fetched_dt.astimezone(SLST)
        fetched_formatted = format_slst_time(slst_dt)

    source_formatted = last_updated if last_updated else "Never"

    # ── Determine freshness label ──────────────────────────────────────
    if not source_available or fetch_error:
        return {
            "label": "UNKNOWN",
            "source_timestamp": source_formatted,
            "fetched_time": fetched_formatted,
            "age_seconds": age_seconds,
            "color": "grey",
        }

    if session == SESSION_OPEN:
        if age_seconds >= 0:
            if age_seconds < 120:
                return {
                    "label": "LIVE",
                    "source_timestamp": source_formatted,
                    "fetched_time": fetched_formatted,
                    "age_seconds": age_seconds,
                    "color": "green",
                }
            elif age_seconds < 300:
                return {
                    "label": "DELAYED",
                    "source_timestamp": source_formatted,
                    "fetched_time": fetched_formatted,
                    "age_seconds": age_seconds,
                    "color": "amber",
                }
            else:
                return {
                    "label": "STALE",
                    "source_timestamp": source_formatted,
                    "fetched_time": fetched_formatted,
                    "age_seconds": age_seconds,
                    "color": "red",
                }
    elif session in (SESSION_CLOSED, SESSION_PRE_OPEN):
        # During closed hours, data from today is "Latest Available"
        return {
            "label": "LATEST AVAILABLE",
            "source_timestamp": source_formatted,
            "fetched_time": fetched_formatted,
            "age_seconds": age_seconds,
            "color": "blue",
        }
    elif session in (SESSION_WEEKEND, SESSION_MARKET_HOLIDAY):
        return {
            "label": "CACHED",
            "source_timestamp": source_formatted,
            "fetched_time": fetched_formatted,
            "age_seconds": age_seconds,
            "color": "grey",
        }
    else:
        return {
            "label": "UNKNOWN",
            "source_timestamp": source_formatted,
            "fetched_time": fetched_formatted,
            "age_seconds": age_seconds,
            "color": "grey",
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_slst(dt: datetime.datetime) -> datetime.datetime:
    """Ensure *dt* is timezone-aware and converted to SLST."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=SLST)
    return dt.astimezone(SLST)


def _compute_data_status(
    now: datetime.datetime, session: str
) -> str:
    """Compute a backward-compatible data_status string for a closed market."""
    if session == SESSION_WEEKEND:
        return "Last Close"
    if session == SESSION_MARKET_HOLIDAY:
        return "Market Holiday"
    if session == SESSION_PRE_OPEN:
        return "Pre-Open"
    return "Delayed"


def _refresh_interval_for_session(session: str) -> int:
    """Return refresh interval seconds for a given market session."""
    intervals = {
        SESSION_OPEN: 120,
        SESSION_PRE_OPEN: 300,
        SESSION_CLOSED: 900,
        SESSION_WEEKEND: 900,
        SESSION_MARKET_HOLIDAY: 900,
        SESSION_UNKNOWN: 900,
    }
    return intervals.get(session, 900)


def _next_trading_day_open(after: datetime.datetime) -> datetime.datetime:
    """Return the datetime of the next trading day's open (9:30 AM SLST).

    If *after* is on a trading day but after close, returns the next day.
    If *after* is on a weekend, returns Monday.
    """
    next_open = get_next_market_open(after)
    if next_open is None:
        # Fallback: scan day by day
        candidate = after + datetime.timedelta(days=1)
        while candidate.weekday() not in TRADING_HOURS_CONFIG["weekdays"]:
            candidate += datetime.timedelta(days=1)
        return candidate.replace(hour=9, minute=30, second=0, microsecond=0)
    return next_open


def _format_timedelta(td: datetime.timedelta) -> str:
    """Format a timedelta as ``"Xh Ym Zs"``."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return "0s"
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)
