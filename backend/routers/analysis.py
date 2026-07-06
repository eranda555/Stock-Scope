"""Analysis router.

Performs financial health, valuation, risk, scenario, and technical analysis
using the existing stock_utils.py functions.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# These imports re-use the existing analysis functions
from stock_utils import (
    add_indicators,
    build_financial_health,
    build_risk_snapshot,
    build_scenario_projection,
    build_valuation_snapshot,
    forecast_prices,
    summarize,
)

router = APIRouter()


# ──────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────


class FinancialHealthRequest(BaseModel):
    company_info: dict[str, Any]
    currency_code: str = "USD"


class FinancialHealthResponse(BaseModel):
    label: str
    score: float
    explanation: str
    metrics: dict[str, str]


class ValuationRequest(BaseModel):
    company_info: dict[str, Any]
    current_price: float


class ValuationResponse(BaseModel):
    label: str
    score: float
    explanation: str
    current_price: float
    estimated_fair_value: float
    upside_pct: float
    metrics: dict[str, str]


class RiskRequest(BaseModel):
    price_history: list[dict[str, Any]]
    company_info: dict[str, Any]


class RiskResponse(BaseModel):
    label: str
    score: float
    explanation: str
    metrics: dict[str, str]


class ScenarioRequest(BaseModel):
    price_history: list[dict[str, Any]]
    forecast_days: int = 30
    currency_code: str = "USD"


class ScenarioResponse(BaseModel):
    base_label: str
    summary: dict[str, str]
    base_path: list[dict[str, Any]]
    bull_path: list[dict[str, Any]]
    bear_path: list[dict[str, Any]]


class TechnicalRequest(BaseModel):
    price_history: list[dict[str, Any]]


class TechnicalResponse(BaseModel):
    stats: dict[str, float | str]
    indicators: list[dict[str, Any]]


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _dict_to_dataframe(records: list[dict[str, Any]]) -> Any:
    """Convert a list of dicts back to a pandas DataFrame."""
    import pandas as pd

    df = pd.DataFrame(records)
    # Ensure Date column is datetime
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
    return df


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────


@router.post("/financial-health", response_model=FinancialHealthResponse)
async def financial_health(body: FinancialHealthRequest):
    """Score a company's financial health based on balance-sheet metrics."""
    try:
        result = build_financial_health(
            body.company_info, currency_code=body.currency_code
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Analysis failed: {exc}")

    return FinancialHealthResponse(
        label=result.label,
        score=result.score,
        explanation=result.explanation,
        metrics=result.metrics,
    )


@router.post("/valuation", response_model=ValuationResponse)
async def valuation(body: ValuationRequest):
    """Estimate fair value and assess whether the stock looks cheap or expensive."""
    try:
        result = build_valuation_snapshot(body.company_info, body.current_price)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Analysis failed: {exc}")

    return ValuationResponse(
        label=result.label,
        score=result.score,
        explanation=result.explanation,
        current_price=result.current_price,
        estimated_fair_value=result.estimated_fair_value,
        upside_pct=result.upside_pct,
        metrics=result.metrics,
    )


@router.post("/risk", response_model=RiskResponse)
async def risk(body: RiskRequest):
    """Calculate risk metrics: volatility, drawdown, beta, and debt/equity."""
    try:
        data = _dict_to_dataframe(body.price_history)
        result = build_risk_snapshot(data, body.company_info)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Analysis failed: {exc}")

    return RiskResponse(
        label=result.label,
        score=result.score,
        explanation=result.explanation,
        metrics=result.metrics,
    )


@router.post("/scenario", response_model=ScenarioResponse)
async def scenario(body: ScenarioRequest):
    """Generate bull / base / bear scenario projections."""
    try:
        data = _dict_to_dataframe(body.price_history)
        forecast = forecast_prices(data, days=body.forecast_days)
        result = build_scenario_projection(data, forecast, currency_code=body.currency_code)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Scenario failed: {exc}")

    def _path_to_list(path: Any) -> list[dict[str, Any]]:
        import pandas as pd
        records = []
        for _, row in path.iterrows():
            rec: dict[str, Any] = {}
            for col in path.columns:
                val = row[col]
                if isinstance(val, pd.Timestamp):
                    rec[str(col)] = val.isoformat()
                elif hasattr(val, "item"):
                    rec[str(col)] = val.item()
                else:
                    rec[str(col)] = val
            records.append(rec)
        return records

    return ScenarioResponse(
        base_label=result.base_label,
        summary=result.summary,
        base_path=_path_to_list(result.base_path),
        bull_path=_path_to_list(result.bull_path),
        bear_path=_path_to_list(result.bear_path),
    )


@router.post("/technical", response_model=TechnicalResponse)
async def technical(body: TechnicalRequest):
    """Calculate technical indicators (SMA, MACD, RSI) and summary statistics."""
    try:
        data = _dict_to_dataframe(body.price_history)
        enriched = add_indicators(data)
        stats = summarize(enriched)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Technical analysis failed: {exc}")

    # Convert enriched DataFrame to list of dicts
    import pandas as pd
    indicators_list: list[dict[str, Any]] = []
    for _, row in enriched.iterrows():
        rec: dict[str, Any] = {}
        for col in enriched.columns:
            val = row[col]
            if isinstance(val, pd.Timestamp):
                rec[str(col)] = val.isoformat()
            elif hasattr(val, "item"):
                rec[str(col)] = val.item()
            else:
                rec[str(col)] = val
        indicators_list.append(rec)

    return TechnicalResponse(
        stats={k: v for k, v in stats.items()},
        indicators=indicators_list,
    )
