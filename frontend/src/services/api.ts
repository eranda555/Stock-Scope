/* ═══════════════════════════════════════════════════════════════
   Stock Scope - API Service Layer
   ═══════════════════════════════════════════════════════════════ */

// ─── Base Configuration ─────────────────────────────────────────
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// ─── TypeScript Interfaces ──────────────────────────────────────

export interface MarketOverviewSummary {
  companiesTrading: number;
  advancers: number;
  decliners: number;
  totalVolume: number;
  totalMarketCap: number;
  totalTurnover: number;
}

export interface CseCompany {
  symbol: string;
  name: string;
  price?: number;
  change?: number;
  percentageChange?: number;
  sharevolume?: number;
  turnover?: number;
  marketCap?: number;
  status?: number;
  yfinance_symbol?: string;
}

export interface MarketOverviewResponse {
  summary: MarketOverviewSummary;
  gainers: CseCompany[];
  losers: CseCompany[];
  mostActive: CseCompany[];
}

export interface CseCompanyDetail {
  symbol: string;
  name: string;
  yfinance_symbol?: string;
  sector?: string;
  status: string;
  status_code: number;
  price?: number;
  change?: number;
  percentageChange?: number;
  marketCap?: number;
  shareVolume?: number;
  turnover?: number;
  '52wHigh'?: number;
  '52wLow'?: number;
  previousClose?: number;
  open?: number;
  high?: number;
  low?: number;
}

export interface CseSearchResponse {
  count: number;
  companies: CseCompany[];
}

export interface PriceHistoryRecord {
  Date: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
  [key: string]: number | string;
}

export interface PriceHistoryStats {
  latest_close: number;
  '52w_high': number;
  '52w_low': number;
  avg_daily_return: number;
  volatility: number;
  change_pct: number;
  average_volume: number;
  rsi14: number;
  macd: number;
  macd_signal: number;
}

export interface PriceHistoryResponse {
  ticker: string;
  market: string;
  period: string;
  dataPoints: number;
  records: PriceHistoryRecord[];
  stats?: PriceHistoryStats;
}

export interface CompanyProfile {
  ticker: string;
  market: string;
  name: string;
  sector: string;
  industry: string;
  country: string;
  market_cap?: number;
}

export interface CompanyInfo {
  ticker: string;
  market: string;
  longName?: string;
  shortName?: string;
  sector?: string;
  industry?: string;
  country?: string;
  marketCap?: number;
  enterpriseValue?: number;
  trailingPE?: number;
  forwardPE?: number;
  priceToBook?: number;
  priceToSalesTrailing12Months?: number;
  pegRatio?: number;
  trailingEps?: number;
  forwardEps?: number;
  dividendYield?: number;
  beta?: number;
  bookValue?: number;
  revenueGrowth?: number;
  earningsGrowth?: number;
  profitMargins?: number;
  operatingMargins?: number;
  returnOnAssets?: number;
  returnOnEquity?: number;
  currentRatio?: number;
  debtToEquity?: number;
  freeCashflow?: number;
  operatingCashflow?: number;
  targetMeanPrice?: number;
  targetHighPrice?: number;
  targetLowPrice?: number;
  recommendationKey?: string;
  numberOfAnalystOpinions?: number;
}

export interface NewsArticle {
  title: string;
  publisher: string;
  summary: string;
  link: string;
  published: string;
  sentiment: number;
}

export interface NewsResponse {
  ticker: string;
  market: string;
  averageScore: number;
  label: string;
  articles: NewsArticle[];
}

export interface FinancialHealthResponse {
  label: string;
  score: number;
  explanation: string;
  metrics: Record<string, string>;
}

export interface ValuationResponse {
  label: string;
  score: number;
  explanation: string;
  current_price: number;
  estimated_fair_value: number;
  upside_pct: number;
  metrics: Record<string, string>;
}

export interface RiskResponse {
  label: string;
  score: number;
  explanation: string;
  metrics: Record<string, string>;
}

export interface ScenarioPathPoint {
  Date: string;
  Base?: number;
  Bull?: number;
  Bear?: number;
}

export interface ScenarioResponse {
  base_label: string;
  summary: Record<string, string>;
  base_path: ScenarioPathPoint[];
  bull_path: ScenarioPathPoint[];
  bear_path: ScenarioPathPoint[];
}

export interface TechnicalResponse {
  stats: Record<string, number | string>;
  indicators: PriceHistoryRecord[];
}

// ─── Fetch Wrappers ──────────────────────────────────────────────

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let detail: string;
    try {
      const body = await res.json();
      detail = body.detail || res.statusText;
    } catch {
      detail = res.statusText;
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

// ─── CSE Endpoints ───────────────────────────────────────────────

export function fetchCseMarketOverview(): Promise<MarketOverviewResponse> {
  return request<MarketOverviewResponse>('/cse/market-overview');
}

export function searchCseCompanies(query: string, limit = 20): Promise<CseSearchResponse> {
  const params = new URLSearchParams({ query, limit: String(limit) });
  return request<CseSearchResponse>(`/cse/companies?${params}`);
}

export function fetchCseCompanyDetail(symbol: string): Promise<CseCompanyDetail> {
  return request<CseCompanyDetail>(`/cse/company/${encodeURIComponent(symbol)}`);
}

// ─── Stock Endpoints ─────────────────────────────────────────────

export function fetchPriceHistory(
  market: string,
  ticker: string,
  period = '5y',
  includeIndicators = true,
  includeStats = true
): Promise<PriceHistoryResponse> {
  const params = new URLSearchParams({
    period,
    include_indicators: String(includeIndicators),
    include_stats: String(includeStats),
  });
  return request<PriceHistoryResponse>(
    `/stocks/${encodeURIComponent(market)}/${encodeURIComponent(ticker)}/price-history?${params}`
  );
}

export function fetchCompanyInfo(market: string, ticker: string): Promise<CompanyInfo> {
  return request<CompanyInfo>(
    `/stocks/${encodeURIComponent(market)}/${encodeURIComponent(ticker)}/info`
  );
}

export function fetchCompanyProfile(market: string, ticker: string): Promise<CompanyProfile> {
  return request<CompanyProfile>(
    `/stocks/${encodeURIComponent(market)}/${encodeURIComponent(ticker)}/profile`
  );
}

export function fetchCompanyNews(market: string, ticker: string, limit = 6): Promise<NewsResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  return request<NewsResponse>(
    `/stocks/${encodeURIComponent(market)}/${encodeURIComponent(ticker)}/news?${params}`
  );
}

// ─── Analysis Endpoints ──────────────────────────────────────────

interface FinancialHealthRequest {
  company_info: Record<string, unknown>;
  currency_code: string;
}

export function analyzeFinancialHealth(
  companyInfo: Record<string, unknown>,
  currencyCode = 'USD'
): Promise<FinancialHealthResponse> {
  const body: FinancialHealthRequest = {
    company_info: companyInfo,
    currency_code: currencyCode,
  };
  return request<FinancialHealthResponse>('/analysis/financial-health', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

interface ValuationRequest {
  company_info: Record<string, unknown>;
  current_price: number;
}

export function analyzeValuation(
  companyInfo: Record<string, unknown>,
  currentPrice: number
): Promise<ValuationResponse> {
  const body: ValuationRequest = {
    company_info: companyInfo,
    current_price: currentPrice,
  };
  return request<ValuationResponse>('/analysis/valuation', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

interface RiskRequest {
  price_history: PriceHistoryRecord[];
  company_info: Record<string, unknown>;
}

export function analyzeRisk(
  priceHistory: PriceHistoryRecord[],
  companyInfo: Record<string, unknown>
): Promise<RiskResponse> {
  const body: RiskRequest = {
    price_history: priceHistory,
    company_info: companyInfo,
  };
  return request<RiskResponse>('/analysis/risk', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

interface ScenarioRequest {
  price_history: PriceHistoryRecord[];
  forecast_days: number;
  currency_code: string;
}

export function analyzeScenario(
  priceHistory: PriceHistoryRecord[],
  forecastDays = 30,
  currencyCode = 'USD'
): Promise<ScenarioResponse> {
  const body: ScenarioRequest = {
    price_history: priceHistory,
    forecast_days: forecastDays,
    currency_code: currencyCode,
  };
  return request<ScenarioResponse>('/analysis/scenario', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

interface TechnicalRequest {
  price_history: PriceHistoryRecord[];
}

export function analyzeTechnical(
  priceHistory: PriceHistoryRecord[]
): Promise<TechnicalResponse> {
  const body: TechnicalRequest = { price_history: priceHistory };
  return request<TechnicalResponse>('/analysis/technical', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ─── Health Check ────────────────────────────────────────────────

export function healthCheck(): Promise<{ status: string; app: string; version: string }> {
  return request('/health');
}
