"""Data source registry for Stock Scope.

Maps every fundamental/valuation/risk field used in the app to its source
and availability for CSE stocks.  This single source of truth prevents
silent data corruption when yfinance returns None for Colombo Stock Exchange
tickers (the .CM suffix has price history but zero fundamental data).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataField:
    """Metadata for a single data field used in the app."""

    name: str  # Human-readable label, e.g. "P/E Ratio"
    key: str  # Programmatic key, e.g. "trailingPE"
    category: str  # "financial_health", "valuation", "risk", "market_data"
    source: str  # "yfinance", "CSE API", "calculated"
    is_available_for_cse: bool  # True only if CSE API / yfinance provides it
    format_fn: str  # "percent", "ratio", "currency", "number"
    description: str  # Plain English explanation


# ── Financial Health fields (all from yfinance, NONE available for CSE) ───

FINANCIAL_HEALTH_FIELDS: list[DataField] = [
    DataField(
        name="Cash cushion (current ratio)",
        key="currentRatio",
        category="financial_health",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="ratio",
        description="Current assets divided by current liabilities — measures short-term liquidity.",
    ),
    DataField(
        name="Debt load (debt-to-equity)",
        key="debtToEquity",
        category="financial_health",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="ratio",
        description="Total debt divided by shareholder equity — how much leverage the company uses.",
    ),
    DataField(
        name="Operating margin",
        key="operatingMargins",
        category="financial_health",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="percent",
        description="Operating income divided by revenue — profitability from core operations.",
    ),
    DataField(
        name="Profit margin",
        key="profitMargins",
        category="financial_health",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="percent",
        description="Net income divided by revenue — overall profitability after all expenses.",
    ),
    DataField(
        name="Return on assets",
        key="returnOnAssets",
        category="financial_health",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="percent",
        description="Net income divided by total assets — how efficiently assets generate profit.",
    ),
    DataField(
        name="Free cash flow",
        key="freeCashflow",
        category="financial_health",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="currency",
        description="Cash from operations minus capital expenditures — available for expansion or dividends.",
    ),
    DataField(
        name="Revenue growth",
        key="revenueGrowth",
        category="financial_health",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="percent",
        description="Year-over-year revenue growth rate.",
    ),
    DataField(
        name="Earnings growth",
        key="earningsGrowth",
        category="financial_health",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="percent",
        description="Year-over-year earnings growth rate.",
    ),
]

# ── Valuation fields (all from yfinance, NONE available for CSE) ──────────

VALUATION_FIELDS: list[DataField] = [
    DataField(
        name="P/E Ratio (trailing)",
        key="trailingPE",
        category="valuation",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="ratio",
        description="Price divided by trailing 12-month earnings per share.",
    ),
    DataField(
        name="P/E Ratio (forward)",
        key="forwardPE",
        category="valuation",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="ratio",
        description="Price divided by expected future earnings per share.",
    ),
    DataField(
        name="Price / Book",
        key="priceToBook",
        category="valuation",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="ratio",
        description="Price divided by book value per share.",
    ),
    DataField(
        name="Price / Sales",
        key="priceToSalesTrailing12Months",
        category="valuation",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="ratio",
        description="Price divided by trailing 12-month revenue per share.",
    ),
    DataField(
        name="PEG Ratio",
        key="pegRatio",
        category="valuation",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="ratio",
        description="P/E divided by earnings growth rate — adjusts P/E for growth.",
    ),
    DataField(
        name="Trailing EPS",
        key="trailingEps",
        category="valuation",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="currency",
        description="Trailing 12-month earnings per share.",
    ),
    DataField(
        name="Analyst target price",
        key="targetMeanPrice",
        category="valuation",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="currency",
        description="Average analyst price target.",
    ),
]

# ── Risk fields ───────────────────────────────────────────────────────────

RISK_FIELDS: list[DataField] = [
    DataField(
        name="Volatility (annualised)",
        key="volatility",
        category="risk",
        source="calculated",
        is_available_for_cse=True,
        format_fn="percent",
        description="Annualised standard deviation of daily returns — how much the price typically swings.",
    ),
    DataField(
        name="Beta",
        key="beta",
        category="risk",
        source="yfinance + CSE API",
        is_available_for_cse=True,
        format_fn="ratio",
        description="Sensitivity to the overall market. Beta > 1 means it amplifies market moves.",
    ),
    DataField(
        name="Max drawdown",
        key="maxDrawdown",
        category="risk",
        source="calculated",
        is_available_for_cse=True,
        format_fn="percent",
        description="Largest peak-to-trough decline in the selected period.",
    ),
    DataField(
        name="Debt / equity",
        key="debtToEquity",
        category="risk",
        source="yfinance",
        is_available_for_cse=False,
        format_fn="ratio",
        description="Total debt divided by shareholder equity — not available for CSE stocks.",
    ),
]

# ── CSE API market-data fields (available for CSE only) ───────────────────

CSE_API_FIELDS: list[DataField] = [
    DataField(
        name="Market Cap",
        key="cse_market_cap",
        category="market_data",
        source="CSE API",
        is_available_for_cse=True,
        format_fn="currency",
        description="Total market capitalisation from the CSE API.",
    ),
    DataField(
        name="52-Week High",
        key="cse_52w_high",
        category="market_data",
        source="CSE API",
        is_available_for_cse=True,
        format_fn="currency",
        description="12-month high price from the CSE API.",
    ),
    DataField(
        name="52-Week Low",
        key="cse_52w_low",
        category="market_data",
        source="CSE API",
        is_available_for_cse=True,
        format_fn="currency",
        description="12-month low price from the CSE API.",
    ),
    DataField(
        name="Beta (CSE)",
        key="cse_beta",
        category="market_data",
        source="CSE API",
        is_available_for_cse=True,
        format_fn="ratio",
        description="Beta value calculated by the Colombo Stock Exchange.",
    ),
    DataField(
        name="Volume (today)",
        key="cse_volume",
        category="market_data",
        source="CSE API",
        is_available_for_cse=True,
        format_fn="number",
        description="Today's trading volume from the CSE API.",
    ),
    DataField(
        name="Turnover (today)",
        key="cse_turnover",
        category="market_data",
        source="CSE API",
        is_available_for_cse=True,
        format_fn="currency",
        description="Today's turnover value from the CSE API.",
    ),
]

# ── Aggregate lookup helpers ──────────────────────────────────────────────

ALL_FIELDS: list[DataField] = (
    FINANCIAL_HEALTH_FIELDS
    + VALUATION_FIELDS
    + RISK_FIELDS
    + CSE_API_FIELDS
)

_FIELD_BY_KEY: dict[str, DataField] = {f.key: f for f in ALL_FIELDS}


def field_by_key(key: str) -> DataField | None:
    """Look up a DataField by its programmatic key."""
    return _FIELD_BY_KEY.get(key)


def is_field_available_for_cse(key: str) -> bool:
    """Check whether a field is available for CSE stocks."""
    field = _FIELD_BY_KEY.get(key)
    if field is None:
        return False
    return field.is_available_for_cse


def category_fields(category: str) -> list[DataField]:
    """Return all fields in a given category."""
    return [f for f in ALL_FIELDS if f.category == category]


def available_cse_fields(category: str | None = None) -> list[DataField]:
    """Return fields that are available for CSE, optionally filtered by category."""
    fields = ALL_FIELDS if category is None else category_fields(category)
    return [f for f in fields if f.is_available_for_cse]


def unavailable_cse_fields(category: str | None = None) -> list[DataField]:
    """Return fields that are NOT available for CSE, optionally filtered by category."""
    fields = ALL_FIELDS if category is None else category_fields(category)
    return [f for f in fields if not f.is_available_for_cse]
