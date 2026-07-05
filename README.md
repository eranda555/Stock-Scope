# Stock Scope

A beginner-friendly Streamlit dashboard for stock analysis, simple forecasting, and plain-English investing insights.

## What it shows
- Company Overview
- Financial Health
- Valuation
- Technical Analysis
- Risk
- Bull / Base / Bear Scenarios
- Final Summary
- Market Assistant

## Features
- Search a company ticker like `AAPL`, `MSFT`, or `TSLA`
- Use a single Analyze button to load the dashboard
- See price trend charts with moving averages, RSI, and MACD
- Compare the company against a sector ETF benchmark
- Review recent news with simple headline sentiment scoring
- Check a valuation context chart and a scenario range chart
- Save tickers to a local watchlist
- Ask the built-in Market Assistant questions about the current ticker

## Run locally
1. Install Python 3.11+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   streamlit run app.py
   ```

## Notes
- Forecasts are educational only and should not be used as financial advice.
- Market prices are pulled from Yahoo Finance through `yfinance`.
- Watchlist entries are stored locally in `watchlist.json`.
