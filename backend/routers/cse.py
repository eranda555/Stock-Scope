"""CSE (Colombo Stock Exchange) router.

Exposes endpoints backed by the existing cse_data.py and markets.py modules.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import APIRouter, HTTPException, Query

from cse_data import CSE_DIRECTORY, fetch_live_trade_summary

router = APIRouter()


@router.get("/companies")
async def search_companies(
    query: str = Query("", description="Search query (name, symbol, or code)"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search CSE companies by name, symbol, or security code."""
    if not query.strip():
        companies = CSE_DIRECTORY.all_companies(only_trading=True)
        return {"count": len(companies), "companies": companies[:limit]}

    results = CSE_DIRECTORY.search(query, limit=limit)
    return {"count": len(results), "companies": results}


@router.get("/market-overview")
async def market_overview():
    """Fetch live CSE market summary (advancers, decliners, volume, etc.)."""
    try:
        companies_live, market_summary = fetch_live_trade_summary()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    trading = [c for c in companies_live if c.get("status") == 0]
    advancers = [c for c in trading if (c.get("change") or 0) > 0]
    decliners = [c for c in trading if (c.get("change") or 0) < 0]

    total_market_cap = sum(c.get("marketCap") or 0 for c in trading)
    total_volume = sum(c.get("sharevolume") or 0 for c in trading)
    total_turnover = sum(c.get("turnover") or 0 for c in trading)

    # Top movers
    sorted_gainers = sorted(trading, key=lambda c: -(c.get("percentageChange") or 0))[:10]
    sorted_losers = sorted(trading, key=lambda c: (c.get("percentageChange") or 0))[:10]
    sorted_active = sorted(trading, key=lambda c: -(c.get("sharevolume") or 0))[:10]

    def _sanitize_company(c: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": c.get("symbol", ""),
            "name": c.get("name", ""),
            "price": c.get("price"),
            "change": c.get("change"),
            "percentageChange": c.get("percentageChange"),
            "sharevolume": c.get("sharevolume"),
            "turnover": c.get("turnover"),
            "marketCap": c.get("marketCap"),
            "status": c.get("status"),
        }

    return {
        "summary": {
            "companiesTrading": len(trading),
            "advancers": len(advancers),
            "decliners": len(decliners),
            "totalVolume": total_volume,
            "totalMarketCap": total_market_cap,
            "totalTurnover": total_turnover,
        },
        "gainers": [_sanitize_company(c) for c in sorted_gainers],
        "losers": [_sanitize_company(c) for c in sorted_losers],
        "mostActive": [_sanitize_company(c) for c in sorted_active],
        "rawMarketSummary": market_summary,
    }


@router.get("/company/{symbol}")
async def company_detail(symbol: str):
    """Fetch detailed information for a specific CSE company."""
    # Try to find the company in the directory
    company = CSE_DIRECTORY.get_by_symbol(symbol)
    if company is None:
        company = CSE_DIRECTORY.get_by_security_code(symbol)
    if company is None:
        results = CSE_DIRECTORY.search(symbol, limit=1)
        if results:
            company = results[0]

    if company is None:
        raise HTTPException(status_code=404, detail=f"CSE company not found: {symbol}")

    # Get live data if available
    try:
        companies_live, _ = fetch_live_trade_summary()
        live_map = {c.get("symbol", "").upper(): c for c in companies_live}
        live = live_map.get(company["symbol"].upper(), {})
    except RuntimeError:
        live = {}

    sector_name = CSE_DIRECTORY.get_sector_name(company.get("sector_id"))
    status_label = CSE_DIRECTORY.get_status_label(company.get("status", 0))

    return {
        "symbol": company["symbol"],
        "name": company["name"],
        "yfinance_symbol": company.get("yfinance_symbol"),
        "sector": sector_name,
        "status": status_label,
        "status_code": company.get("status", 0),
        "price": live.get("price") or company.get("price"),
        "change": live.get("change"),
        "percentageChange": live.get("percentageChange"),
        "marketCap": live.get("marketCap") or company.get("market_cap"),
        "shareVolume": live.get("sharevolume"),
        "turnover": live.get("turnover"),
        "52wHigh": live.get("p12HiPrice"),
        "52wLow": live.get("p12LowPrice"),
        "previousClose": live.get("previousClose"),
        "open": live.get("open"),
        "high": live.get("hiTrade"),
        "low": live.get("lowTrade"),
    }
