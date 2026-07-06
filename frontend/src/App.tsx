/* ═══════════════════════════════════════════════════════════════
   Stock Scope - Main Application Shell
   ═══════════════════════════════════════════════════════════════ */

import React, { useState, useCallback } from 'react';
import Layout from './components/Layout';
import MarketOverview from './components/MarketOverview';
import StockSearch from './components/StockSearch';
import Watchlist from './components/Watchlist';

export type Section = 'market-overview' | 'stock-search' | 'watchlist';

export interface AppState {
  activeSection: Section;
  selectedMarket: 'CSE' | 'US';
  selectedTicker: string | null;
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    activeSection: 'market-overview',
    selectedMarket: 'CSE',
    selectedTicker: null,
  });

  const navigateTo = useCallback((section: Section) => {
    setState((prev) => ({ ...prev, activeSection: section }));
  }, []);

  const setMarket = useCallback((market: 'CSE' | 'US') => {
    setState((prev) => ({ ...prev, selectedMarket: market }));
  }, []);

  const selectTicker = useCallback((ticker: string) => {
    setState((prev) => ({
      ...prev,
      selectedTicker: ticker,
      activeSection: 'stock-search',
    }));
  }, []);

  const renderContent = () => {
    switch (state.activeSection) {
      case 'market-overview':
        return <MarketOverview onSelectTicker={selectTicker} />;
      case 'stock-search':
        return (
          <StockSearch
            selectedMarket={state.selectedMarket}
            initialTicker={state.selectedTicker}
            onSelectTicker={selectTicker}
          />
        );
      case 'watchlist':
        return <Watchlist onSelectTicker={selectTicker} />;
      default:
        return <MarketOverview onSelectTicker={selectTicker} />;
    }
  };

  return (
    <Layout
      activeSection={state.activeSection}
      selectedMarket={state.selectedMarket}
      onNavigate={navigateTo}
      onMarketChange={setMarket}
    >
      <div className="animate-fade-in" style={{ minHeight: '100%' }}>
        {renderContent()}
      </div>
    </Layout>
  );
};

export default App;
