"""Comprehensive tests for CSE market status detection.

Uses mocked datetime to test each market state:
  - PRE_OPEN, OPEN, CLOSED (weekday)
  - WEEKEND (Sat/Sun)
  - MARKET_HOLIDAY (fixed-date holidays)
  - UNKNOWN (holiday data failure edge-case)
  - Year boundary
"""

from __future__ import annotations

import datetime
import unittest
from unittest.mock import patch

from zoneinfo import ZoneInfo

import market_status as ms

SLST = ZoneInfo("Asia/Colombo")


class TestMarketSession(unittest.TestCase):
    """Core session detection tests."""

    # ── Helpers ──────────────────────────────────────────────────────────

    def _make_dt(self, weekday: int, hour: int, minute: int = 0) -> datetime.datetime:
        """Create an SLST datetime for a given weekday and time.

        Uses a Monday=0 … Sunday=6 scheme consistent with Python's weekday().
        Uses a base date of 2026-01-05 (a Monday) and offsets by *weekday* days.
        """
        base = datetime.date(2026, 1, 5)  # Monday
        target_date = base + datetime.timedelta(days=weekday)
        return datetime.datetime(
            target_date.year, target_date.month, target_date.day,
            hour, minute, 0, 0, tzinfo=SLST,
        )

    # ── Tests ────────────────────────────────────────────────────────────

    def test_monday_0830_closed_before_pre_open(self):
        """Monday 8:30 AM → CLOSED (before pre-open)"""
        dt = self._make_dt(0, 8, 30)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_CLOSED)

    def test_monday_0915_pre_open(self):
        """Monday 9:15 AM → PRE_OPEN"""
        dt = self._make_dt(0, 9, 15)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_PRE_OPEN)

    def test_monday_0930_exactly_open(self):
        """Monday 9:30 AM → OPEN (exactly at open)"""
        dt = self._make_dt(0, 9, 30)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_OPEN)

    def test_monday_1100_mid_session(self):
        """Monday 11:00 AM → OPEN (mid-session)"""
        dt = self._make_dt(0, 11, 0)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_OPEN)
        self.assertTrue(ms.is_cse_market_open(dt))

    def test_monday_1430_exactly_close(self):
        """Monday 2:30 PM → CLOSED (exactly at close — market_time < close_time)"""
        dt = self._make_dt(0, 14, 30)
        session = ms.get_market_session(dt)
        # 14:30 = close_time, condition is open_start <= market_time < close_time
        # so 14:30 is NOT < 14:30 → CLOSED
        self.assertEqual(session, ms.SESSION_CLOSED)
        self.assertFalse(ms.is_cse_market_open(dt))

    def test_monday_1500_after_close(self):
        """Monday 3:00 PM → CLOSED (after close)"""
        dt = self._make_dt(0, 15, 0)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_CLOSED)

    def test_friday_1500_closed(self):
        """Friday 3:00 PM → CLOSED"""
        dt = self._make_dt(4, 15, 0)  # Friday
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_CLOSED)

    def test_saturday_1100_weekend(self):
        """Saturday 11:00 AM → WEEKEND"""
        dt = self._make_dt(5, 11, 0)  # Saturday
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_WEEKEND)

    def test_sunday_1100_weekend(self):
        """Sunday 11:00 AM → WEEKEND"""
        dt = self._make_dt(6, 11, 0)  # Sunday
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_WEEKEND)

    def test_monday_0900_after_weekend_pre_open(self):
        """Monday 9:00 AM (after weekend) → PRE_OPEN"""
        dt = self._make_dt(0, 9, 0)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_PRE_OPEN)

    def test_dec_25_market_holiday(self):
        """December 25 → MARKET_HOLIDAY"""
        dt = datetime.datetime(2026, 12, 25, 10, 0, 0, tzinfo=SLST)  # Friday
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_MARKET_HOLIDAY)

    def test_jan_1_market_holiday(self):
        """January 1 → MARKET_HOLIDAY (if configured)"""
        dt = datetime.datetime(2026, 1, 1, 10, 0, 0, tzinfo=SLST)  # Thursday
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_MARKET_HOLIDAY)

    def test_apr_13_market_holiday(self):
        """April 13 → MARKET_HOLIDAY (Sinhala & Tamil New Year)"""
        dt = datetime.datetime(2026, 4, 13, 10, 0, 0, tzinfo=SLST)  # Monday
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_MARKET_HOLIDAY)

    def test_apr_14_market_holiday(self):
        """April 14 → MARKET_HOLIDAY (Sinhala & Tamil New Year)"""
        dt = datetime.datetime(2026, 4, 14, 10, 0, 0, tzinfo=SLST)  # Tuesday
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_MARKET_HOLIDAY)

    def test_year_boundary_jan1_holiday(self):
        """Year boundary: Jan 1 → MARKET_HOLIDAY"""
        dt = datetime.datetime(2027, 1, 1, 10, 0, 0, tzinfo=SLST)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_MARKET_HOLIDAY)

    def test_regular_weekday_not_holiday(self):
        """A regular weekday (not a holiday) during open hours → OPEN"""
        # Jan 5, 2026 was a Monday, not a holiday
        dt = datetime.datetime(2026, 1, 5, 11, 0, 0, tzinfo=SLST)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_OPEN)

    def test_get_cse_market_status_keys(self):
        """get_cse_market_status() returns all expected keys"""
        dt = self._make_dt(0, 11, 0)  # Monday 11 AM OPEN
        status = ms.get_cse_market_status(dt)
        expected_keys = {
            "is_open", "next_open", "next_close", "current_time_sl",
            "trading_day_remaining", "data_status", "session",
            "session_label", "next_transition",
        }
        self.assertEqual(set(status.keys()), expected_keys)
        self.assertTrue(status["is_open"])
        self.assertEqual(status["session"], ms.SESSION_OPEN)
        self.assertEqual(status["session_label"], "Open")

    def test_get_cse_market_status_closed(self):
        """get_cse_market_status() returns correct values when closed"""
        dt = self._make_dt(0, 7, 0)  # Monday 7 AM CLOSED
        status = ms.get_cse_market_status(dt)
        self.assertFalse(status["is_open"])
        self.assertEqual(status["session"], ms.SESSION_CLOSED)

    def test_get_refresh_interval_open(self):
        """During OPEN, refresh interval is 120s"""
        dt = self._make_dt(0, 11, 0)
        self.assertEqual(ms.get_refresh_interval_seconds(dt), 120)

    def test_get_refresh_interval_pre_open(self):
        """During PRE_OPEN, refresh interval is 300s"""
        dt = self._make_dt(0, 9, 15)
        self.assertEqual(ms.get_refresh_interval_seconds(dt), 300)

    def test_get_refresh_interval_closed(self):
        """When CLOSED, refresh interval is 900s"""
        dt = self._make_dt(0, 15, 0)
        self.assertEqual(ms.get_refresh_interval_seconds(dt), 900)

    def test_get_refresh_interval_weekend(self):
        """During WEEKEND, refresh interval is 900s"""
        dt = self._make_dt(5, 11, 0)  # Saturday
        self.assertEqual(ms.get_refresh_interval_seconds(dt), 900)

    def test_get_refresh_interval_holiday(self):
        """On MARKET_HOLIDAY, refresh interval is 900s"""
        dt = datetime.datetime(2026, 12, 25, 10, 0, 0, tzinfo=SLST)
        self.assertEqual(ms.get_refresh_interval_seconds(dt), 900)

    def test_get_time_until_status_change_open(self):
        """During OPEN, countdown shows 'Closes in HH:MM:SS'"""
        dt = self._make_dt(0, 11, 0)  # Monday 11 AM, close at 2:30 PM = 3h30m
        result = ms.get_time_until_status_change(dt)
        self.assertIn("Closes in", result)
        # 3h30m = 03:30:00
        self.assertEqual(result, "Closes in 03:30:00")

    def test_get_time_until_status_change_pre_open(self):
        """During PRE_OPEN, countdown shows 'Opens in Xm'"""
        dt = self._make_dt(0, 9, 15)  # Monday 9:15 AM, open at 9:30 AM = 15m
        result = ms.get_time_until_status_change(dt)
        self.assertIn("Opens in", result)
        self.assertEqual(result, "Opens in 15m")

    def test_get_time_until_status_change_closed(self):
        """When CLOSED (before pre-open), countdown shows 'Opens in Xh Xm'"""
        dt = self._make_dt(0, 7, 0)  # Monday 7 AM, open at 9:30 AM = 2h30m
        result = ms.get_time_until_status_change(dt)
        self.assertIn("Opens in", result)
        self.assertIn("h", result)

    def test_market_status_labels(self):
        """get_market_status_label returns correct labels"""
        self.assertEqual(ms.get_market_status_label(ms.SESSION_OPEN), "Open")
        self.assertEqual(ms.get_market_status_label(ms.SESSION_PRE_OPEN), "Pre-Open Session")
        self.assertEqual(ms.get_market_status_label(ms.SESSION_CLOSED), "Closed")
        self.assertEqual(ms.get_market_status_label(ms.SESSION_WEEKEND), "Weekend")
        self.assertEqual(ms.get_market_status_label(ms.SESSION_MARKET_HOLIDAY), "Market Holiday")
        self.assertEqual(ms.get_market_status_label(ms.SESSION_UNKNOWN), "Unknown")
        self.assertEqual(ms.get_market_status_label("BOGUS"), "Unknown")

    def test_format_slst_time(self):
        """format_slst_time formats correctly"""
        dt = self._make_dt(0, 11, 25)
        result = ms.format_slst_time(dt)
        self.assertIn("11:25 AM", result)
        self.assertIn("SLST", result)

    def test_format_slst_date(self):
        """format_slst_date includes day abbreviation"""
        dt = self._make_dt(0, 9, 30)  # Monday
        result = ms.format_slst_date(dt)
        self.assertIn("Mon", result)
        self.assertIn("SLST", result)

    def test_is_market_holiday_known(self):
        """is_market_holiday returns True for known holidays"""
        self.assertTrue(ms.is_market_holiday(datetime.date(2026, 12, 25)))
        self.assertTrue(ms.is_market_holiday(datetime.date(2026, 1, 1)))
        self.assertTrue(ms.is_market_holiday(datetime.date(2026, 4, 13)))

    def test_is_market_holiday_unknown(self):
        """is_market_holiday returns False for non-holidays"""
        self.assertFalse(ms.is_market_holiday(datetime.date(2026, 1, 5)))  # Monday
        self.assertFalse(ms.is_market_holiday(datetime.date(2026, 7, 15)))  # Regular day

    def test_get_next_market_open_from_closed(self):
        """get_next_market_open from a closed state returns next trading day"""
        dt = self._make_dt(0, 7, 0)  # Monday 7 AM
        next_open = ms.get_next_market_open(dt)
        self.assertIsNotNone(next_open)
        # Should be today at 9:30 AM
        expected = datetime.datetime(2026, 1, 5, 9, 30, 0, tzinfo=SLST)
        self.assertEqual(next_open, expected)

    def test_get_next_market_open_from_pre_open(self):
        """get_next_market_open from PRE_OPEN returns today at 9:30"""
        dt = self._make_dt(0, 9, 15)
        next_open = ms.get_next_market_open(dt)
        expected = datetime.datetime(2026, 1, 5, 9, 30, 0, tzinfo=SLST)
        self.assertEqual(next_open, expected)

    def test_get_next_market_open_from_open(self):
        """get_next_market_open from OPEN returns next trading day"""
        dt = self._make_dt(0, 11, 0)
        next_open = ms.get_next_market_open(dt)
        self.assertIsNotNone(next_open)
        # Should be Tuesday Jan 6, 2026 at 9:30 AM
        expected = datetime.datetime(2026, 1, 6, 9, 30, 0, tzinfo=SLST)
        self.assertEqual(next_open, expected)

    def test_get_next_market_open_after_friday_close(self):
        """get_next_market_open after Friday close returns Monday"""
        dt = self._make_dt(4, 15, 0)  # Friday 3 PM
        next_open = ms.get_next_market_open(dt)
        self.assertIsNotNone(next_open)
        # Should be Monday Jan 12 (since Jan 5 is Monday, Jan 9 is Friday, next Mon is Jan 12)
        # Wait: Jan 5 2026 is Monday. So Jan 5+4 = Jan 9 is Friday. Next Monday = Jan 12.
        self.assertEqual(next_open.weekday(), 0)  # Monday
        self.assertEqual(next_open.hour, 9)
        self.assertEqual(next_open.minute, 30)

    def test_get_next_market_close_from_open(self):
        """get_next_market_close during OPEN returns today's close"""
        dt = self._make_dt(0, 11, 0)  # Mon 11 AM
        next_close = ms.get_next_market_close(dt)
        expected = datetime.datetime(2026, 1, 5, 14, 30, 0, tzinfo=SLST)
        self.assertEqual(next_close, expected)

    def test_get_next_market_close_from_closed(self):
        """get_next_market_close when closed returns next trading day's close"""
        dt = self._make_dt(0, 7, 0)  # Mon 7 AM
        next_close = ms.get_next_market_close(dt)
        expected = datetime.datetime(2026, 1, 5, 14, 30, 0, tzinfo=SLST)
        self.assertEqual(next_close, expected)

    def test_get_next_market_close_after_friday(self):
        """get_next_market_close after Friday close returns Monday close"""
        dt = self._make_dt(4, 15, 0)  # Fri 3 PM
        next_close = ms.get_next_market_close(dt)
        self.assertIsNotNone(next_close)
        self.assertEqual(next_close.hour, 14)
        self.assertEqual(next_close.minute, 30)

    def test_backward_compat_is_cse_market_open(self):
        """Legacy is_cse_market_open() still works correctly"""
        self.assertTrue(ms.is_cse_market_open(self._make_dt(0, 11, 0)))
        self.assertFalse(ms.is_cse_market_open(self._make_dt(0, 7, 0)))
        self.assertFalse(ms.is_cse_market_open(self._make_dt(5, 11, 0)))  # Saturday
        self.assertFalse(ms.is_cse_market_open(
            datetime.datetime(2026, 12, 25, 10, 0, 0, tzinfo=SLST)
        ))

    def test_backward_compat_get_refresh_interval(self):
        """Legacy get_refresh_interval_seconds() still works"""
        self.assertEqual(ms.get_refresh_interval_seconds(None), 900)
        # When open
        self.assertEqual(ms.get_refresh_interval_seconds(
            self._make_dt(0, 11, 0)
        ), 120)

    def test_holiday_unknown_on_exception(self):
        """If holiday detection raises, session returns UNKNOWN (not OPEN)"""
        # Patch is_market_holiday to raise
        with patch.object(ms, "is_market_holiday", side_effect=Exception("Boom!")):
            dt = self._make_dt(0, 11, 0)
            session = ms.get_market_session(dt)
            self.assertEqual(session, ms.SESSION_UNKNOWN)

    def test_slst_now_returns_aware(self):
        """get_slst_now() returns a timezone-aware datetime"""
        now = ms.get_slst_now()
        self.assertIsNotNone(now.tzinfo)
        self.assertEqual(now.tzinfo.key, "Asia/Colombo")

    def test_get_cse_market_status_unknown_on_exception(self):
        """If holiday detection fails, data_status is safe"""
        with patch.object(ms, "is_market_holiday", side_effect=Exception("Boom!")):
            dt = self._make_dt(0, 11, 0)
            status = ms.get_cse_market_status(dt)
            self.assertEqual(status["session"], ms.SESSION_UNKNOWN)

    def test_pre_open_edge_9am_exactly(self):
        """9:00 AM exactly → PRE_OPEN"""
        dt = self._make_dt(0, 9, 0)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_PRE_OPEN)

    def test_pre_open_edge_929(self):
        """9:29 AM → PRE_OPEN"""
        dt = self._make_dt(0, 9, 29)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_PRE_OPEN)

    def test_open_edge_931(self):
        """9:31 AM → OPEN"""
        dt = self._make_dt(0, 9, 31)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_OPEN)

    def test_closed_edge_1429(self):
        """2:29 PM → OPEN (still in trading)"""
        dt = self._make_dt(0, 14, 29)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_OPEN)

    def test_closed_edge_1430(self):
        """2:30 PM → CLOSED"""
        dt = self._make_dt(0, 14, 30)
        session = ms.get_market_session(dt)
        self.assertEqual(session, ms.SESSION_CLOSED)

    def test_time_until_change_at_close_edge(self):
        """At exactly close time, countdown says 'Closes now'"""
        dt = self._make_dt(0, 14, 30)
        result = ms.get_time_until_status_change(dt)
        # At 14:30, the session is CLOSED, not OPEN
        # So it should show "Opens in ..."
        self.assertIn("Opens in", result)

    def test_freshness_unknown_without_source(self):
        """get_data_freshness_status returns UNKNOWN when source unavailable"""
        import streamlit
        data = {
            "companies": [],
            "market_summary": {},
            "last_updated": None,
            "source_available": False,
            "fetch_error": "Connection error",
        }
        # Pre-seed streamlit session state so get_data_freshness_status can read it
        session_key = "_cse_market_data"
        if session_key not in streamlit.session_state:
            streamlit.session_state[session_key] = {}
        streamlit.session_state[session_key]["last_fetch_time"] = None

        result = ms.get_data_freshness_status(data)
        self.assertEqual(result["label"], "UNKNOWN")
        self.assertEqual(result["color"], "grey")


class TestHolidayList(unittest.TestCase):
    """Verify that the HOLIDAYS set contains expected dates."""

    def test_holidays_contains_new_year(self):
        self.assertIn((1, 1), ms.HOLIDAYS)

    def test_holidays_contains_sinhala_tamil_new_year(self):
        self.assertIn((4, 13), ms.HOLIDAYS)
        self.assertIn((4, 14), ms.HOLIDAYS)

    def test_holidays_contains_christmas(self):
        self.assertIn((12, 25), ms.HOLIDAYS)

    def test_holidays_not_contains_random(self):
        self.assertNotIn((6, 15), ms.HOLIDAYS)
        self.assertNotIn((3, 20), ms.HOLIDAYS)
        self.assertNotIn((9, 1), ms.HOLIDAYS)


class TestTradingHoursConfig(unittest.TestCase):
    """Verify TRADING_HOURS_CONFIG structure."""

    def test_config_has_all_keys(self):
        expected_keys = {"pre_open_start", "pre_open_end", "open_start", "close_time", "weekdays", "timezone_name"}
        self.assertEqual(set(ms.TRADING_HOURS_CONFIG.keys()), expected_keys)

    def test_config_times_are_time_objects(self):
        for key in ("pre_open_start", "pre_open_end", "open_start", "close_time"):
            self.assertIsInstance(ms.TRADING_HOURS_CONFIG[key], datetime.time)

    def test_weekdays_tuple(self):
        self.assertEqual(ms.TRADING_HOURS_CONFIG["weekdays"], (0, 1, 2, 3, 4))

    def test_timezone_name(self):
        self.assertEqual(ms.TRADING_HOURS_CONFIG["timezone_name"], "Asia/Colombo")


class TestBackwardCompatibility(unittest.TestCase):
    """Ensure old public API still works exactly as before."""

    def test_is_cse_market_open_none_defaults(self):
        """is_cse_market_open() with no args doesn't crash"""
        # Can't test exact value since we don't control time, but should not raise
        result = ms.is_cse_market_open()
        self.assertIsInstance(result, bool)

    def test_get_cse_market_status_none_defaults(self):
        """get_cse_market_status() with no args doesn't crash"""
        result = ms.get_cse_market_status()
        self.assertIsInstance(result, dict)
        self.assertIn("is_open", result)
        self.assertIn("next_open", result)
        self.assertIn("next_close", result)

    def test_get_refresh_interval_no_args(self):
        """get_refresh_interval_seconds() with no args doesn't crash"""
        result = ms.get_refresh_interval_seconds()
        self.assertIsInstance(result, int)

    def test_naive_datetime_auto_converted(self):
        """A naive datetime is auto-converted to SLST"""
        naive = datetime.datetime(2026, 1, 5, 11, 0, 0)  # no tzinfo
        # Should still work
        self.assertTrue(ms.is_cse_market_open(naive))
        status = ms.get_cse_market_status(naive)
        self.assertTrue(status["is_open"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
