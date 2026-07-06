"""Risk-based investment analysis engine for Stock Scope.

Provides comprehensive risk scoring, scenario projection, portfolio allocation,
and ranking functions for the Risk & Investment Simulator feature.

All functions are pure calculation logic (no Streamlit dependency).
"""

from __future__ import annotations

import concurrent.futures
import math
import time
from typing import Any

import numpy as np
import pandas as pd

from stock_utils import (
    add_indicators,
    build_financial_health,
    build_risk_snapshot,
    load_price_history,
    load_company_info,
    load_company_profile,
    summarize,
)

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def format_risk_label(score: float) -> str:
    """Map a numeric risk score (0-100) to a human-readable label.

    - 0-30:   "Lower Risk"
    - 31-60:  "Moderate Risk"
    - 61-100: "Higher Risk"
    """
    if score <= 30:
        return "Lower Risk"
    if score <= 60:
        return "Moderate Risk"
    return "Higher Risk"


def get_horizon_days(horizon: str) -> int:
    """Map a human-readable horizon string to approximate trading days.

    Parameters
    ----------
    horizon : str
        One of ``"1 month"``, ``"3 months"``, ``"6 months"``,
        ``"1 year"``, ``"3 years"``, ``"5 years"``.

    Returns
    -------
    int
        Number of trading days (default 252 if label is unrecognised).
    """
    mapping = {
        "1 month": 21,
        "3 months": 63,
        "6 months": 126,
        "1 year": 252,
        "3 years": 756,
        "5 years": 1260,
    }
    return mapping.get(horizon.strip().lower(), 252)


def compute_portfolio_risk_score(
    risk_scores: list[float], weights: list[float]
) -> float:
    """Weighted average of individual stock risk scores.

    Parameters
    ----------
    risk_scores : list[float]
        Individual risk scores (0-100).
    weights : list[float]
        Corresponding weight values (do not need to sum to 1 — the function
        normalises internally).

    Returns
    -------
    float
        Portfolio-level risk score.
    """
    if not risk_scores or not weights:
        return 0.0
    if len(risk_scores) != len(weights):
        raise ValueError("risk_scores and weights must have the same length")
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(s * w for s, w in zip(risk_scores, weights))
    return round(weighted_sum / total_weight, 1)


# ---------------------------------------------------------------------------
# Core risk & scenario calculations
# ---------------------------------------------------------------------------

def compute_risk_score(
    price_history_df: pd.DataFrame, company_info_dict: dict
) -> dict:
    """Calculate a comprehensive Risk Score (0-100) for a single stock.

    Component breakdown
    -------------------
    - **Volatility (25%)**:      Annualised standard deviation of daily returns.
    - **Max Drawdown (20%)**:    Maximum peak-to-trough decline.
    - **Beta (15%)**:            Market sensitivity from yfinance / CSE API.
    - **Financial Health (15%)**: Debt levels, cash position, operating margin.
    - **Liquidity Risk (15%)**:  Average trading volume relative to shares outstanding.
    - **Historical Stability (10%)**: Frequency of daily returns < -5%.

    Parameters
    ----------
    price_history_df : pd.DataFrame
        DataFrame with at least a ``"Close"`` column and optionally ``"Volume"``.
    company_info_dict : dict
        Company information dict (from yfinance ``Ticker.info``, optionally
        enhanced with CSE API fields).

    Returns
    -------
    dict
        Keys: ``score``, ``level``, ``volatility``, ``beta``, ``max_drawdown``,
        ``financial_health``, ``liquidity_risk``, ``debt_risk``, ``historical_return``.
    """
    close = price_history_df["Close"]
    daily_returns = close.pct_change().dropna()

    # --- 1. Volatility (25%) ------------------------------------------------
    if not daily_returns.empty:
        daily_vol = daily_returns.std()
        annualized_vol = float(daily_vol * math.sqrt(252))
    else:
        annualized_vol = 0.0
    # 0% vol = 0 pts, 60%+ vol = 25 pts (linear in between)
    vol_score = min(25.0, (annualized_vol / 0.60) * 25.0)

    # --- 2. Max Drawdown (20%) ----------------------------------------------
    max_dd = 0.0
    if not price_history_df.empty:
        running_max = close.cummax()
        drawdown = (close / running_max) - 1.0
        max_dd = float(drawdown.min())
    # 0% drawdown = 0 pts, 50%+ drawdown = 20 pts
    dd_score = min(20.0, (abs(max_dd) / 0.50) * 20.0)

    # --- 3. Beta (15%) ------------------------------------------------------
    beta = company_info_dict.get("beta")
    if beta is None:
        beta = company_info_dict.get("cse_beta")
    if beta is None:
        beta = 1.0
    beta = float(beta)
    # beta <= 0.5 = 0 pts, beta >= 2.0 = 15 pts
    beta_score = min(15.0, max(0.0, (beta - 0.5) / 1.5 * 15.0))

    # --- 4. Financial Health (15%) ------------------------------------------
    try:
        health_result = build_financial_health(company_info_dict)
        health_raw_score = health_result.score  # float or None
        health_label_raw = health_result.label  # "Healthy", "Mixed", "Watch", or "Data unavailable"
    except Exception:
        health_raw_score = None
        health_label_raw = "Data unavailable"

    if health_raw_score is not None:
        # Map build_financial_health labels to risk-oriented labels
        if health_label_raw == "Healthy":
            financial_health_label = "Strong"
        elif health_label_raw == "Mixed":
            financial_health_label = "Fair"
        else:
            financial_health_label = "Weak"

        # Invert: healthy company = low risk contribution
        health_score = (1.0 - health_raw_score) * 15.0
    else:
        financial_health_label = "Data Unavailable"
        health_score = 0.0  # No penalty — data simply doesn't exist

    # Debt risk (more specific: based on debt-to-equity, skip if unavailable)
    debt_to_equity = company_info_dict.get("debtToEquity")
    if debt_to_equity is not None:
        dte = float(debt_to_equity)
        if dte < 50:
            debt_risk_label = "Low"
        elif dte <= 200:
            debt_risk_label = "Moderate"
        else:
            debt_risk_label = "High"
    else:
        debt_risk_label = "Unavailable"

    # --- 5. Liquidity Risk (15%) --------------------------------------------
    avg_volume = (
        float(price_history_df["Volume"].dropna().mean())
        if "Volume" in price_history_df.columns
        else 0.0
    )

    # Estimate shares outstanding from market cap / price
    shares_outstanding = company_info_dict.get("sharesOutstanding")
    if shares_outstanding is None:
        market_cap = company_info_dict.get(
            "marketCap"
        ) or company_info_dict.get("cse_market_cap")
        latest_price = float(close.iloc[-1]) if not close.empty else None
        if market_cap is not None and latest_price and latest_price > 0:
            shares_outstanding = market_cap / latest_price

    if shares_outstanding and shares_outstanding > 0 and avg_volume > 0:
        turnover_ratio = avg_volume / shares_outstanding
        # turnover_ratio >= 0.005  → 0 pts (liquid, low risk)
        # turnover_ratio <= 0      → 15 pts (illiquid, high risk)
        liquidity_score = 15.0 * max(0.0, min(1.0, 1.0 - turnover_ratio / 0.005))
    else:
        liquidity_score = 7.5  # Conservative default (Medium)

    if liquidity_score <= 5:
        liquidity_label = "Low"
    elif liquidity_score <= 10:
        liquidity_label = "Medium"
    else:
        liquidity_label = "High"

    # --- 6. Historical Stability (10%) --------------------------------------
    if not daily_returns.empty:
        large_negative_freq = float(
            (daily_returns < -0.05).sum() / len(daily_returns)
        )
    else:
        large_negative_freq = 0.0
    # 0% frequency = 0 pts, 10%+ frequency = 10 pts
    stability_score = min(10.0, (large_negative_freq / 0.10) * 10.0)

    # --- Total Score --------------------------------------------------------
    # When financial health data is unavailable (health_score = 0), we
    # redistribute the 15% weight proportionally across the other components
    # to keep the total in the 0-100 range.
    if health_raw_score is not None:
        total_score = (
            vol_score + dd_score + beta_score + health_score
            + liquidity_score + stability_score
        )
    else:
        # Financial health weight (15%) redistributed:
        # Volatility 29%, Max Drawdown 24%, Beta 18%, Liquidity 18%, Stability 11%
        scale = 100.0 / 85.0  # 1.17647 — scales 85 max back to 100
        base_score = vol_score + dd_score + beta_score + liquidity_score + stability_score
        total_score = base_score * scale

    total_score = max(0.0, min(100.0, total_score))

    # Annualised historical return
    if not daily_returns.empty:
        mean_daily_return = daily_returns.mean()
        historical_return = float((1.0 + mean_daily_return) ** 252 - 1.0)
    else:
        historical_return = 0.0

    return {
        "score": round(total_score, 1),
        "level": format_risk_label(total_score),
        "volatility": round(annualized_vol, 4),
        "beta": round(beta, 4),
        "max_drawdown": round(max_dd, 4),
        "financial_health": financial_health_label,
        "liquidity_risk": liquidity_label,
        "debt_risk": debt_risk_label,
        "historical_return": round(historical_return, 4),
    }


def compute_scenario_prices(
    price_history_df: pd.DataFrame, horizon_days: int
) -> dict:
    """Calculate Bear, Base, Bull future price estimates.

    Methodology
    -----------
    - **Base**: Historical mean daily return projected forward.
    - **Bull**: Base return + 1.5 × upside semi-deviation × sqrt(horizon).
    - **Bear**: Base return − 1.5 × downside semi-deviation × sqrt(horizon).

    Upside / downside semi-deviation uses the standard deviation of only
    positive / negative daily returns respectively, scaled by sqrt(horizon).

    Parameters
    ----------
    price_history_df : pd.DataFrame
        Must contain a ``"Close"`` column.
    horizon_days : int
        Number of trading days to project forward.

    Returns
    -------
    dict
        Keys: ``bear``, ``base``, ``bull`` (each a dict with ``price`` and
        ``return``) and ``horizon_days``.
    """
    close = price_history_df["Close"]
    daily_returns = close.pct_change().dropna()
    last_price = float(close.iloc[-1])

    if daily_returns.empty or len(daily_returns) < 5:
        # Not enough data — return flat projection
        return {
            "bear": {"price": round(last_price, 2), "return": 0.0},
            "base": {"price": round(last_price, 2), "return": 0.0},
            "bull": {"price": round(last_price, 2), "return": 0.0},
            "horizon_days": horizon_days,
        }

    # --- Base scenario: historical mean return projected forward -------------
    mean_daily_return = daily_returns.mean()
    base_return = (1.0 + mean_daily_return) ** horizon_days - 1.0
    base_price = last_price * (1.0 + base_return)

    # --- Semi-deviation (upside / downside) ----------------------------------
    positive_returns = daily_returns[daily_returns > 0]
    negative_returns = daily_returns[daily_returns < 0]

    # Overall daily std as fallback if one side has too few samples
    overall_daily_std = daily_returns.std()

    if len(positive_returns) > 1:
        upside_std = positive_returns.std() * math.sqrt(horizon_days)
    else:
        upside_std = overall_daily_std * math.sqrt(horizon_days)

    if len(negative_returns) > 1:
        downside_std = negative_returns.std() * math.sqrt(horizon_days)
    else:
        downside_std = overall_daily_std * math.sqrt(horizon_days)

    # --- Bull scenario -------------------------------------------------------
    bull_return = base_return + 1.5 * upside_std
    bull_price = last_price * (1.0 + bull_return)

    # --- Bear scenario -------------------------------------------------------
    bear_return = base_return - 1.5 * downside_std
    bear_price = last_price * (1.0 + bear_return)

    return {
        "bear": {"price": round(bear_price, 2), "return": round(bear_return, 4)},
        "base": {"price": round(base_price, 2), "return": round(base_return, 4)},
        "bull": {"price": round(bull_price, 2), "return": round(bull_return, 4)},
        "horizon_days": horizon_days,
    }


# ---------------------------------------------------------------------------
# Investment & future value helpers
# ---------------------------------------------------------------------------

def calculate_investment(
    investment_amount: float, share_price: float
) -> dict:
    """Calculate whole shares purchasable, actual amount invested, cash leftover.

    Parameters
    ----------
    investment_amount : float
        Total capital to deploy (e.g. 100000.0).
    share_price : float
        Price per share.

    Returns
    -------
    dict
        Keys: ``shares``, ``actual_invested``, ``cash_remaining``, ``share_price``.
    """
    if share_price <= 0:
        return {
            "shares": 0,
            "actual_invested": 0.0,
            "cash_remaining": round(investment_amount, 2),
            "share_price": round(share_price, 2),
        }
    shares = math.floor(investment_amount / share_price)
    actual_invested = shares * share_price
    cash_remaining = investment_amount - actual_invested
    return {
        "shares": shares,
        "actual_invested": round(actual_invested, 2),
        "cash_remaining": round(cash_remaining, 2),
        "share_price": round(share_price, 2),
    }


def calculate_future_value(
    shares: int,
    future_price: float,
    cash_remaining: float,
    original_investment: float,
) -> dict:
    """Calculate future portfolio value and profit / loss from a scenario price.

    Parameters
    ----------
    shares : int
        Number of shares held.
    future_price : float
        Projected per-share price.
    cash_remaining : float
        Uninvested cash.
    original_investment : float
        Total capital originally deployed.

    Returns
    -------
    dict
        Keys: ``portfolio_value``, ``profit_loss``, ``return_pct``.
    """
    portfolio_value = shares * future_price + cash_remaining
    profit_loss = portfolio_value - original_investment
    return_pct = (
        (profit_loss / original_investment) * 100
        if original_investment
        else 0.0
    )
    return {
        "portfolio_value": round(portfolio_value, 2),
        "profit_loss": round(profit_loss, 2),
        "return_pct": round(return_pct, 2),
    }


# ---------------------------------------------------------------------------
# Risk-adjusted scoring
# ---------------------------------------------------------------------------

def compute_risk_adjusted_score(
    risk_score_dict: dict, scenario_dict: dict
) -> float:
    """Combine risk score and scenario returns into a risk-adjusted score.

    Formula
    -------
    ``(base_return + 0.5 * bull_return - 0.5 * bear_return) / (risk_score / 100)``

    Higher values indicate a better risk-return trade-off.

    Parameters
    ----------
    risk_score_dict : dict
        Output of :func:`compute_risk_score`.
    scenario_dict : dict
        Output of :func:`compute_scenario_prices`.

    Returns
    -------
    float
    """
    base_return = scenario_dict.get("base", {}).get("return", 0.0)
    bull_return = scenario_dict.get("bull", {}).get("return", 0.0)
    bear_return = scenario_dict.get("bear", {}).get("return", 0.0)
    risk_score = risk_score_dict.get("score", 50.0)

    if risk_score <= 0:
        risk_score = 1.0  # avoid division by zero

    numerator = base_return + 0.5 * bull_return - 0.5 * bear_return
    return round(numerator / (risk_score / 100.0), 4)


# ---------------------------------------------------------------------------
# Signal logic
# ---------------------------------------------------------------------------

def compute_signal(
    risk_score: float,
    risk_level: str,
    financial_health: str,
    base_return_pct: float,
    volatility: float,
    beta: float,
    max_drawdown: float,
    liquidity_risk: str,
    historical_return_pct: float,
) -> dict:
    """Multi-component investment signal with confidence scoring.

    Evaluates risk, liquidity, financial strength, and return outlook
    to produce a 5-tier signal with an auditable confidence score.

    Returns
    -------
    dict with keys: signal, confidence, components, data_quality_note
    """
    # --- Component scoring ---
    # 1. Risk
    if risk_score <= 30:
        risk_c = "low"
    elif risk_score <= 60:
        risk_c = "moderate"
    else:
        risk_c = "high"

    # 2. Liquidity
    if liquidity_risk == "Low":
        liquidity_c = "good"
    elif liquidity_risk == "Medium":
        liquidity_c = "medium"
    else:
        liquidity_c = "poor"

    # 3. Financial strength
    fh = financial_health
    if fh in ("Strong", "Healthy"):
        financial_strength_c = "strong"
    elif fh in ("Fair", "Mixed"):
        financial_strength_c = "fair"
    elif fh in ("Weak", "Watch"):
        financial_strength_c = "weak"
    else:
        financial_strength_c = "unavailable"

    # 4. Return outlook
    if base_return_pct > 5:
        return_outlook_c = "positive"
    elif base_return_pct >= -5:
        return_outlook_c = "neutral"
    else:
        return_outlook_c = "negative"

    # --- Signal assignment (rules checked IN ORDER) ---
    if risk_c == "high" or financial_strength_c == "weak" or return_outlook_c == "negative":
        signal = "High Caution"
    elif risk_c == "moderate" and (liquidity_c == "poor" or return_outlook_c == "neutral"):
        signal = "Caution"
    elif risk_c == "low" and (return_outlook_c == "positive" or financial_strength_c == "strong"):
        signal = "Strong Positive"
    elif risk_c == "low" or (return_outlook_c == "positive" and financial_strength_c != "weak"):
        signal = "Positive"
    else:
        signal = "Neutral"

    # --- Confidence score ---
    confidence = 1.0
    if financial_strength_c == "unavailable":
        confidence -= 0.25
    # Check for default/zero numeric inputs
    for val in (risk_score, base_return_pct, volatility, beta, max_drawdown, historical_return_pct):
        if val == 0:
            confidence -= 0.1
    confidence = max(0.2, min(1.0, confidence))

    # --- Data quality note ---
    if financial_strength_c == "unavailable":
        data_quality_note = (
            "Financial health data is not available from public APIs "
            "for CSE stocks. Signal is based on market-price risk "
            "components only."
        )
    else:
        data_quality_note = ""

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "components": {
            "risk": risk_c,
            "liquidity": liquidity_c,
            "financial_strength": financial_strength_c,
            "return_outlook": return_outlook_c,
        },
        "data_quality_note": data_quality_note,
    }


# ---------------------------------------------------------------------------
# Main orchestrator: risk ranking table
# ---------------------------------------------------------------------------

MAX_WORKERS = 8
PRICE_HISTORY_TIMEOUT = 15  # seconds per stock
COMPANY_INFO_TIMEOUT = 10  # seconds per stock


def _call_with_timeout(func, args=None, kwargs=None, timeout=20):
    """Call a function with a strict timeout.

    If the call exceeds *timeout* seconds, or raises any exception,
    ``None`` is returned.  This prevents a single stuck yfinance call
    from blocking the entire ranking pipeline.
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except Exception:
            return None


def _process_single_company(
    company: dict,
    provider,
    horizon_days: int,
    max_retries: int = 2,
) -> dict | None:
    """Process one company for the risk ranking table.

    Parameters
    ----------
    company : dict
        Company dict with at least a ``"symbol"`` key.
    provider : BaseProvider
        Market data provider.
    horizon_days : int
        Number of trading days for scenario projections.
    max_retries : int
        Maximum number of retries for price history download
        (exponential backoff).  Default 2.

    Returns
    -------
    dict | None
        Ranked-stock dict, or ``None`` if the stock could not be processed.
    """
    symbol = company["symbol"]
    name = company.get("name", symbol)

    # --- 1. Price history (with retries & per-call timeout) ---------------
    price_data = None
    for attempt in range(max_retries + 1):
        price_data = _call_with_timeout(
            provider.load_price_history,
            (symbol, "5y"),
            timeout=PRICE_HISTORY_TIMEOUT,
        )
        if price_data is not None and not price_data.empty and len(price_data) >= 20:
            break
        if attempt < max_retries:
            time.sleep(2**attempt)  # 1 s, 2 s

    if price_data is None or price_data.empty or len(price_data) < 20:
        return None

    try:
        price_data = add_indicators(price_data)
    except Exception:
        return None

    # --- 2. Company info (with timeout) -----------------------------------
    company_info = _call_with_timeout(
        provider.load_company_info,
        (symbol,),
        timeout=COMPANY_INFO_TIMEOUT,
    )
    if company_info is None:
        company_info = {}

    # --- 3. Current price & market cap ------------------------------------
    current_price = company.get("price")
    if current_price is None or current_price == 0:
        current_price = float(price_data["Close"].iloc[-1])
    else:
        current_price = float(current_price)

    market_cap = company.get("market_cap")
    if market_cap is None:
        market_cap = company_info.get("marketCap")
    if market_cap is None:
        market_cap = company_info.get("cse_market_cap")
    if market_cap is not None:
        market_cap = float(market_cap)

    # --- 4. Risk score ----------------------------------------------------
    risk = compute_risk_score(price_data, company_info)

    # --- 5. Scenario prices -----------------------------------------------
    scenario = compute_scenario_prices(price_data, horizon_days)

    # --- 6. Risk-adjusted score -------------------------------------------
    risk_adj = compute_risk_adjusted_score(risk, scenario)

    # Format values for output
    hist_return_pct = risk["historical_return"] * 100
    bear_return_pct = scenario["bear"]["return"] * 100
    base_return_pct = scenario["base"]["return"] * 100
    bull_return_pct = scenario["bull"]["return"] * 100

    signal_result = compute_signal(
        risk_score=risk["score"],
        risk_level=risk["level"],
        financial_health=risk["financial_health"],
        base_return_pct=base_return_pct,
        volatility=risk["volatility"],
        beta=risk["beta"],
        max_drawdown=risk["max_drawdown"],
        liquidity_risk=risk["liquidity_risk"],
        historical_return_pct=hist_return_pct,
    )
    signal = signal_result["signal"]
    signal_confidence = signal_result["confidence"]
    signal_components = signal_result["components"]
    data_quality_note = signal_result["data_quality_note"]

    return {
        "company": name,
        "ticker": symbol,
        "sector": "Unknown",
        "current_price": round(current_price, 2),
        "market_cap": round(market_cap, 2) if market_cap else 0.0,
        "risk_score": risk["score"],
        "risk_level": risk["level"],
        "volatility": risk["volatility"],
        "beta": risk["beta"],
        "max_drawdown": risk["max_drawdown"],
        "debt_risk": risk["debt_risk"],
        "liquidity_risk": risk["liquidity_risk"],
        "financial_health": risk["financial_health"],
        "historical_return_pct": round(hist_return_pct, 1),
        "scenario_bear_return_pct": round(bear_return_pct, 1),
        "scenario_base_return_pct": round(base_return_pct, 1),
        "scenario_bull_return_pct": round(bull_return_pct, 1),
        "risk_adjusted_score": risk_adj,
        "signal": signal,
        "signal_confidence": signal_confidence,
        "signal_components": signal_components,
        "data_quality_note": data_quality_note,
    }


def build_risk_ranking_table(
    trading_companies: list[dict],
    market_data_provider,
    horizon_days: int = 252,
    progress_callback: callable = None,
) -> tuple[list[dict], int, int]:
    """Build a risk-ranked table for every trading CSE company.

    For each company this function:
    1. Loads price history via the provider (with timeout & retries).
    2. Loads company info (yfinance + CSE API enhancement).
    3. Computes the comprehensive risk score.
    4. Computes Bear / Base / Bull scenario returns.
    5. Computes the risk-adjusted score.
    6. Determines an investment signal.

    All yfinance calls are performed **concurrently** (up to
    ``MAX_WORKERS`` = 8 parallel downloads) so that ~167 stocks
    complete in seconds rather than minutes.

    Results are sorted by risk score ascending (lowest risk first).

    Parameters
    ----------
    trading_companies : list[dict]
        List of CSE trading company dicts (from ``CseDirectory.all_companies()``).
    market_data_provider : BaseProvider
        A provider instance (typically ``CseProvider``) whose ``load_price_history``
        and ``load_company_info`` methods will be called.
    horizon_days : int
        Number of trading days for scenario projections (default 252 = 1 year).
    progress_callback : callable, optional
        Called after every completed stock as
        ``progress_callback(current: int, total: int, symbol: str)``.
        Can be used by the Streamlit layer to drive a progress bar.

    Returns
    -------
    tuple[list[dict], int, int]
        ``(results, succeeded_count, failed_count)``.
        Each result dict contains rank, company metadata, risk metrics,
        scenario returns, and investment signal.
    """
    results: list[dict] = []
    succeeded = 0
    failed = 0
    total = len(trading_companies)
    completed = 0

    if total == 0:
        return results, 0, 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all companies at once — the bounded thread pool prevents
        # more than MAX_WORKERS concurrent downloads.
        future_to_company: dict = {}
        for company in trading_companies:
            future = executor.submit(
                _process_single_company, company, market_data_provider, horizon_days
            )
            future_to_company[future] = company

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_company):
            company = future_to_company[future]
            try:
                result = future.result(timeout=PRICE_HISTORY_TIMEOUT + 5)
                if result is not None:
                    results.append(result)
                    succeeded += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

            completed += 1
            if progress_callback is not None:
                try:
                    progress_callback(completed, total, company.get("symbol", ""))
                except Exception:
                    pass

            # Brief pause every batch to avoid hammering Yahoo Finance
            if completed % MAX_WORKERS == 0:
                time.sleep(0.1)

    # Sort by risk score ascending (lowest risk first)
    results.sort(key=lambda x: x["risk_score"])

    # Assign ordinal ranks
    for i, entry in enumerate(results, start=1):
        entry["rank"] = i

    return results, succeeded, failed


# ---------------------------------------------------------------------------
# Portfolio allocation
# ---------------------------------------------------------------------------

def _get_scenario_price_from_ranked_stock(stock: dict, scenario: str) -> float:
    """Derive a scenario price from a ranked stock entry's return percentages."""
    current_price = stock["current_price"]
    if scenario == "bear":
        ret = stock.get("scenario_bear_return_pct", 0.0) / 100.0
    elif scenario == "base":
        ret = stock.get("scenario_base_return_pct", 0.0) / 100.0
    elif scenario == "bull":
        ret = stock.get("scenario_bull_return_pct", 0.0) / 100.0
    else:
        ret = 0.0
    return current_price * (1.0 + ret)


def _empty_portfolio(style: str, investment_amount: float) -> dict:
    """Return an empty portfolio structure (no stocks matched)."""
    style_label = style.replace("_", " ").title()
    return {
        "style": f"{style_label} Portfolio",
        "stocks": [],
        "total_invested": 0.0,
        "cash_remaining": round(investment_amount, 2),
        "risk_score": 0.0,
        "bear_value": 0.0,
        "base_value": 0.0,
        "bull_value": 0.0,
    }


def build_portfolio_allocation(
    investment_amount: float,
    ranked_stocks: list[dict],
    style: str,
) -> dict:
    """Build a diversified portfolio allocation for a given investment style.

    Styles
    ------
    **lower_risk**
        Top 5 lowest-risk stocks, weighted inversely by risk score.
    **balanced**
        Top 8 stocks, equal-weighted (mix of lower and moderate risk).
    **growth**
        Top 5 stocks with highest risk-adjusted return among those with
        risk score < 50.

    Parameters
    ----------
    investment_amount : float
        Total capital to deploy across the portfolio.
    ranked_stocks : list[dict]
        Risk-ranked stock list from :func:`build_risk_ranking_table`.
    style : str
        One of ``"lower_risk"``, ``"balanced"``, ``"growth"``.

    Returns
    -------
    dict
        Portfolio allocation with stock breakdown, risk score, and
        scenario values.
    """
    style = style.strip().lower()

    if style == "lower_risk":
        candidates = ranked_stocks[:5]
        if not candidates:
            return _empty_portfolio(style, investment_amount)

        # Weight by inverse risk score (lower risk → higher allocation)
        total_inverse = sum(max(1.0, 100.0 - s["risk_score"]) for s in candidates)
        alloc_pcts = []
        for s in candidates:
            inverse = max(1.0, 100.0 - s["risk_score"])
            alloc_pcts.append((inverse / total_inverse) * 100.0)

    elif style == "balanced":
        candidates = ranked_stocks[:8]
        if not candidates:
            return _empty_portfolio(style, investment_amount)
        eq = 100.0 / len(candidates)
        alloc_pcts = [eq] * len(candidates)

    elif style == "growth":
        # Moderate-low risk (score < 50), highest risk-adjusted return
        moderate_low = [s for s in ranked_stocks if s["risk_score"] < 50]
        candidates = sorted(
            moderate_low, key=lambda x: -x["risk_adjusted_score"]
        )[:5]
        if not candidates:
            return _empty_portfolio(style, investment_amount)
        eq = 100.0 / len(candidates)
        alloc_pcts = [eq] * len(candidates)

    else:
        raise ValueError(
            f"Unknown portfolio style: '{style}'. "
            "Use 'lower_risk', 'balanced', or 'growth'."
        )

    stock_entries: list[dict] = []
    risk_scores: list[float] = []
    weights: list[float] = []

    for stock, alloc_pct in zip(candidates, alloc_pcts):
        amount = investment_amount * (alloc_pct / 100.0)
        inv = calculate_investment(amount, stock["current_price"])
        stock_entries.append(
            {
                "ticker": stock["ticker"],
                "company": stock["company"],
                "allocation_pct": round(alloc_pct, 2),
                "amount_invested": inv["actual_invested"],
                "shares": inv["shares"],
                "share_price": inv["share_price"],
                "cash_remaining": inv["cash_remaining"],
            }
        )
        risk_scores.append(stock["risk_score"])
        weights.append(alloc_pct)

    total_invested = sum(e["amount_invested"] for e in stock_entries)

    # Portfolio-level risk score (weighted by allocation pct)
    portfolio_risk = compute_portfolio_risk_score(risk_scores, weights)

    # Aggregate scenario values
    bear_value = sum(
        e["shares"] * _get_scenario_price_from_ranked_stock(
            candidates[i], "bear"
        ) + e["cash_remaining"]
        for i, e in enumerate(stock_entries)
    )
    base_value = sum(
        e["shares"] * _get_scenario_price_from_ranked_stock(
            candidates[i], "base"
        ) + e["cash_remaining"]
        for i, e in enumerate(stock_entries)
    )
    bull_value = sum(
        e["shares"] * _get_scenario_price_from_ranked_stock(
            candidates[i], "bull"
        ) + e["cash_remaining"]
        for i, e in enumerate(stock_entries)
    )

    style_label = style.replace("_", " ").title()

    return {
        "style": f"{style_label} Portfolio",
        "stocks": stock_entries,
        "total_invested": round(total_invested, 2),
        "cash_remaining": round(investment_amount - total_invested, 2),
        "risk_score": portfolio_risk,
        "bear_value": round(bear_value, 2),
        "base_value": round(base_value, 2),
        "bull_value": round(bull_value, 2),
    }
