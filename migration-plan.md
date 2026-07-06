# Stock Scope - Migration Plan

## Current Architecture (Streamlit Monolithic)

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit App                       │
│                    (app.py)                          │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ app.py       │  │ cse_data.py  │  │ markets.py│  │
│  │ (UI + Logic) │  │ (CSE API)   │  │ (Markets) │  │
│  └─────────────┘  └──────────────┘  └───────────┘  │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐                   │
│  │ providers.py│  │ stock_utils  │                   │
│  │ (Providers) │  │ (Analysis)   │                   │
│  └─────────────┘  └──────────────┘                   │
│                                                      │
│  All rendering is server-side via Streamlit          │
│  State managed via st.session_state                  │
│  Caching via @st.cache_data                          │
└─────────────────────────────────────────────────────┘
```

**Problems with current architecture:**
- Tightly coupled UI and business logic
- No separation of concerns (UI rendering mixed with data fetching)
- Limited to Streamlit's component library
- No programmatic API for external consumers
- No TypeScript type safety on the frontend
- State management limited to Streamlit session state

---

## Target Architecture (FastAPI Backend + React/TypeScript Frontend)

```
┌──────────────────────────────────────────────────┐
│                  Frontend (React/TypeScript)       │
│                                                    │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ Sidebar  │ │ Layout   │ │ StockSearch       │  │
│  │ (Nav)    │ │ (Shell)  │ │ ┌───────────────┐ │  │
│  └──────────┘ └──────────┘ │ │CompanyOverview │ │  │
│                            │ │FinancialHealth │ │  │
│  ┌──────────────┐          │ │Valuation       │ │  │
│  │MarketOverview│          │ │Technical       │ │  │
│  └──────────────┘          │ │Risk            │ │  │
│                            │ │Scenarios       │ │  │
│  ┌──────────┐              │ └───────────────┘ │  │
│  │Watchlist │              └───────────────────┘  │
│  └──────────┘                                     │
│         │                                         │
│         │ HTTP/JSON (REST API)                    │
└─────────┼─────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────┐
│              Backend (FastAPI/Python)               │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ routers/ │ │ routers/ │ │ routers/          │  │
│  │ cse.py   │ │stocks.py │ │ analysis.py       │  │
│  └──────────┘ └──────────┘ └───────────────────┘  │
│         │         │                │               │
│         ▼         ▼                ▼               │
│  ┌──────────────────────────────────────────────┐  │
│  │         Existing Python Library              │  │
│  │  (stock_utils.py, cse_data.py, markets.py,  │  │
│  │   providers.py - unchanged, imported via     │  │
│  │   sys.path from project root)               │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Data Sources                                │  │
│  │  ┌─────────┐  ┌──────────┐  ┌───────────┐  │  │
│  │  │yfinance │  │CSE API   │  │Local JSON │  │  │
│  │  │(market) │  │(CSE live)│  │(watchlist)│  │  │
│  │  └─────────┘  └──────────┘  └───────────┘  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## API Endpoint Design

### Market Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/cse/market-overview` | Live CSE market summary (advancers, decliners, volume, etc.) |
| `GET` | `/api/cse/companies?query=` | Search/filter CSE companies |
| `GET` | `/api/cse/company/{symbol}` | Detailed CSE company info |

### Stock Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stocks/{market}/{ticker}/price-history?period=5y` | Price history with technical indicators |
| `GET` | `/api/stocks/{market}/{ticker}/info` | Company fundamental info |
| `GET` | `/api/stocks/{market}/{ticker}/profile` | Company profile |
| `GET` | `/api/stocks/{market}/{ticker}/news` | News with sentiment |

### Analysis Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analysis/financial-health` | Financial health scoring |
| `POST` | `/api/analysis/valuation` | Valuation analysis |
| `POST` | `/api/analysis/risk` | Risk metrics |
| `POST` | `/api/analysis/scenario` | Bull/base/bear scenario projection |
| `POST` | `/api/analysis/technical` | Technical indicators summary |

### All Responses are JSON
- Price history DataFrames are converted to lists of objects
- Analysis results use the existing dataclass structures serialized as JSON
- Error responses follow `{"detail": "message"}` format (FastAPI default)

---

## Frontend Component Tree

```
App
├── Layout
│   ├── Sidebar
│   │   ├── Logo/AppName
│   │   ├── NavLink: Market Overview
│   │   ├── NavLink: Stock Search
│   │   └── NavLink: Watchlist
│   ├── Header
│   │   ├── App Title
│   │   ├── Market Selector (CSE/US)
│   │   └── Search Bar
│   └── Main Content (router)
│       ├── MarketOverview
│       │   ├── MetricsCards (Market Cap, Volume, Adv/Dec, Turnover)
│       │   ├── TopGainersTable
│       │   ├── TopLosersTable
│       │   └── MostActiveTable
│       ├── StockSearch
│       │   ├── SearchInput (with autocomplete)
│       │   ├── StockDetail (when a stock is selected)
│       │   │   ├── TabNav (Overview, Health, Valuation, Technical, Risk, Scenarios)
│       │   │   ├── CompanyProfile
│       │   │   ├── PriceChart
│       │   │   ├── FinancialHealth
│       │   │   ├── ValuationAnalysis
│       │   │   ├── TechnicalAnalysis
│       │   │   ├── RiskAnalysis
│       │   │   └── ScenarioProjection
│       │   └── EmptyState (when no stock selected)
│       └── Watchlist
│           ├── WatchlistGrid
│           └── WatchlistItem (card per ticker)
└── Global Styles (CSS Variables for Dark Theme)
```

---

## Data Flow Diagram

```
User Action                  Frontend                    Backend                    Data Sources
───────────                  ────────                    ───────                    ────────────
                                                         
1. Select Market ──────> App.tsx updates state
                          
2. Search Stock ───────> StockSearch.tsx
                         │ GET /api/cse/companies?query=
                         └────────────────────> cse.py ──> CSE_DIRECTORY.search()
                         <──── JSON ─────────────────────
                         (autocomplete results)

3. Click Analyze ──────> StockSearch.tsx
                         │ GET /api/stocks/CSE/JKH/price-history
                         └────────────────────> stocks.py ──> provider.load_price_history()
                         <──── JSON ───────────────────────
                         
                         │ GET /api/stocks/CSE/JKH/profile
                         └────────────────────> stocks.py ──> provider.load_company_profile()
                         <──── JSON ───────────────────────

                         │ POST /api/analysis/financial-health
                         └────────────────────> analysis.py ──> build_financial_health()
                         <──── JSON ───────────────────────

4. Tab Switch ─────────> Component renders pre-fetched data
   (No new API call, data is cached in component state)

5. View Market ────────> MarketOverview.tsx
                         │ GET /api/cse/market-overview
                         └────────────────────> cse.py ──> fetch_live_trade_summary()
                         <──── JSON ─────────────────────
```

---

## Route Design (Frontend Navigation)

The frontend uses a simple state-based router (no React Router needed initially):

| Active Section | URL Hash | Component | Description |
|----------------|----------|-----------|-------------|
| `market-overview` | `#market` | MarketOverview | CSE market dashboard |
| `stock-search` | `#search` | StockSearch | Search and analyze stocks |
| `watchlist` | `#watchlist` | Watchlist | Saved tickers overview |

Internal stock detail tab navigation (within StockSearch component):
| Tab Key | Component | Description |
|---------|-----------|-------------|
| `overview` | CompanyProfile + PriceChart | Company info and chart |
| `health` | FinancialHealth | Financial metrics |
| `valuation` | ValuationAnalysis | Valuation metrics |
| `technical` | TechnicalAnalysis | Technical indicators |
| `risk` | RiskAnalysis | Risk metrics |
| `scenarios` | ScenarioProjection | Bull/base/bear forecast |

---

## Step-by-Step Migration Phases

### Phase 1: Foundation (Current)
- [x] Create project directories
- [x] Copy existing files to `streamlit-app/` (preserving the working Streamlit app)
- [x] Create migration plan document

### Phase 2: Backend API
- [x] Create FastAPI backend with CORS middleware
- [x] Create routers for CSE data, stocks, and analysis
- [x] Reuse existing Python modules via sys.path import
- [x] Test backend endpoints with curl/Postman

### Phase 3: Frontend Shell
- [x] Create React/TypeScript project with build configuration
- [x] Set up dark theme design system with CSS variables
- [x] Build Layout, Sidebar, and navigation
- [x] Create API service layer with TypeScript interfaces

### Phase 4: Frontend Feature Components
- [ ] Build MarketOverview component
- [ ] Build StockSearch with autocomplete
- [ ] Build CompanyProfile component
- [ ] Build PriceChart component (with Recharts)
- [ ] Build FinancialHealth, Valuation, Technical, Risk, Scenarios components
- [ ] Build Watchlist component

### Phase 5: Integration & Polish
- [ ] Connect frontend to live backend API
- [ ] Add loading states and error handling
- [ ] Add responsive design refinements
- [ ] Performance optimization
- [ ] Deploy backend and frontend

---

## Reused Python Modules

| Module | Purpose | Status |
|--------|---------|--------|
| `stock_utils.py` | Core analysis functions, forecasting, indicators | Unchanged - imported by backend |
| `cse_data.py` | CSE directory and live trade data | Unchanged - imported by backend |
| `markets.py` | Market configs, security resolution, formatting | Unchanged - imported by backend |
| `providers.py` | Data provider abstraction (yfinance, CSE API) | Unchanged - imported by backend |
| `cse_companies.json` | CSE company directory data | Unchanged - read by cse_data.py |

**Key functions exposed as API endpoints:**

| Function | Source File | API Endpoint |
|----------|-------------|--------------|
| `fetch_live_trade_summary()` | `cse_data.py` | `GET /api/cse/market-overview` |
| `CSE_DIRECTORY.search(query)` | `cse_data.py` | `GET /api/cse/companies` |
| `load_price_history(ticker, period)` | `stock_utils.py` | `GET /api/stocks/{m}/{t}/price-history` |
| `load_company_info(ticker)` | `stock_utils.py` | `GET /api/stocks/{m}/{t}/info` |
| `load_company_profile(ticker)` | `stock_utils.py` | `GET /api/stocks/{m}/{t}/profile` |
| `load_company_news(ticker)` | `stock_utils.py` | `GET /api/stocks/{m}/{t}/news` |
| `add_indicators(data)` | `stock_utils.py` | `POST /api/analysis/technical` |
| `summarize(data)` | `stock_utils.py` | `POST /api/analysis/technical` |
| `build_financial_health(info, currency)` | `stock_utils.py` | `POST /api/analysis/financial-health` |
| `build_valuation_snapshot(info, price)` | `stock_utils.py` | `POST /api/analysis/valuation` |
| `build_risk_snapshot(data, info)` | `stock_utils.py` | `POST /api/analysis/risk` |
| `forecast_prices(data, days)` | `stock_utils.py` | `POST /api/analysis/scenario` |
| `build_scenario_projection(data, forecast, currency)` | `stock_utils.py` | `POST /api/analysis/scenario` |
| `get_provider(market)` | `providers.py` | Used internally by stock endpoints |
| `resolve_security(query, market)` | `markets.py` | Used internally by CSE endpoints |
| `format_money(value, currency)` | `markets.py` | Used internally for formatting |

---

## How to Run

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs available at http://localhost:8000/docs
```

### Frontend (React)
```bash
cd frontend
npm install
npm start
# Opens at http://localhost:3000
```

### Legacy Streamlit App (unchanged)
```bash
cd streamlit-app
streamlit run app.py
# Opens at http://localhost:8501
```
