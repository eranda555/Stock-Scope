# Stock Scope

> A beginner-friendly investment dashboard for the Sri Lanka Colombo Stock Exchange (CSE) and US markets. Built with Python and Streamlit.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-orange.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why This Exists

Investing should be accessible to everyone, not just financial experts. Stock Scope pulls live market data from the Colombo Stock Exchange (CSE) and US markets, then presents it in plain English with clear visualizations, risk analysis, and scenario planning — all in one dashboard.

**What problems does it solve?**
- CSE investors lack a modern, beginner-friendly dashboard with live data
- Technical jargon makes stock analysis intimidating for newcomers
- Scattered information (prices, news, technicals) requires multiple tools
- Risk assessment and scenario planning are typically enterprise-only features

## Quick Start

```bash
cd Stock-Scope
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Features

### Market Support
- **Sri Lanka Colombo Stock Exchange (CSE)** — Full support with live data from the CSE API
- **US Markets** — Yahoo Finance integration for major US stocks

### CSE Market Features
- **Live CSE Market Data** — Real-time prices, volume, and turnover from the CSE API
- **Market Open/Closed Status** — Shows current trading session with countdown timer
  - Pre-Open Session (9:00 AM - 9:30 AM SLST)
  - Regular Trading (9:30 AM - 2:30 PM SLST)
  - Market Closed / Weekend / Holiday detection
- **CSE Market Overview** — Dashboard showing:
  - Companies currently trading
  - Advancers vs Decliners
  - Total volume and market cap
  - **Top Gainers** — 10 stocks with highest percentage gains
  - **Top Losers** — 10 stocks with highest percentage losses
  - **Most Active** — 10 stocks by trading volume
- **Data Freshness Indicators** — LIVE, DELAYED, STALE, or LATEST AVAILABLE status

### Stock Analysis Features
- **Stock Search** — Search by ticker (JKH), company name (John Keells), or full symbol (JKH.N0000)
- **Watchlist** — Save and load your favorite tickers locally
- **Historical Price Analysis** — Price charts with customizable time windows (1y, 2y, 5y, max)
- **Technical Analysis** — Moving averages (SMA20, SMA50), RSI, MACD indicators
- **Financial Health** — Balance sheet and income statement analysis (US stocks)
- **Valuation** — Fair value estimation and upside/downside calculations
- **Risk Analysis** — Comprehensive risk scoring (0-100) with:
  - Volatility assessment
  - Maximum drawdown
  - Beta analysis
  - Liquidity risk
  - Debt risk evaluation
- **Bull / Base / Bear Scenarios** — Future price projections with three scenarios
- **Risk-Based Stock Ranking** — Analyze all ~167 CSE trading stocks ranked by risk score
- **Portfolio Allocation Simulator** — Build diversified portfolios (Lower Risk, Balanced, Growth styles)
- **Plain-English Insights** — Beginner-friendly explanations for every metric
- **Market Assistant** — Chat-style Q&A about the current stock

### Data Sources and Fallback Behavior
- **CSE Live Data** — Primary source for CSE prices via `https://www.cse.lk/api/`
- **Yahoo Finance (yfinance)** — Fallback for historical prices and US market data
- **Graceful Degradation** — When CSE API is unavailable, the app shows cached data with clear status indicators
- **Error Handling** — Timeouts and retries built into all external API calls

## Installation

### Prerequisites
- **Python 3.11 or higher**
- **pip** (Python package manager)

### Step-by-Step

1. **Clone or download the repository**
   ```bash
   cd Stock-Scope
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   The app will automatically open at `http://localhost:8501`

## How to Run

```bash
streamlit run app.py
```

The dashboard will launch in your default browser. Use the sidebar to:
- Select a market (CSE or US)
- Enter a ticker or company name
- Adjust analysis settings (history window, forecast horizon)
- Manage your watchlist

## Project Structure

```
Stock-Scope/
├── app.py                    # Main Streamlit application (UI)
├── cse_data.py              # CSE company directory and API integration
├── cse_companies.json       # Cached CSE company list
├── data_sources.py          # Data source configuration
├── markets.py               # Market configuration and security resolution
├── market_data_manager.py   # CSE market data caching and refresh logic
├── market_status.py         # CSE trading hours and market status
├── providers.py             # Data provider abstractions (CSE, yfinance)
├── risk_analyzer.py         # Risk scoring and portfolio allocation engine
├── stock_utils.py           # Utility functions for analysis and indicators
├── watchlist.json           # User's saved watchlist (auto-created)
├── .risk_ranking_snapshot.json  # Cached risk ranking results (auto-created)
├── requirements.txt         # Python dependencies
├── .gitignore              # Git exclusion rules
└── README.md               # This file
```

### Key Modules

| File | Purpose |
|------|---------|
| `app.py` | Streamlit dashboard UI with all visualizations |
| `cse_data.py` | CSE API integration, company search, autocomplete |
| `market_status.py` | Trading hours detection, session status, countdown timers |
| `market_data_manager.py` | Smart caching, auto-refresh, data freshness tracking |
| `providers.py` | Abstraction layer for CSE API and yfinance |
| `risk_analyzer.py` | Risk scoring, scenario projection, portfolio allocation |
| `stock_utils.py` | Technical indicators, financial health, valuation logic |

## Testing and QA

### Running Tests

The project includes unit tests for critical components:

```bash
# Run market status tests
python test_market_status.py
```

### QA Coverage

- **Market Status Logic** — Trading hours, session detection, holiday handling
- **Risk Calculations** — Volatility, drawdown, beta, portfolio scoring
- **Data Freshness** — Cache invalidation, staleness detection
- **Watchlist Operations** — Save/load, migration, validation

See `QA_REPORT.md` for detailed test results and coverage analysis.

## Known Limitations

### CSE-Specific Limitations
- **Financial Statement Data** — CSE does not provide balance sheet or income statement data through its public API. Financial health analysis is unavailable for CSE stocks.
- **Sector Benchmarks** — Sector ETF comparisons are not available for CSE; only the overall CSE All Share index is used as a reference.
- **Poya Day Holidays** — Lunar-based Poya holidays are not in the fixed holiday list. The app handles these gracefully by showing "Unknown" status rather than falsely displaying "Market Open."

### Data Limitations
- **Yahoo Finance Rate Limits** — Heavy usage may trigger rate limiting; the app includes retries and caching to mitigate this.
- **Historical Data Gaps** — Some CSE stocks have limited price history on Yahoo Finance.
- **Real-Time Delay** — CSE API data may have a slight delay; status indicators show data freshness.

### Feature Limitations
- **No Buy/Sell Recommendations** — This is an educational tool, not financial advice.
- **Single-User** — Watchlist is stored locally; no multi-user or cloud sync.
- **No Backtesting** — Scenario projections are based on historical statistics, not simulated trading.

## API Reference

### Market Status API

```python
from market_status import (
    get_slst_now,
    get_market_session,
    get_cse_market_status,
    get_market_status_label,
    get_next_market_open,
    get_time_until_status_change,
    get_data_freshness_status,
    format_slst_time,
    format_slst_date,
)
```

### Risk Analysis API

```python
from risk_analyzer import (
    compute_risk_score,
    compute_scenario_prices,
    compute_signal,
    build_risk_ranking_table,
    build_portfolio_allocation,
    calculate_investment,
    calculate_future_value,
    compute_portfolio_risk_score,
    format_risk_label,
)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Before submitting:**
- Test with both CSE and US tickers
- Verify no secrets or API keys are committed
- Update documentation for new features

## Data Attribution

- **CSE Data** — Colombo Stock Exchange (https://www.cse.lk)
- **US Market Data** — Yahoo Finance via yfinance
- **Company Profiles** — Provided by respective exchanges

## Changelog

### Recent Updates
- Added CSE market open/closed status with countdown timer
- Implemented data freshness indicators (LIVE, DELAYED, STALE)
- Added risk-based stock ranking for all ~167 CSE trading stocks
- Introduced portfolio allocation simulator (Lower Risk, Balanced, Growth)
- Enhanced CSE company name resolution to avoid Yahoo corruption

## Disclaimer

**EDUCATIONAL PURPOSES ONLY — NOT FINANCIAL ADVICE**

Stock Scope is an educational tool designed to help beginners understand stock analysis concepts. It is **NOT** financial advice, investment recommendation, or a trading signal generator.

- All data is provided "as is" without warranty
- Past performance does not guarantee future results
- Always consult a qualified financial advisor before making investment decisions
- The authors and contributors are not responsible for any financial losses

**Forecasts and scenarios are for educational purposes only and should not be used as the sole basis for investment decisions.**

## License

MIT License — See [LICENSE](LICENSE) for details.

## Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) — Dashboard framework
- [yfinance](https://github.com/ranaroussi/yfinance) — Market data
- [Plotly](https://plotly.com/) — Interactive charts
- [pandas](https://pandas.pydata.org/) — Data manipulation
- [numpy](https://numpy.org/) — Numerical computing

---

<div align="center">

**Made with ❤️ for beginner investors in Sri Lanka and beyond**

</div>