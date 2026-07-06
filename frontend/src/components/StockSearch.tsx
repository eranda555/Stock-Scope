/* ═══════════════════════════════════════════════════════════════
   StockSearch - Search for stocks and view detailed analysis tabs
   ═══════════════════════════════════════════════════════════════ */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import type { CseCompany } from '../services/api';
import { searchCseCompanies } from '../services/api';
import CompanyProfile from './CompanyProfile';
import PriceChart from './PriceChart';
import FinancialHealth from './FinancialHealth';
import ValuationAnalysis from './ValuationAnalysis';
import TechnicalAnalysis from './TechnicalAnalysis';
import RiskAnalysis from './RiskAnalysis';
import ScenarioProjection from './ScenarioProjection';

interface StockSearchProps {
  selectedMarket: 'CSE' | 'US';
  initialTicker: string | null;
  onSelectTicker: (ticker: string) => void;
}

type AnalysisTab = 'overview' | 'health' | 'valuation' | 'technical' | 'risk' | 'scenarios';

const ANALYSIS_TABS: { id: AnalysisTab; label: string }[] = [
  { id: 'overview', label: 'Company Overview' },
  { id: 'health', label: 'Financial Health' },
  { id: 'valuation', label: 'Valuation' },
  { id: 'technical', label: 'Technical Analysis' },
  { id: 'risk', label: 'Risk' },
  { id: 'scenarios', label: 'Scenarios' },
];

/* ── Mock stock data for development ── */
const MOCK_TICKER_INFO = {
  CSE: {
    JKH: {
      profile: {
        name: 'John Keells Holdings PLC',
        sector: 'Diversified Financials',
        industry: 'Investment Holding Companies',
        country: 'Sri Lanka',
        market_cap: 285000000000,
      },
      currentPrice: 204.50,
      currency: 'LKR',
    },
    COMB: {
      profile: {
        name: 'Commercial Bank of Ceylon PLC',
        sector: 'Financial Services',
        industry: 'Banks',
        country: 'Sri Lanka',
        market_cap: 118000000000,
      },
      currentPrice: 98.20,
      currency: 'LKR',
    },
    LOLC: {
      profile: {
        name: 'LOLC Holdings PLC',
        sector: 'Diversified Financials',
        industry: 'Investment Holding Companies',
        country: 'Sri Lanka',
        market_cap: 385000000000,
      },
      currentPrice: 385.00,
      currency: 'LKR',
    },
  },
  US: {
    AAPL: {
      profile: {
        name: 'Apple Inc.',
        sector: 'Technology',
        industry: 'Consumer Electronics',
        country: 'United States',
        market_cap: 2850000000000,
      },
      currentPrice: 178.50,
      currency: 'USD',
    },
  },
};

const DEFAULT_MOCK_TICKER = {
  profile: {
    name: 'John Keells Holdings PLC',
    sector: 'Diversified Financials',
    industry: 'Investment Holding Companies',
    country: 'Sri Lanka',
    market_cap: 285000000000,
  },
  currentPrice: 204.50,
  currency: 'LKR',
};

const StockSearch: React.FC<StockSearchProps> = ({
  selectedMarket,
  initialTicker,
}) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<CseCompany[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeTab, setActiveTab] = useState<AnalysisTab>('overview');
  const [selectedStock, setSelectedStock] = useState<string | null>(initialTicker);
  const [loading, setLoading] = useState(false);
  const suggestRef = useRef<HTMLDivElement>(null);

  // Parse the selectedStock into ticker symbol
  const resolvedTicker = selectedStock ? selectedStock.replace(/^(CSE|US):/, '') : null;
  const resolvedMarket = selectedStock?.startsWith('US') ? 'US' : 'CSE';

  // Get mock data for the selected stock
  const stockData = resolvedTicker
    ? (MOCK_TICKER_INFO as any)[resolvedMarket]?.[resolvedTicker] || DEFAULT_MOCK_TICKER
    : null;

  // Handle search input changes
  const handleSearchChange = useCallback(
    async (value: string) => {
      setQuery(value);
      if (value.length < 1) {
        setSuggestions([]);
        setShowSuggestions(false);
        return;
      }
      if (selectedMarket === 'CSE') {
        try {
          const result = await searchCseCompanies(value);
          setSuggestions(result.companies);
          setShowSuggestions(result.companies.length > 0);
        } catch {
          // Use mock suggestions
          const mockSuggestions: CseCompany[] = [
            { symbol: 'JKH.N0000', name: 'John Keells Holdings PLC', price: 204.50, percentageChange: 5.2 },
            { symbol: 'COMB.N0000', name: 'Commercial Bank of Ceylon PLC', price: 98.20, percentageChange: 4.8 },
            { symbol: 'LOLC.N0000', name: 'LOLC Holdings PLC', price: 385.00, percentageChange: 4.1 },
            { symbol: 'SAMP.N0000', name: 'Sampath Bank PLC', price: 72.60, percentageChange: 3.9 },
            { symbol: 'HNB.N0000', name: 'Hatton National Bank PLC', price: 185.40, percentageChange: 3.2 },
          ].filter(
            (c) =>
              c.symbol.toUpperCase().includes(value.toUpperCase()) ||
              c.name.toUpperCase().includes(value.toUpperCase())
          );
          setSuggestions(mockSuggestions);
          setShowSuggestions(mockSuggestions.length > 0);
        }
      } else {
        // US market - simple mock
        const mockResults: CseCompany[] = [
          { symbol: 'AAPL', name: 'Apple Inc.', price: 178.50, percentageChange: 1.2 },
          { symbol: 'MSFT', name: 'Microsoft Corporation', price: 425.30, percentageChange: 0.8 },
          { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 175.40, percentageChange: -0.3 },
          { symbol: 'TSLA', name: 'Tesla Inc.', price: 248.60, percentageChange: 2.1 },
          { symbol: 'NVDA', name: 'NVIDIA Corporation', price: 880.20, percentageChange: 3.4 },
        ].filter(
          (c) =>
            c.symbol.toUpperCase().includes(value.toUpperCase()) ||
            c.name.toUpperCase().includes(value.toUpperCase())
        );
        setSuggestions(mockResults);
        setShowSuggestions(mockResults.length > 0);
      }
    },
    [selectedMarket]
  );

  // Handle suggestion selection
  const handleSelect = useCallback((symbol: string) => {
    setQuery(symbol.split('.')[0]); // Show short form
    setShowSuggestions(false);
    const marketPrefix = selectedMarket === 'CSE' ? 'CSE' : 'US';
    const fullTicker = `${marketPrefix}:${symbol}`;
    setSelectedStock(fullTicker);
    setActiveTab('overview');
  }, [selectedMarket]);

  // Handle Analyze button
  const handleAnalyze = useCallback(() => {
    if (!query.trim()) return;
    const marketPrefix = selectedMarket === 'CSE' ? 'CSE' : 'US';
    const ticker = query.trim().toUpperCase().split('.')[0];
    const fullTicker = `${marketPrefix}:${ticker}`;
    setSelectedStock(fullTicker);
    setShowSuggestions(false);
    setActiveTab('overview');
  }, [query, selectedMarket]);

  // Handle Enter key
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleAnalyze();
      }
      if (e.key === 'Escape') {
        setShowSuggestions(false);
      }
    },
    [handleAnalyze]
  );

  // Close suggestions on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (suggestRef.current && !suggestRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load from initialTicker
  useEffect(() => {
    if (initialTicker) {
      setSelectedStock(initialTicker);
      const tickerPart = initialTicker.replace(/^(CSE|US):/, '');
      setQuery(tickerPart);
    }
  }, [initialTicker]);

  const renderTabContent = () => {
    if (!resolvedTicker || !stockData) {
      return (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>🔍</div>
          <h3 style={styles.emptyTitle}>No stock selected</h3>
          <p style={styles.emptyText}>
            Search for a company above and click <strong>Analyze</strong> to view detailed analysis.
          </p>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return (
          <>
            <CompanyProfile
              name={stockData.profile.name}
              sector={stockData.profile.sector}
              industry={stockData.profile.industry}
              country={stockData.profile.country}
              marketCap={stockData.profile.market_cap}
              currency={stockData.currency}
              ticker={resolvedTicker}
              market={resolvedMarket}
            />
            <PriceChart
              ticker={resolvedTicker}
              market={resolvedMarket}
              currency={stockData.currency}
            />
          </>
        );
      case 'health':
        return <FinancialHealth currency={stockData.currency} />;
      case 'valuation':
        return (
          <ValuationAnalysis
            currentPrice={stockData.currentPrice}
            currency={stockData.currency}
          />
        );
      case 'technical':
        return <TechnicalAnalysis />;
      case 'risk':
        return <RiskAnalysis />;
      case 'scenarios':
        return (
          <ScenarioProjection
            currentPrice={stockData.currentPrice}
            currency={stockData.currency}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div>
      {/* Search Section */}
      <div style={styles.hero}>
        <h2 style={styles.heroTitle}>Stock Search</h2>
        <p style={styles.heroSubtext}>
          {selectedMarket === 'CSE'
            ? 'Search for CSE companies by name, symbol, or security code'
            : 'Search for US stocks by ticker symbol'}
        </p>
      </div>

      <div style={styles.searchCard} ref={suggestRef}>
        <div style={styles.searchRow}>
          <div style={styles.marketBadge}>
            {selectedMarket === 'CSE' ? 'CSE' : 'NYSE/NASDAQ'}
          </div>
          <input
            type="text"
            style={styles.searchInput}
            placeholder={
              selectedMarket === 'CSE'
                ? 'Search by name, symbol or code...'
                : 'Enter a US ticker (e.g. AAPL)'
            }
            value={query}
            onChange={(e) => handleSearchChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (suggestions.length > 0) setShowSuggestions(true);
            }}
          />
          <button style={styles.analyzeBtn} onClick={handleAnalyze}>
            Analyze
          </button>
        </div>

        {/* Autocomplete Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div style={styles.suggestionsDropdown}>
            {suggestions.slice(0, 10).map((c) => (
              <div
                key={c.symbol}
                style={styles.suggestionItem}
                onClick={() => handleSelect(c.symbol)}
              >
                <div>
                  <span style={styles.suggestionSymbol}>{c.symbol}</span>
                  <span style={styles.suggestionName}>{c.name}</span>
                </div>
                {c.price != null && (
                  <span style={styles.suggestionPrice}>
                    {selectedMarket === 'CSE' ? 'LKR' : '$'}
                    {c.price.toFixed(2)}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stock Detail Tabs */}
      {selectedStock && (
        <div style={styles.stockDetail}>
          {/* Tab Navigation */}
          <div style={styles.tabNav}>
            {ANALYSIS_TABS.map((tab) => (
              <button
                key={tab.id}
                style={{
                  ...styles.tabBtn,
                  ...(activeTab === tab.id ? styles.tabBtnActive : {}),
                }}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={styles.tabContent}>{renderTabContent()}</div>
        </div>
      )}
    </div>
  );
};

/* ── Styles ── */
const styles: Record<string, React.CSSProperties> = {
  hero: {
    marginBottom: 'var(--space-6)',
  },
  heroTitle: {
    fontSize: '1.5rem',
    fontWeight: 700,
    marginBottom: 4,
    color: 'var(--text-primary)',
  },
  heroSubtext: {
    color: 'var(--text-muted)',
    fontSize: '0.88rem',
  },
  searchCard: {
    backgroundColor: 'var(--bg-card)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border)',
    padding: 'var(--space-5)',
    marginBottom: 'var(--space-6)',
    position: 'relative',
  },
  searchRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--space-3)',
  },
  marketBadge: {
    padding: '6px 14px',
    backgroundColor: 'var(--accent-blue-light)',
    color: 'var(--accent-blue)',
    borderRadius: '6px',
    fontSize: '0.78rem',
    fontWeight: 700,
    whiteSpace: 'nowrap',
  },
  searchInput: {
    flex: 1,
    padding: '10px 14px',
    backgroundColor: 'var(--bg-input)',
    border: '1px solid var(--border-light)',
    borderRadius: '6px',
    color: 'var(--text-primary)',
    fontSize: '0.92rem',
    fontFamily: 'var(--font-sans)',
    outline: 'none',
    transition: 'border-color var(--transition-fast)',
  },
  analyzeBtn: {
    padding: '10px 24px',
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '0.88rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'var(--font-sans)',
    transition: 'background-color var(--transition-fast)',
    whiteSpace: 'nowrap',
  },
  suggestionsDropdown: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    marginTop: 4,
    backgroundColor: 'var(--bg-elevated)',
    border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-sm)',
    boxShadow: 'var(--shadow-lg)',
    zIndex: 500,
    maxHeight: 320,
    overflowY: 'auto',
  },
  suggestionItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 14px',
    cursor: 'pointer',
    borderBottom: '1px solid var(--border)',
    transition: 'background-color var(--transition-fast)',
  },
  suggestionSymbol: {
    fontWeight: 600,
    color: 'var(--accent-blue)',
    fontSize: '0.85rem',
    marginRight: 10,
  },
  suggestionName: {
    color: 'var(--text-secondary)',
    fontSize: '0.82rem',
  },
  suggestionPrice: {
    fontFamily: 'var(--font-mono)',
    fontSize: '0.82rem',
    color: 'var(--text-secondary)',
  },
  stockDetail: {
    marginTop: 'var(--space-4)',
  },
  tabNav: {
    display: 'flex',
    gap: 2,
    backgroundColor: 'var(--bg-card)',
    borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
    border: '1px solid var(--border)',
    borderBottom: 'none',
    overflowX: 'auto',
    padding: '4px 4px 0',
  },
  tabBtn: {
    padding: '10px 18px',
    backgroundColor: 'transparent',
    color: 'var(--text-muted)',
    border: 'none',
    borderBottom: '2px solid transparent',
    cursor: 'pointer',
    fontSize: '0.82rem',
    fontWeight: 500,
    fontFamily: 'var(--font-sans)',
    whiteSpace: 'nowrap',
    transition: 'all var(--transition-fast)',
    borderRadius: '6px 6px 0 0',
  },
  tabBtnActive: {
    color: 'var(--accent-blue)',
    backgroundColor: 'var(--accent-blue-light)',
    borderBottomColor: 'var(--accent-blue)',
    fontWeight: 600,
  },
  tabContent: {
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderTop: 'none',
    borderRadius: '0 0 var(--radius-md) var(--radius-md)',
    padding: 'var(--space-5)',
    minHeight: 400,
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '60px 20px',
    textAlign: 'center',
  },
  emptyIcon: {
    fontSize: '3rem',
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: '1.15rem',
    fontWeight: 600,
    marginBottom: 8,
    color: 'var(--text-primary)',
  },
  emptyText: {
    color: 'var(--text-muted)',
    fontSize: '0.9rem',
    maxWidth: 400,
  },
};

export default StockSearch;
