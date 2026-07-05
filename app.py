from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from markets import (
    MARKET_CSE,
    MARKET_CONFIGS,
    MARKET_OPTIONS,
    MARKET_US,
    format_money,
    money_hover_format,
    money_x_hover_format,
    normalize_watchlist_key,
    resolve_security,
    resolve_watchlist_key,
    watchlist_label,
)

from stock_utils import (
    add_indicators,
    build_financial_health,
    build_risk_snapshot,
    build_scenario_projection,
    build_valuation_snapshot,
    compare_with_benchmark,
    forecast_prices,
    load_company_info,
    load_company_news,
    load_company_profile,
    load_price_history,
    sector_benchmark_ticker,
    summarize,
)


WATCHLIST_FILE = Path(__file__).with_name("watchlist.json").resolve()
DEFAULT_WATCHLIST = ["CSE:JKH.N0000", "CSE:COMB.N0000", "US:AAPL"]


st.set_page_config(page_title="Stock Scope", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
        .main {
            background: radial-gradient(circle at top, #f8fbff 0%, #eef4ff 45%, #eefaf5 100%);
        }
        .block-container {
            padding-top: 1.75rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3, h4 {
            color: #0f172a;
        }
        .hero {
            padding: 1.25rem 1.5rem;
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(8px);
        }
        .section-card {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 22px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        }
        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.3rem 0.75rem;
            border-radius: 999px;
            background: #dbeafe;
            color: #1d4ed8;
            font-size: 0.82rem;
            font-weight: 700;
            margin: 0 0.4rem 0.35rem 0;
        }
        .status-chip.green {
            background: #dcfce7;
            color: #166534;
        }
        .status-chip.amber {
            background: #fef3c7;
            color: #92400e;
        }
        .status-chip.red {
            background: #fee2e2;
            color: #991b1b;
        }
        .mini-label {
            font-size: 0.82rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.15rem;
        }
        .what-this-means {
            color: #334155;
            line-height: 1.55;
        }
        @media (max-width: 768px) {
            .hero, .section-card {
                padding: 1rem;
                border-radius: 18px;
            }
            .block-container {
                padding-top: 1rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_watchlist() -> list[str]:
    if WATCHLIST_FILE.exists():
        try:
            raw = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                normalized: list[str] = []
                for item in raw:
                    try:
                        normalized.append(normalize_watchlist_key(str(item)))
                    except ValueError:
                        continue
                if normalized:
                    return sorted(set(normalized))
        except Exception:
            pass
    return DEFAULT_WATCHLIST.copy()


def save_watchlist(watchlist: list[str]) -> None:
    WATCHLIST_FILE.write_text(json.dumps(sorted(set(watchlist)), indent=2), encoding="utf-8")


def display_company_name(company: dict, security) -> str:
    provider_name = str(company.get("name") or "").strip()
    if provider_name and provider_name.upper() != security.provider_symbol.upper():
        return provider_name
    return security.company_name


def make_status_chip(label: str, tone: str = "blue") -> str:
    return f"<span class='status-chip {tone}'>{label}</span>"


def build_quick_verdict(
    health,
    valuation,
    risk,
    forecast,
    news,
    stats: dict,
    benchmark_available: bool,
    comparison,
    analysis_ticker: str,
) -> dict[str, str | float | list[str]]:
    combined_score = (health.score * 28) + (valuation.score * 22) + (risk.score * 20) + (15 if forecast.slope > 0 else 6)
    if news.average_score > 0.15:
        combined_score += 5
    elif news.average_score < -0.15:
        combined_score -= 3

    if combined_score >= 72:
        label = "Worth a closer look"
        tone = "green"
        explanation = (
            f"{analysis_ticker} looks reasonably balanced overall. The company health, trend, and valuation do not raise major red flags, so it may be a candidate for further research rather than an instant decision."
        )
    elif combined_score >= 52:
        label = "Mixed setup"
        tone = "amber"
        explanation = (
            f"{analysis_ticker} has some strengths and some caution signs. That usually means a beginner should keep it on a watchlist and let more information confirm the story."
        )
    else:
        label = "Higher caution"
        tone = "red"
        explanation = (
            f"{analysis_ticker} shows more caution signs than strong signals. A beginner should treat it carefully and focus on understanding the business before acting."
        )

    key_points = [
        f"Financial health is {health.label.lower()}",
        f"Valuation looks {valuation.label.lower()}",
        f"Risk profile is {risk.label.lower()}",
    ]
    if benchmark_available and comparison is not None:
        key_points.append(f"It has outperformed its sector benchmark by {comparison.relative_return_pct:.1f}% in the selected period")
    if news.label != "Mixed":
        key_points.append(f"Recent headlines feel {news.label.lower()}")

    next_step = "Use this as a starting point and compare it with 2-3 other stocks before deciding."
    if tone == "red":
        next_step = "If you are new to investing, wait for a clearer setup or learn more about the company first."

    return {
        "label": label,
        "tone": tone,
        "explanation": explanation,
        "score": combined_score,
        "key_points": key_points,
        "next_step": next_step,
    }


def answer_market_assistant(question: str, context: dict[str, object]) -> str:
    text = question.strip().lower()
    ticker = str(context.get("ticker", "this stock"))
    company_name = str(context.get("company_name", ticker))
    overview_label = str(context.get("overview_label", "Mixed setup"))
    overview_explanation = str(context.get("overview_explanation", ""))
    health_label = str(context.get("health_label", "Mixed"))
    health_explanation = str(context.get("health_explanation", ""))
    valuation_label = str(context.get("valuation_label", "Fair value"))
    valuation_explanation = str(context.get("valuation_explanation", ""))
    risk_label = str(context.get("risk_label", "Moderate risk"))
    risk_explanation = str(context.get("risk_explanation", ""))
    trend_text = str(context.get("trend_text", "mixed"))
    momentum_text = str(context.get("momentum_text", "neutral"))
    news_label = str(context.get("news_label", "Mixed"))
    news_score = float(context.get("news_score", 0.0))
    forecast_slope = float(context.get("forecast_slope", 0.0))
    forecast_score = float(context.get("forecast_score", 0.0))
    current_price = float(context.get("current_price", 0.0))
    fair_value = float(context.get("fair_value", current_price))
    upside_pct = float(context.get("upside_pct", 0.0))
    comparison_text = str(context.get("comparison_text", "No sector comparison is available right now."))
    scenario_bull = str(context.get("scenario_bull", ""))
    scenario_base = str(context.get("scenario_base", ""))
    scenario_bear = str(context.get("scenario_bear", ""))

    if any(keyword in text for keyword in ["hello", "hi", "help", "what can you do", "start"]):
        return (
            f"I can help you understand {company_name} in plain English. Ask me about valuation, risk, financial health, technical trend, news sentiment, or the bull/base/bear scenarios."
        )

    if any(keyword in text for keyword in ["buy", "should i buy", "invest", "good stock"]):
        return (
            f"I cannot tell you what to buy, but my plain-English read is: {overview_explanation} Right now the setup is {overview_label.lower()}. {context.get('next_step', '')}"
        )

    if "health" in text or "financial" in text or "balance sheet" in text or "debt" in text or "cash" in text:
        return f"Financial health looks {health_label.lower()}. {health_explanation} Simple check: strong cash flow and manageable debt usually make a stock easier to hold through rough patches."

    if "value" in text or "valuation" in text or "expensive" in text or "cheap" in text or "fair" in text:
        return (
            f"Valuation looks {valuation_label.lower()}. At the moment the stock trades near ${current_price:.2f}, while a rough fair-value estimate is about ${fair_value:.2f}. That suggests about {upside_pct:.1f}% upside or downside. {valuation_explanation}"
        )

    if "risk" in text or "safe" in text or "volatile" in text or "volatility" in text:
        return (
            f"Risk looks {risk_label.lower()}. {risk_explanation} That means the price can move around, so position size and time horizon matter more for this one."
        )

    if "trend" in text or "technical" in text or "rsi" in text or "macd" in text or "momentum" in text:
        return (
            f"The technical picture is {trend_text} and momentum is {momentum_text}. The forecast model slope is {forecast_slope:.4f} with a fit score of {forecast_score:.3f}, so the short-term direction is {'leaning up' if forecast_slope > 0 else 'leaning down' if forecast_slope < 0 else 'fairly flat'}."
        )

    if "news" in text or "sentiment" in text or "headline" in text:
        return (
            f"Recent news sentiment is {news_label.lower()} with an average score of {news_score:.2f}. That usually means the latest headlines are neither strongly positive nor strongly negative."
        )

    if "scenario" in text or "bull" in text or "bear" in text or "base" in text:
        return f"Scenario view: {scenario_bull} {scenario_base} {scenario_bear}"

    if "compare" in text or "benchmark" in text or "sector" in text:
        return comparison_text

    return (
        f"Ask me about {company_name}'s valuation, financial health, technical trend, risk, news sentiment, sector comparison, or bull/base/bear scenarios. I can explain each part in simple terms."
    )


def cached_price_history(ticker: str, period: str) -> pd.DataFrame:
    return load_price_history(ticker, period=period).copy()


@st.cache_data(show_spinner=False)
def cached_company_profile(ticker: str) -> dict:
    return load_company_profile(ticker)


@st.cache_data(show_spinner=False)
def cached_company_info(ticker: str) -> dict:
    return load_company_info(ticker)


@st.cache_data(show_spinner=False)
def cached_company_news(ticker: str) -> object:
    return load_company_news(ticker)


if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_watchlist()
if "search_ticker" not in st.session_state:
    st.session_state.search_ticker = "AAPL"
if "analysis_ticker" not in st.session_state:
    st.session_state.analysis_ticker = None
if "assistant_messages" not in st.session_state:
    st.session_state.assistant_messages = []
if "assistant_ticker" not in st.session_state:
    st.session_state.assistant_ticker = None
if "assistant_pending_prompt" not in st.session_state:
    st.session_state.assistant_pending_prompt = None


with st.sidebar:
    st.header("Analysis settings")
    st.caption("Keep the search box above simple. These settings stay out of the way.")
    period = st.selectbox("History window", ["1y", "2y", "5y", "max"], index=2, help="How much price history to use for charts and indicators.")
    forecast_days = st.slider("Scenario horizon", min_value=5, max_value=60, value=30, step=5, help="How far forward the base, bull, and bear paths should extend.")
    st.divider()
    st.subheader("Watchlist")
    watchlist_choice = st.selectbox(
        "Saved tickers",
        options=st.session_state.watchlist if st.session_state.watchlist else [st.session_state.search_ticker],
        index=0,
        help="Load a ticker you have already saved.",
    )
    load_watchlist_ticker = st.button("Load ticker", use_container_width=True)
    add_to_watchlist = st.button("Save current ticker", use_container_width=True)
    remove_from_watchlist = st.button("Remove current ticker", use_container_width=True)


if load_watchlist_ticker:
    st.session_state.search_ticker = watchlist_choice
    st.session_state.analysis_ticker = watchlist_choice
    st.rerun()


if add_to_watchlist and st.session_state.search_ticker:
    if st.session_state.search_ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(st.session_state.search_ticker)
        save_watchlist(st.session_state.watchlist)
    st.rerun()


if remove_from_watchlist and st.session_state.search_ticker:
    st.session_state.watchlist = [item for item in st.session_state.watchlist if item != st.session_state.search_ticker]
    if not st.session_state.watchlist:
        st.session_state.watchlist = ["AAPL", "MSFT", "NVDA"]
    save_watchlist(st.session_state.watchlist)
    st.rerun()


st.markdown(
    """
    <div class="hero">
        <h1 style="margin-bottom:0.25rem;">Stock Scope</h1>
        <p style="margin-bottom:0.45rem; color:#334155;">A beginner-friendly investment dashboard that keeps the important signals simple.</p>
        <div>
            <span class='status-chip green'>Clear sections</span>
            <span class='status-chip amber'>Simple language</span>
            <span class='status-chip'>Charts + scenarios</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.container(border=True):
    st.markdown("### Search a stock")
    st.caption("Enter a ticker such as AAPL or MSFT, then click Analyze.")
    with st.form("search_form", clear_on_submit=False):
        input_col, button_col = st.columns([4, 1])
        with input_col:
            ticker_input = st.text_input(
                "Ticker",
                value=st.session_state.search_ticker,
                placeholder="AAPL",
                label_visibility="collapsed",
                help="Type a public stock ticker, like AAPL for Apple.",
            ).strip().upper()
        with button_col:
            submitted = st.form_submit_button("Analyze", use_container_width=True)

    if submitted:
        if not ticker_input:
            st.error("Please enter a ticker before analyzing.")
        else:
            st.session_state.search_ticker = ticker_input
            st.session_state.analysis_ticker = ticker_input


analysis_ticker = st.session_state.analysis_ticker

if not analysis_ticker:
    st.info("Enter a ticker above to see the dashboard. For a quick start, try AAPL or MSFT.")
else:
    try:
        with st.spinner(f"Loading market data for {analysis_ticker}..."):
            raw_data = cached_price_history(analysis_ticker, period)
            data = add_indicators(raw_data)
            stats = summarize(data)
            company = cached_company_profile(analysis_ticker)
            company_info = cached_company_info(analysis_ticker)
            news = cached_company_news(analysis_ticker)
            health = build_financial_health(company_info)
            valuation = build_valuation_snapshot(company_info, current_price=stats["latest_close"])
            risk = build_risk_snapshot(data, company_info)
            forecast = forecast_prices(data, days=forecast_days)
            scenario = build_scenario_projection(data, forecast)

            sector = str(company.get("sector") or "Unknown")
            benchmark_ticker = sector_benchmark_ticker(sector)
            comparison = None
            comparison_error = None
            try:
                benchmark_data = cached_price_history(benchmark_ticker, period)
                comparison = compare_with_benchmark(data, benchmark_data, stock_label=analysis_ticker, benchmark_label=benchmark_ticker)
            except Exception as benchmark_error:
                comparison_error = str(benchmark_error)

        close_series = data["Close"] if "Close" in data.columns else raw_data["Close"]
        latest_row = data.iloc[-1]
        short_trend = "Uptrend" if stats["latest_close"] > latest_row["SMA20"] and latest_row["SMA20"] > latest_row["SMA50"] else "Mixed trend"
        momentum = "Strong" if stats["rsi14"] >= 55 else "Neutral" if stats["rsi14"] >= 40 else "Weak"
        analysis_overview = build_quick_verdict(
            health=health,
            valuation=valuation,
            risk=risk,
            forecast=forecast,
            news=news,
            stats=stats,
            benchmark_available=comparison is not None,
            comparison=comparison,
            analysis_ticker=analysis_ticker,
        )
        comparison_text = (
            f"Compared with {benchmark_ticker}, the stock has returned {comparison.relative_return_pct:.1f}% more and has a correlation of {comparison.correlation:.2f}."
            if comparison is not None
            else f"Sector comparison is unavailable right now. {comparison_error or ''}".strip()
        )

        if st.session_state.assistant_ticker != analysis_ticker:
            st.session_state.assistant_ticker = analysis_ticker
            st.session_state.assistant_messages = [
                {
                    "role": "assistant",
                    "content": (
                        f"I am ready to help you understand {analysis_ticker}. Ask me about valuation, risk, financial health, technical trend, news sentiment, sector comparison, or scenarios."
                    ),
                }
            ]

        assistant_context = {
            "ticker": analysis_ticker,
            "company_name": company.get("name", analysis_ticker),
            "overview_label": analysis_overview["label"],
            "overview_explanation": analysis_overview["explanation"],
            "next_step": analysis_overview["next_step"],
            "health_label": health.label,
            "health_explanation": health.explanation,
            "valuation_label": valuation.label,
            "valuation_explanation": valuation.explanation,
            "risk_label": risk.label,
            "risk_explanation": risk.explanation,
            "trend_text": short_trend,
            "momentum_text": momentum,
            "news_label": news.label,
            "news_score": news.average_score,
            "forecast_slope": forecast.slope,
            "forecast_score": forecast.score,
            "current_price": stats["latest_close"],
            "fair_value": valuation.estimated_fair_value,
            "upside_pct": valuation.upside_pct,
            "comparison_text": comparison_text,
            "scenario_bull": scenario.summary["bull"],
            "scenario_base": scenario.summary["base"],
            "scenario_bear": scenario.summary["bear"],
        }

        st.markdown(
            f"""
            <div style="margin:0.75rem 0 1rem 0;">
                {make_status_chip(company.get('name', analysis_ticker), 'green')}
                {make_status_chip(f"Sector: {sector}", 'blue')}
                {make_status_chip(f"Benchmark: {benchmark_ticker}", 'amber')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.subheader("Quick verdict")
            st.caption("What this means: a plain-English starting point before you dig into the details.")
            verdict_left, verdict_right = st.columns([1.2, 0.8])
            with verdict_left:
                st.markdown(f"<div class='status-chip {analysis_overview['tone']}'> {analysis_overview['label']} </div>", unsafe_allow_html=True)
                st.write(analysis_overview["explanation"])
                st.markdown(
                    f"""
                    <div style="margin-top:0.6rem; color:#334155;">
                        Next step: {analysis_overview['next_step']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with verdict_right:
                st.markdown("**Key things to know**")
                for point in analysis_overview["key_points"]:
                    st.markdown(f"- {point}")

        summary_columns = st.columns(4)
        summary_metrics = [
            ("Price", f"${stats['latest_close']:.2f}", "The latest market price.", "blue"),
            ("Health", health.label, health.explanation, "green" if health.label == "Healthy" else "amber" if health.label == "Mixed" else "red"),
            ("Value", valuation.label, valuation.explanation, "green" if valuation.label == "Looks attractive" else "amber" if valuation.label == "Fair value" else "red"),
            ("Risk", risk.label, risk.explanation, "green" if risk.label == "Lower risk" else "amber" if risk.label == "Moderate risk" else "red"),
        ]
        for column, (title, value, note, tone) in zip(summary_columns, summary_metrics):
            with column:
                st.markdown(
                    f"""
                    <div class="section-card" style="min-height:130px;">
                        <div class="mini-label">{title}</div>
                        <h3 style="margin-bottom:0.35rem;">{value}</h3>
                        <p class="what-this-means" style="margin-bottom:0;">{note}</p>
                        <div style="margin-top:0.65rem;">{make_status_chip(value, tone)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        tab_overview, tab_health, tab_valuation, tab_technical, tab_risk, tab_scenarios, tab_summary, tab_assistant = st.tabs(
            ["Company Overview", "Financial Health", "Valuation", "Technical Analysis", "Risk", "Bull/Base/Bear", "Final Summary", "Assistant"]
        )

        with tab_overview:
            with st.container(border=True):
                st.subheader("Company Overview")
                st.caption("What this means: who the company is and where it sits in the market.")
                overview_left, overview_right = st.columns([1.15, 0.85])
                with overview_left:
                    st.markdown(f"**Company:** {company.get('name', analysis_ticker)}")
                    st.markdown(f"**Sector:** {sector}")
                    st.markdown(f"**Industry:** {company.get('industry', 'Unknown')}")
                    st.markdown(f"**Country:** {company.get('country', 'Unknown')}")
                    st.markdown(f"**Market value:** {format_currency(company_info.get('marketCap'))}")
                    if comparison is not None:
                        st.write(
                            f"Compared with {benchmark_ticker}, the stock has returned {comparison.relative_return_pct:.1f}% more over the selected period."
                        )
                    else:
                        st.info(f"Sector comparison is unavailable right now. {comparison_error or ''}".strip())
                with overview_right:
                    st.markdown("**Recent news**")
                    st.write(f"Headline sentiment is **{news.label.lower()}** for the latest articles.")
                    if news.articles:
                        for article in news.articles[:3]:
                            tone = "green" if article["sentiment"] > 0.15 else "red" if article["sentiment"] < -0.15 else "amber"
                            st.markdown(
                                f"""
                                <div style="margin-bottom:0.6rem;">
                                    {make_status_chip(article['publisher'], tone)}
                                    <div style="font-weight:600; margin-top:0.2rem;">{article['title']}</div>
                                    <div style="color:#475569; font-size:0.92rem;">{article.get('summary') or 'No short summary was available.'}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

        with tab_health:
            with st.container(border=True):
                st.subheader("Financial Health")
                st.caption("What this means: whether the business looks sturdy enough to handle setbacks.")
                st.write(health.explanation)
                health_cols = st.columns(3)
                health_items = list(health.metrics.items())[:6]
                for index, (label, value) in enumerate(health_items):
                    with health_cols[index % 3]:
                        st.metric(label, value)
                st.markdown(
                    """
                    <div style="margin-top:0.75rem; color:#334155;">
                        Simple read: a stronger cash cushion, manageable debt, and healthy margins usually make the company easier to hold through rough patches.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with tab_valuation:
            with st.container(border=True):
                st.subheader("Valuation")
                st.caption("What this means: whether the stock looks cheap, fair, or expensive compared with its own earnings signals.")
                st.write(valuation.explanation)
                valuation_chart = go.Figure()
                valuation_chart.add_trace(
                    go.Bar(
                        x=[valuation.current_price, valuation.estimated_fair_value],
                        y=["Current price", "Estimated fair value"],
                        orientation="h",
                        marker=dict(color=["#2563eb", "#10b981"]),
                        text=[f"${valuation.current_price:.2f}", f"${valuation.estimated_fair_value:.2f}"],
                        textposition="auto",
                        hovertemplate="%{y}: $%{x:.2f}<extra></extra>",
                        showlegend=False,
                    )
                )
                valuation_chart.update_layout(height=280, margin=dict(l=10, r=10, t=20, b=10), template="plotly_white", yaxis=dict(title=""))
                st.plotly_chart(valuation_chart, use_container_width=True)
                valuation_cols = st.columns(3)
                for index, (label, value) in enumerate(list(valuation.metrics.items())[:6]):
                    with valuation_cols[index % 3]:
                        st.metric(label, value)
                st.markdown(
                    """
                    <div style="margin-top:0.75rem; color:#334155;">
                        Beginner takeaway: if the fair-value bar is well above the current price, the market may be pricing in extra upside. If it is below, the stock may already be expensive.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with tab_technical:
            with st.container(border=True):
                st.subheader("Technical Analysis")
                st.caption("What this means: the stock's recent trend and momentum.")
                trend_note = "Price is above key moving averages, which often suggests positive momentum." if short_trend == "Uptrend" else "The trend is mixed, so the chart is less decisive right now."
                momentum_note = "RSI is leaning strong." if momentum == "Strong" else "RSI is neutral." if momentum == "Neutral" else "RSI is weak, so the stock may have lost some momentum."
                st.write(f"**Trend:** {short_trend}. {trend_note}")
                st.write(f"**Momentum:** {momentum}. {momentum_note}")

                technical_chart = go.Figure()
                technical_chart.add_trace(
                    go.Scatter(
                        x=data["Date"],
                        y=close_series,
                        name="Close",
                        line=dict(color="#2563eb", width=2.5),
                        hovertemplate="%{x|%b %d, %Y}<br>Close: $%{y:.2f}<extra></extra>",
                    )
                )
                technical_chart.add_trace(
                    go.Scatter(
                        x=data["Date"],
                        y=data["SMA20"],
                        name="20-day average",
                        line=dict(color="#f59e0b", width=1.7),
                        hovertemplate="%{x|%b %d, %Y}<br>20-day average: $%{y:.2f}<extra></extra>",
                    )
                )
                technical_chart.add_trace(
                    go.Scatter(
                        x=data["Date"],
                        y=data["SMA50"],
                        name="50-day average",
                        line=dict(color="#10b981", width=1.7),
                        hovertemplate="%{x|%b %d, %Y}<br>50-day average: $%{y:.2f}<extra></extra>",
                    )
                )
                technical_chart.update_layout(
                    height=420,
                    margin=dict(l=10, r=10, t=20, b=10),
                    template="plotly_white",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                )
                st.plotly_chart(technical_chart, use_container_width=True)
                st.markdown(
                    """
                    <div style="color:#334155;">
                        Simple read: when the price stays above both moving averages, the trend is usually healthier. When it slips below them, momentum tends to cool off.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with tab_risk:
            with st.container(border=True):
                st.subheader("Risk")
                st.caption("What this means: how much the stock tends to bounce around and how sensitive it can be to market moves.")
                st.write(risk.explanation)
                risk_cols = st.columns(4)
                for index, (label, value) in enumerate(risk.metrics.items()):
                    with risk_cols[index % 4]:
                        st.metric(label, value)
                if comparison is not None:
                    st.markdown(
                        f"""
                        <div style="margin-top:0.75rem; color:#334155;">
                            Compared with {benchmark_ticker}, the stock has moved with a correlation of {comparison.correlation:.2f}. That means it often follows the market direction but still keeps its own personality.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        with tab_scenarios:
            with st.container(border=True):
                st.subheader("Bull / Base / Bear Scenarios")
                st.caption("What this means: a simple range of possible paths, not a promise of what will happen.")
                scenario_chart = go.Figure()
                scenario_chart.add_trace(
                    go.Scatter(
                        x=scenario.bear_path["Date"],
                        y=scenario.bear_path["Bear"],
                        name="Bear",
                        line=dict(color="#ef4444", width=2),
                        hovertemplate="%{x|%b %d, %Y}<br>Bear: $%{y:.2f}<extra></extra>",
                    )
                )
                scenario_chart.add_trace(
                    go.Scatter(
                        x=scenario.bull_path["Date"],
                        y=scenario.bull_path["Bull"],
                        name="Bull",
                        line=dict(color="#10b981", width=2),
                        fill="tonexty",
                        fillcolor="rgba(16, 185, 129, 0.10)",
                        hovertemplate="%{x|%b %d, %Y}<br>Bull: $%{y:.2f}<extra></extra>",
                    )
                )
                scenario_chart.add_trace(
                    go.Scatter(
                        x=scenario.base_path["Date"],
                        y=scenario.base_path["Base"],
                        name="Base",
                        line=dict(color="#2563eb", width=2.5, dash="dot"),
                        hovertemplate="%{x|%b %d, %Y}<br>Base: $%{y:.2f}<extra></extra>",
                    )
                )
                scenario_chart.update_layout(
                    height=430,
                    margin=dict(l=10, r=10, t=20, b=10),
                    template="plotly_white",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                )
                st.plotly_chart(scenario_chart, use_container_width=True)

                scenario_cols = st.columns(3)
                scenario_cards = [
                    ("Bull", scenario.summary["bull"], "green"),
                    ("Base", scenario.summary["base"], "blue"),
                    ("Bear", scenario.summary["bear"], "red"),
                ]
                for column, (label, message, tone) in zip(scenario_cols, scenario_cards):
                    with column:
                        st.markdown(
                            f"""
                            <div class="section-card">
                                <div class="mini-label">{label}</div>
                                <p class="what-this-means" style="margin-bottom:0;">{message}</p>
                                <div style="margin-top:0.6rem;">{make_status_chip(label, tone)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                st.markdown(
                    """
                    <div style="margin-top:0.75rem; color:#334155;">
                        Beginner takeaway: the base case is the middle path, the bull case is the optimistic path, and the bear case is the caution path.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with tab_summary:
            with st.container(border=True):
                st.subheader("Final Summary")
                st.caption("What this means: a simple plain-English wrap-up.")
                st.markdown(f"<div class='status-chip {analysis_overview['tone']}'> {analysis_overview['label']} </div>", unsafe_allow_html=True)
                st.write(analysis_overview["explanation"])
                st.markdown(
                    f"""
                    <div style="margin-top:0.75rem; color:#334155;">
                        Short version: the market is saying {stats['change_pct']:.1f}% over the selected period, the latest momentum is {momentum.lower()}, and the valuation story is {valuation.label.lower()}.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with tab_assistant:
            with st.container(border=True):
                st.subheader("Market Assistant")
                st.caption("Ask simple questions about the current ticker. This local assistant uses the analysis on the page.")
                quick_questions = st.columns(4)
                quick_prompts = [
                    "Should I buy this stock?",
                    "How does the valuation look?",
                    "What is the risk level?",
                    "Explain the bull/base/bear scenarios.",
                ]
                for column, prompt in zip(quick_questions, quick_prompts):
                    with column:
                        if st.button(prompt, use_container_width=True, key=f"assistant_{prompt}"):
                            st.session_state.assistant_pending_prompt = prompt

                for message in st.session_state.assistant_messages:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

                user_prompt = st.chat_input(f"Ask about {analysis_ticker}...", key=f"assistant_input_{analysis_ticker}")
                prompt_to_answer = user_prompt or st.session_state.assistant_pending_prompt
                if prompt_to_answer:
                    st.session_state.assistant_pending_prompt = None
                    st.session_state.assistant_messages.append({"role": "user", "content": prompt_to_answer})
                    with st.chat_message("user"):
                        st.write(prompt_to_answer)
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking through the data..."):
                            reply = answer_market_assistant(prompt_to_answer, assistant_context)
                            st.write(reply)
                    st.session_state.assistant_messages.append({"role": "assistant", "content": reply})

        st.caption("Built with Streamlit, yfinance, Plotly, and simple explanatory scoring for beginner investors.")

    except ValueError as error:
        st.error(f"We could not analyze {analysis_ticker}. {error}")
        st.info("Try a different ticker such as AAPL, MSFT, NVDA, or TSLA.")
    except Exception as error:
        st.error(f"Something went wrong while loading {analysis_ticker}. {error}")
        st.info("If the ticker is valid but data is unavailable, try again later or choose another stock.")
