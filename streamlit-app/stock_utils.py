from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from markets import (
    MARKET_CSE,
    MARKET_US,
    format_money,
    money_hover_format,
)
from providers import get_provider


@dataclass
class PredictionResult:
    forecast_dates: list[str]
    forecast_values: list[float]
    slope: float
    score: float


@dataclass
class NewsSentimentResult:
    articles: list[dict[str, Any]]
    average_score: float
    label: str


@dataclass
class ComparisonResult:
    stock_label: str
    benchmark_label: str
    comparison: pd.DataFrame
    stock_return_pct: float
    benchmark_return_pct: float
    relative_return_pct: float
    correlation: float


@dataclass
class FinancialHealthResult:
    label: str
    score: float
    explanation: str
    metrics: dict[str, str]


@dataclass
class ValuationResult:
    label: str
    score: float
    explanation: str
    current_price: float
    estimated_fair_value: float
    upside_pct: float
    metrics: dict[str, str]


@dataclass
class RiskResult:
    label: str
    score: float
    explanation: str
    metrics: dict[str, str]


@dataclass
class ScenarioResult:
    base_label: str
    base_path: pd.DataFrame
    bull_path: pd.DataFrame
    bear_path: pd.DataFrame
    summary: dict[str, str]


POSITIVE_WORDS = {
    "beat",
    "benefit",
    "bull",
    "bullish",
    "growth",
    "gain",
    "improve",
    "increase",
    "outperform",
    "profit",
    "rally",
    "record",
    "resilient",
    "strong",
    "up",
    "upgrade",
}

NEGATIVE_WORDS = {
    "bear",
    "bearish",
    "concern",
    "decline",
    "drop",
    "fall",
    "loss",
    "negative",
    "risk",
    "slowdown",
    "weak",
    "warning",
    "down",
    "downgrade",
    "miss",
}

SECTOR_BENCHMARKS = {
    "Basic Materials": "XLB",
    "Communication Services": "XLC",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Industrials": "XLI",
    "Real Estate": "XLRE",
    "Technology": "XLK",
    "Utilities": "XLU",
}


PRICE_COLUMN_MAP = {
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "adj close": "Adj Close",
    "volume": "Volume",
    "date": "Date",
    "index": "Date",
}


def _normalize_yfinance_columns(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    normalized = data.copy()
    ticker_upper = ticker.upper()

    def resolve_column(column: Any) -> str:
        if not isinstance(column, tuple):
            column_text = str(column).strip()
            return PRICE_COLUMN_MAP.get(column_text.lower(), column_text)

        parts = [str(part).strip() for part in column if part is not None and str(part).strip()]
        for part in parts:
            canonical_name = PRICE_COLUMN_MAP.get(part.lower())
            if canonical_name:
                return canonical_name

        non_ticker_parts = [part for part in parts if part.upper() != ticker_upper]
        if non_ticker_parts:
            return non_ticker_parts[0]
        if parts:
            return parts[0]
        return ""

    normalized.columns = [resolve_column(column) for column in normalized.columns]
    normalized = normalized.reset_index()
    normalized.columns = [resolve_column(column) for column in normalized.columns]

    rename_map = {
        column: PRICE_COLUMN_MAP[str(column).strip().lower()]
        for column in normalized.columns
        if str(column).strip().lower() in PRICE_COLUMN_MAP
    }
    normalized = normalized.rename(columns=rename_map)

    if "Close" not in normalized.columns and "Adj Close" in normalized.columns:
        normalized["Close"] = normalized["Adj Close"]

    required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    missing_columns = [column for column in required_columns if column not in normalized.columns]
    if missing_columns:
        raise ValueError(f"Expected price history columns {', '.join(missing_columns)} for {ticker_upper}")

    return normalized


def load_price_history(ticker: str, period: str = "5y") -> pd.DataFrame:
    data = yf.download(ticker, period=period, auto_adjust=False, progress=False)
    if data.empty:
        raise ValueError(f"No price data found for {ticker.upper()}")

    data = _normalize_yfinance_columns(data, ticker)

    numeric_columns = [column for column in ["Open", "High", "Low", "Close", "Adj Close", "Volume"] if column in data.columns]
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=["Close"]).copy()
    return data


def load_company_profile(ticker: str) -> dict[str, Any]:
    info = load_company_info(ticker)
    return {
        "name": info.get("longName") or info.get("shortName") or ticker.upper(),
        "sector": info.get("sector") or "Unknown",
        "industry": info.get("industry") or "Unknown",
        "market_cap": info.get("marketCap"),
        "country": info.get("country") or "Unknown",
    }


def load_company_info(ticker: str) -> dict[str, Any]:
    try:
        info = yf.Ticker(ticker).info or {}
        if isinstance(info, dict):
            return info
    except Exception:
        pass
    return {}


def _safe_float(value: Any) -> float | None:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None
    if np.isfinite(numeric_value):
        return numeric_value
    return None


def _format_percent(value: float | None) -> str:
    if value is None:
        return "Not available"
    return f"{value:.1f}%"


def _format_ratio(value: float | None) -> str:
    if value is None:
        return "Not available"
    return f"{value:.2f}"


def _format_currency(value: float | None, currency_code: str = "USD") -> str:
    if value is None:
        return "Not available"
    return format_money(value, currency_code, compact=True)


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.rolling(window=period).mean()
    average_loss = loss.rolling(window=period).mean()
    relative_strength = average_gain / average_loss.replace(0, np.nan)
    return 100 - (100 / (1 + relative_strength))


def calculate_macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    enriched = data.copy()
    enriched["SMA20"] = enriched["Close"].rolling(window=20).mean()
    enriched["SMA50"] = enriched["Close"].rolling(window=50).mean()
    enriched["EMA12"] = enriched["Close"].ewm(span=12, adjust=False).mean()
    enriched["EMA26"] = enriched["Close"].ewm(span=26, adjust=False).mean()
    macd, signal, histogram = calculate_macd(enriched["Close"])
    enriched["MACD"] = macd
    enriched["MACD Signal"] = signal
    enriched["MACD Histogram"] = histogram
    enriched["RSI14"] = calculate_rsi(enriched["Close"])
    enriched["Daily Return %"] = enriched["Close"].pct_change() * 100
    return enriched


def summarize(data: pd.DataFrame) -> dict[str, float | str]:
    latest = data.iloc[-1]
    first = data.iloc[0]
    close_series = data["Close"]
    daily_return = data["Daily Return %"].dropna()

    average_volume = float(data["Volume"].dropna().mean()) if "Volume" in data.columns else 0.0
    volatility = float(close_series.pct_change().dropna().std() * 100)
    change_pct = float(((latest["Close"] - first["Close"]) / first["Close"]) * 100)

    return {
        "latest_close": float(latest["Close"]),
        "52w_high": float(close_series.max()),
        "52w_low": float(close_series.min()),
        "avg_daily_return": float(daily_return.mean()) if not daily_return.empty else 0.0,
        "volatility": volatility,
        "change_pct": change_pct,
        "average_volume": average_volume,
        "rsi14": float(latest["RSI14"]) if pd.notna(latest.get("RSI14")) else 0.0,
        "macd": float(latest["MACD"]) if pd.notna(latest.get("MACD")) else 0.0,
        "macd_signal": float(latest["MACD Signal"]) if pd.notna(latest.get("MACD Signal")) else 0.0,
    }


def _feature_frame(data: pd.DataFrame) -> pd.DataFrame:
    enriched = add_indicators(data)
    enriched["Close Lag 1"] = enriched["Close"].shift(1)
    enriched["Close Lag 5"] = enriched["Close"].shift(5)
    enriched["Target"] = enriched["Close"].shift(-1)
    feature_columns = ["Close", "Close Lag 1", "Close Lag 5", "SMA20", "SMA50", "RSI14", "MACD", "MACD Signal", "MACD Histogram", "Volume"]
    frame = enriched.dropna(subset=feature_columns + ["Target"]).copy()
    return frame[["Date"] + feature_columns + ["Target"]]


def _next_business_day(date_value: pd.Timestamp) -> pd.Timestamp:
    return pd.bdate_range(start=date_value + pd.tseries.offsets.BDay(1), periods=1)[0]


def forecast_prices(data: pd.DataFrame, days: int = 30) -> PredictionResult:
    if len(data) < 60:
        raise ValueError("Need at least 60 rows of data for the indicator-based forecast")

    frame = _feature_frame(data)
    feature_columns = [column for column in frame.columns if column not in {"Date", "Target"}]
    model = LinearRegression()
    model.fit(frame[feature_columns], frame["Target"])
    score = float(r2_score(frame["Target"], model.predict(frame[feature_columns])))

    history = data.copy()
    forecast_dates: list[str] = []
    forecast_values: list[float] = []

    for _ in range(days):
        enriched_history = add_indicators(history)
        last_row = enriched_history.iloc[-1]
        feature_row = pd.DataFrame([
            {
                "Close": float(last_row["Close"]),
                "Close Lag 1": float(enriched_history["Close"].iloc[-2]) if len(enriched_history) > 1 else float(last_row["Close"]),
                "Close Lag 5": float(enriched_history["Close"].iloc[-6]) if len(enriched_history) > 5 else float(last_row["Close"]),
                "SMA20": float(last_row["SMA20"]) if pd.notna(last_row["SMA20"]) else float(last_row["Close"]),
                "SMA50": float(last_row["SMA50"]) if pd.notna(last_row["SMA50"]) else float(last_row["Close"]),
                "RSI14": float(last_row["RSI14"]) if pd.notna(last_row["RSI14"]) else 50.0,
                "MACD": float(last_row["MACD"]) if pd.notna(last_row["MACD"]) else 0.0,
                "MACD Signal": float(last_row["MACD Signal"]) if pd.notna(last_row["MACD Signal"]) else 0.0,
                "MACD Histogram": float(last_row["MACD Histogram"]) if pd.notna(last_row["MACD Histogram"]) else 0.0,
                "Volume": float(last_row["Volume"]) if pd.notna(last_row.get("Volume")) else 0.0,
            }
        ])
        predicted_close = float(model.predict(feature_row)[0])
        next_date = _next_business_day(pd.to_datetime(history["Date"].iloc[-1]))

        forecast_dates.append(next_date.strftime("%Y-%m-%d"))
        forecast_values.append(predicted_close)

        synthetic_row = history.iloc[-1].copy()
        synthetic_row["Date"] = next_date
        synthetic_row["Open"] = predicted_close
        synthetic_row["High"] = predicted_close
        synthetic_row["Low"] = predicted_close
        synthetic_row["Close"] = predicted_close
        if "Adj Close" in synthetic_row.index:
            synthetic_row["Adj Close"] = predicted_close
        history = pd.concat([history, pd.DataFrame([synthetic_row])], ignore_index=True)

    return PredictionResult(
        forecast_dates=forecast_dates,
        forecast_values=forecast_values,
        slope=float(model.coef_[0]),
        score=score,
    )


def sector_benchmark_ticker(sector: str) -> str:
    return SECTOR_BENCHMARKS.get(sector, "SPY")


def compare_with_benchmark(stock_data: pd.DataFrame, benchmark_data: pd.DataFrame, stock_label: str, benchmark_label: str) -> ComparisonResult:
    stock = stock_data[["Date", "Close"]].copy().rename(columns={"Close": stock_label})
    benchmark = benchmark_data[["Date", "Close"]].copy().rename(columns={"Close": benchmark_label})
    comparison = pd.merge(stock, benchmark, on="Date", how="inner")
    comparison[stock_label] = comparison[stock_label] / comparison[stock_label].iloc[0] * 100
    comparison[benchmark_label] = comparison[benchmark_label] / comparison[benchmark_label].iloc[0] * 100

    stock_return_pct = float(comparison[stock_label].iloc[-1] - 100)
    benchmark_return_pct = float(comparison[benchmark_label].iloc[-1] - 100)
    relative_return_pct = float(stock_return_pct - benchmark_return_pct)
    correlation = float(comparison[[stock_label, benchmark_label]].pct_change().corr().iloc[0, 1])

    return ComparisonResult(
        stock_label=stock_label,
        benchmark_label=benchmark_label,
        comparison=comparison,
        stock_return_pct=stock_return_pct,
        benchmark_return_pct=benchmark_return_pct,
        relative_return_pct=relative_return_pct,
        correlation=correlation,
    )


def build_financial_health(info: dict[str, Any], currency_code: str = "USD") -> FinancialHealthResult:
    current_ratio = _safe_float(info.get("currentRatio"))
    debt_to_equity = _safe_float(info.get("debtToEquity"))
    operating_margin = _safe_float(info.get("operatingMargins"))
    profit_margin = _safe_float(info.get("profitMargins"))
    return_on_assets = _safe_float(info.get("returnOnAssets"))
    revenue_growth = _safe_float(info.get("revenueGrowth"))
    earnings_growth = _safe_float(info.get("earningsGrowth"))
    free_cashflow = _safe_float(info.get("freeCashflow"))

    score = 0.0
    score += 1 if current_ratio is not None and current_ratio >= 1.5 else 0
    score += 1 if debt_to_equity is not None and debt_to_equity <= 150 else 0
    score += 1 if operating_margin is not None and operating_margin >= 0.15 else 0
    score += 1 if profit_margin is not None and profit_margin >= 0.10 else 0
    score += 1 if return_on_assets is not None and return_on_assets >= 0.05 else 0
    score += 1 if (revenue_growth is not None and revenue_growth > 0) or (earnings_growth is not None and earnings_growth > 0) else 0

    if score >= 5:
        label = "Healthy"
        explanation = "The company looks financially solid, with enough cushion and decent profitability."
    elif score >= 3:
        label = "Mixed"
        explanation = "The company has some strengths, but one or two balance-sheet or profitability checks need attention."
    else:
        label = "Watch"
        explanation = "The business may be more fragile, so it is worth looking closer at debt and profit trends."

    metrics = {
        "Cash cushion": _format_ratio(current_ratio),
        "Debt load": _format_ratio(debt_to_equity),
        "Operating margin": _format_percent(operating_margin * 100 if operating_margin is not None else None),
        "Profit margin": _format_percent(profit_margin * 100 if profit_margin is not None else None),
        "Returns on assets": _format_percent(return_on_assets * 100 if return_on_assets is not None else None),
        "Free cash flow": _format_currency(free_cashflow, currency_code),
    }

    return FinancialHealthResult(label=label, score=score / 6, explanation=explanation, metrics=metrics)


def build_valuation_snapshot(info: dict[str, Any], current_price: float) -> ValuationResult:
    trailing_pe = _safe_float(info.get("trailingPE"))
    forward_pe = _safe_float(info.get("forwardPE"))
    price_to_book = _safe_float(info.get("priceToBook"))
    price_to_sales = _safe_float(info.get("priceToSalesTrailing12Months"))
    peg_ratio = _safe_float(info.get("pegRatio"))
    trailing_eps = _safe_float(info.get("trailingEps"))
    target_mean_price = _safe_float(info.get("targetMeanPrice"))

    estimated_fair_value = target_mean_price
    if estimated_fair_value is None and trailing_eps is not None and forward_pe is not None:
        estimated_fair_value = trailing_eps * forward_pe
    if estimated_fair_value is None and trailing_eps is not None and trailing_pe is not None:
        estimated_fair_value = trailing_eps * trailing_pe
    if estimated_fair_value is None:
        estimated_fair_value = current_price

    upside_pct = ((estimated_fair_value - current_price) / current_price) * 100 if current_price else 0.0

    score = 0.0
    score += 1 if trailing_pe is not None and trailing_pe < 20 else 0
    score += 1 if forward_pe is not None and forward_pe < 20 else 0
    score += 1 if peg_ratio is not None and peg_ratio < 2 else 0
    score += 1 if price_to_book is not None and price_to_book < 8 else 0
    score += 1 if upside_pct >= 10 else 0

    if score >= 4:
        label = "Looks attractive"
        explanation = "The market price may be below what the business could reasonably be worth."
    elif score >= 2:
        label = "Fair value"
        explanation = "The stock does not look obviously cheap or expensive at the moment."
    else:
        label = "Looks expensive"
        explanation = "The market is asking for a premium, so there may be less room for disappointment."

    metrics = {
        "P/E": _format_ratio(trailing_pe),
        "Forward P/E": _format_ratio(forward_pe),
        "Price / Book": _format_ratio(price_to_book),
        "Price / Sales": _format_ratio(price_to_sales),
        "PEG": _format_ratio(peg_ratio),
        "Upside to fair value": _format_percent(upside_pct),
    }

    return ValuationResult(
        label=label,
        score=score / 5,
        explanation=explanation,
        current_price=current_price,
        estimated_fair_value=estimated_fair_value,
        upside_pct=upside_pct,
        metrics=metrics,
    )


def build_risk_snapshot(data: pd.DataFrame, info: dict[str, Any]) -> RiskResult:
    daily_returns = data["Close"].pct_change().dropna()
    volatility = float(daily_returns.std() * np.sqrt(252) * 100) if not daily_returns.empty else 0.0
    max_drawdown = 0.0
    if not data.empty:
        running_high = data["Close"].cummax()
        drawdown = (data["Close"] / running_high - 1) * 100
        max_drawdown = float(drawdown.min())
    beta = _safe_float(info.get("beta"))
    debt_to_equity = _safe_float(info.get("debtToEquity"))

    score = 0.0
    score += 1 if volatility < 30 else 0
    score += 1 if beta is not None and beta < 1.2 else 0
    score += 1 if max_drawdown > -25 else 0
    score += 1 if debt_to_equity is not None and debt_to_equity < 150 else 0

    if score >= 3:
        label = "Lower risk"
        explanation = "The stock has been relatively steadier than many peers, though all equities still move around."
    elif score >= 2:
        label = "Moderate risk"
        explanation = "This looks like a normal stock risk profile: not calm, not extreme."
    else:
        label = "Higher risk"
        explanation = "The stock can swing a lot, so position size and time horizon matter more here."

    metrics = {
        "Volatility": _format_percent(volatility),
        "Largest drop": _format_percent(max_drawdown),
        "Beta": _format_ratio(beta),
        "Debt / equity": _format_ratio(debt_to_equity),
    }

    return RiskResult(label=label, score=score / 4, explanation=explanation, metrics=metrics)


def build_scenario_projection(data: pd.DataFrame, forecast: PredictionResult, currency_code: str = "USD") -> ScenarioResult:
    base_path = pd.DataFrame({"Date": pd.to_datetime(forecast.forecast_dates), "Base": forecast.forecast_values})
    daily_volatility = float(data["Close"].pct_change().dropna().std()) if len(data) > 1 else 0.0
    if daily_volatility == 0:
        daily_volatility = 0.02

    horizon = np.arange(1, len(base_path) + 1)
    spread = daily_volatility * np.sqrt(horizon) * 1.25

    bull_path = base_path.copy()
    bull_path["Bull"] = base_path["Base"] * (1 + spread)

    bear_path = base_path.copy()
    bear_path["Bear"] = base_path["Base"] * (1 - spread)

    summary = {
        "bull": f"If the trend improves, the stock could reach about {format_money(bull_path['Bull'].iloc[-1], currency_code)}.",
        "base": f"The middle path suggests about {format_money(base_path['Base'].iloc[-1], currency_code)}.",
        "bear": f"If conditions weaken, the stock could slip toward {format_money(bear_path['Bear'].iloc[-1], currency_code)}.",
    }

    return ScenarioResult(
        base_label="Base",
        base_path=base_path,
        bull_path=bull_path,
        bear_path=bear_path,
        summary=summary,
    )


def _headline_score(text: str) -> float:
    normalized = text.lower()
    positive_hits = sum(1 for word in POSITIVE_WORDS if word in normalized)
    negative_hits = sum(1 for word in NEGATIVE_WORDS if word in normalized)
    score = positive_hits - negative_hits
    return float(max(-1.0, min(1.0, score / 4.0)))


def load_company_news(ticker: str, limit: int = 6) -> NewsSentimentResult:
    try:
        news_items = yf.Ticker(ticker).news or []
    except Exception:
        news_items = []

    articles: list[dict[str, Any]] = []
    sentiment_scores: list[float] = []

    for item in news_items[:limit]:
        title = str(item.get("title") or "Untitled headline")
        summary = str(item.get("summary") or "")
        score = _headline_score(f"{title} {summary}")
        sentiment_scores.append(score)
        articles.append(
            {
                "title": title,
                "publisher": str(item.get("publisher") or "Unknown"),
                "link": str(item.get("link") or ""),
                "published": pd.to_datetime(item.get("providerPublishTime"), unit="s", errors="coerce"),
                "summary": summary,
                "sentiment": score,
            }
        )

    average_score = float(np.mean(sentiment_scores)) if sentiment_scores else 0.0
    if average_score > 0.15:
        label = "Positive"
    elif average_score < -0.15:
        label = "Negative"
    else:
        label = "Mixed"

    return NewsSentimentResult(articles=articles, average_score=average_score, label=label)
