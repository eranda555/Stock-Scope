"""Stock data router.

Provides price history, company info, profile, and news endpoints
backed by the providers.py and stock_utils.py modules.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
from typing import Any

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import APIRouter, HTTPException, Query

from markets import MARKET_CSE, MARKET_US
from providers import get_provider
from stock_utils import add_indicators, summarize, load_company_news

router = APIRouter()


def _resolve_ticker(market: str, ticker: str) -> tuple[str, str]:
    """Resolve a display ticker to a provider ticker and get the market type.

    Returns (provider_ticker, market_label).
    """
    market_key = market.strip().upper()
    if market_key not in (MARKET_CSE, MARKET_US):
        raise HTTPException(status_code=400, detail=f"Unsupported market: {market}")

    # For CSE, we pass ticker as-is — the CseProvider handles transformation internally.
    # For US, ticker is used directly by YFinanceProvider.
    return ticker.strip().upper(), market_key


@router.get("/{market}/{ticker}/price-history")
async def get_price_history(
    market: str,
    ticker: str,
    period: str = Query("5y", description="History window: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    include_indicators: bool = Query(True, description="Include technical indicators"),
    include_stats: bool = Query(True, description="Include summary statistics"),
):
    """Fetch price history with optional technical indicators and summary stats."""
    try:
        provider_ticker, _ = _resolve_ticker(market, ticker)
        provider = get_provider(market)
        raw_data = provider.load_price_history(provider_ticker, period)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load price history: {exc}")

    if include_indicators:
        data = add_indicators(raw_data)
    else:
        data = raw_data

    # Convert DataFrame to list of dicts (JSON-serializable)
    records: list[dict[str, Any]] = []
    for _, row in data.iterrows():
        record: dict[str, Any] = {}
        for col in data.columns:
            val = row[col]
            if isinstance(val, datetime):
                record[str(col)] = val.isoformat()
            elif hasattr(val, "item"):
                record[str(col)] = val.item()
            else:
                record[str(col)] = val
        records.append(record)

    result: dict[str, Any] = {
        "ticker": ticker.upper(),
        "market": market.upper(),
        "period": period,
        "dataPoints": len(records),
        "records": records,
    }

    if include_stats:
        try:
            stats = summarize(data)
            result["stats"] = {k: v for k, v in stats.items()}
        except Exception:
            result["stats"] = {}

    return result


@router.get("/{market}/{ticker}/info")
async def get_company_info(market: str, ticker: str):
    """Fetch fundamental company information."""
    try:
        provider_ticker, _ = _resolve_ticker(market, ticker)
        provider = get_provider(market)
        info = provider.load_company_info(provider_ticker)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load company info: {exc}")

    # Return a curated subset of the full info dict
    keys_of_interest = [
        "longName", "shortName", "sector", "industry", "country",
        "marketCap", "enterpriseValue", "trailingPE", "forwardPE",
        "priceToBook", "priceToSalesTrailing12Months", "pegRatio",
        "trailingEps", "forwardEps", "dividendYield", "payoutRatio",
        "beta", "bookValue", "revenueGrowth", "earningsGrowth",
        "profitMargins", "operatingMargins", "returnOnAssets",
        "returnOnEquity", "currentRatio", "debtToEquity",
        "freeCashflow", "operatingCashflow", "revenuePerShare",
        "targetMeanPrice", "targetHighPrice", "targetLowPrice",
        "recommendationKey", "numberOfAnalystOpinions",
        "52WeekChange", "SandP52WeekChange",
        # CSE-specific fields injected by CseProvider
        "cse_last_traded_price", "cse_change", "cse_change_pct",
        "cse_market_cap", "cse_52w_high", "cse_52w_low",
        "cse_volume", "cse_turnover", "cse_previous_close",
        "cse_open", "cse_high", "cse_low", "cse_beta",
    ]
    curated: dict[str, Any] = {}
    for key in keys_of_interest:
        if key in info:
            val = info[key]
            if isinstance(val, float) and (val != val):  # NaN check
                continue
            curated[key] = val

    curated["ticker"] = ticker.upper()
    curated["market"] = market.upper()
    return curated


@router.get("/{market}/{ticker}/profile")
async def get_company_profile(market: str, ticker: str):
    """Fetch company profile (name, sector, industry, country, market cap)."""
    try:
        provider_ticker, _ = _resolve_ticker(market, ticker)
        provider = get_provider(market)
        profile = provider.load_company_profile(provider_ticker)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load company profile: {exc}")

    profile["ticker"] = ticker.upper()
    profile["market"] = market.upper()
    return profile


@router.get("/{market}/{ticker}/news")
async def get_company_news(
    market: str,
    ticker: str,
    limit: int = Query(6, ge=1, le=20),
):
    """Fetch recent company news with sentiment analysis."""
    try:
        provider_ticker, _ = _resolve_ticker(market, ticker)
        provider = get_provider(market)
        news = provider.load_company_news(provider_ticker, limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load news: {exc}")

    articles: list[dict[str, Any]] = []
    for article in news.articles:
        published = article.get("published")
        articles.append({
            "title": article.get("title", ""),
            "publisher": article.get("publisher", "Unknown"),
            "summary": article.get("summary", ""),
            "link": article.get("link", ""),
            "published": published.isoformat() if hasattr(published, "isoformat") else str(published),
            "sentiment": article.get("sentiment", 0.0),
        })

    return {
        "ticker": ticker.upper(),
        "market": market.upper(),
        "averageScore": news.average_score,
        "label": news.label,
        "articles": articles,
    }
