/* ═══════════════════════════════════════════════════════════════
   Watchlist - Saved tickers overview dashboard
   ═══════════════════════════════════════════════════════════════ */

import React, { useState } from 'react';

interface WatchlistProps {
  onSelectTicker: (ticker: string) => void;
}

interface WatchlistItem {
  ticker: string;
  market: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
  signal: 'Strong Buy' | 'Buy' | 'Hold' | 'Sell' | 'Strong Sell';
}

const MOCK_WATCHLIST: WatchlistItem[] = [
  {
    ticker: 'JKH.N0000',
    market: 'CSE',
    name: 'John Keells Holdings',
    price: 204.50,
    change: 10.10,
    changePct: 5.2,
    signal: 'Buy',
  },
  {
    ticker: 'COMB.N0000',
    market: 'CSE',
    name: 'Commercial Bank',
    price: 98.20,
    change: 4.50,
    changePct: 4.8,
    signal: 'Strong Buy',
  },
  {
    ticker: 'LOLC.N0000',
    market: 'CSE',
    name: 'LOLC Holdings',
    price: 385.00,
    change: 15.20,
    changePct: 4.1,
    signal: 'Hold',
  },
  {
    ticker: 'AAPL',
    market: 'US',
    name: 'Apple Inc.',
    price: 178.50,
    change: -1.20,
    changePct: -0.67,
    signal: 'Hold',
  },
];

const getSignalColor = (signal: string): string => {
  switch (signal) {
    case 'Strong Buy':
      return 'var(--accent-green)';
    case 'Buy':
      return '#34d399';
    case 'Hold':
      return 'var(--accent-amber)';
    case 'Sell':
      return '#fb923c';
    case 'Strong Sell':
      return 'var(--accent-red)';
    default:
      return 'var(--text-muted)';
  }
};

const getSignalBg = (signal: string): string => {
  switch (signal) {
    case 'Strong Buy':
      return 'var(--accent-green-light)';
    case 'Buy':
      return 'rgba(52, 211, 153, 0.12)';
    case 'Hold':
      return 'var(--accent-amber-light)';
    case 'Sell':
      return 'rgba(251, 146, 60, 0.12)';
    case 'Strong Sell':
      return 'var(--accent-red-light)';
    default:
      return 'transparent';
  }
};

const Watchlist: React.FC<WatchlistProps> = ({ onSelectTicker }) => {
  const [watchlist] = useState<WatchlistItem[]>(MOCK_WATCHLIST);

  return (
    <div>
      <div style={styles.hero}>
        <h2 style={styles.heroTitle}>Watchlist</h2>
        <p style={styles.heroSubtext}>
          Your saved tickers &bull; {watchlist.length} securities
        </p>
      </div>

      {watchlist.length === 0 ? (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>⭐</div>
          <h3 style={styles.emptyTitle}>Your watchlist is empty</h3>
          <p style={styles.emptyText}>
            Search for stocks and add them to your watchlist to track them here.
          </p>
        </div>
      ) : (
        <div style={styles.grid}>
          {watchlist.map((item) => (
            <div
              key={item.ticker}
              style={styles.card}
              onClick={() =>
                onSelectTicker(`${item.market}:${item.ticker}`)
              }
            >
              <div style={styles.cardHeader}>
                <div>
                  <div style={styles.cardMarket}>
                    <span
                      className={
                        item.market === 'CSE' ? 'chip chip--green' : 'chip chip--blue'
                      }
                    >
                      {item.market}
                    </span>
                  </div>
                  <div style={styles.cardTicker}>{item.ticker}</div>
                  <div style={styles.cardName}>{item.name}</div>
                </div>
                <div
                  style={{
                    ...styles.signalBadge,
                    backgroundColor: getSignalBg(item.signal),
                    color: getSignalColor(item.signal),
                  }}
                >
                  {item.signal}
                </div>
              </div>

              <div style={styles.cardBody}>
                <div style={styles.cardPrice}>
                  {item.market === 'CSE' ? 'LKR ' : '$'}
                  {item.price.toFixed(2)}
                </div>
                <div
                  style={{
                    ...styles.cardChange,
                    color: item.change >= 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                  }}
                >
                  {item.change >= 0 ? '+' : ''}
                  {item.change.toFixed(2)} ({item.changePct >= 0 ? '+' : ''}
                  {item.changePct.toFixed(2)}%)
                </div>
              </div>

              <div style={styles.cardFooter}>
                <button
                  style={styles.viewBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectTicker(`${item.market}:${item.ticker}`);
                  }}
                >
                  View Analysis
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  hero: {
    marginBottom: 'var(--space-8)',
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
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '80px 20px',
    textAlign: 'center',
  },
  emptyIcon: {
    fontSize: '3.5rem',
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
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: 'var(--space-5)',
  },
  card: {
    backgroundColor: 'var(--bg-card)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border)',
    cursor: 'pointer',
    transition: 'all var(--transition-normal)',
    overflow: 'hidden',
  },
  cardHeader: {
    padding: '16px 18px 12px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid var(--border)',
  },
  cardMarket: {
    marginBottom: 6,
  },
  cardTicker: {
    fontSize: '1.1rem',
    fontWeight: 700,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)',
    marginBottom: 2,
  },
  cardName: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
  },
  signalBadge: {
    fontSize: '0.7rem',
    fontWeight: 700,
    padding: '3px 10px',
    borderRadius: '999px',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  cardBody: {
    padding: '14px 18px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardPrice: {
    fontSize: '1.3rem',
    fontWeight: 700,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)',
  },
  cardChange: {
    fontSize: '0.85rem',
    fontWeight: 600,
    fontFamily: 'var(--font-mono)',
  },
  cardFooter: {
    padding: '10px 18px',
    borderTop: '1px solid var(--border)',
    backgroundColor: 'var(--bg-secondary)',
  },
  viewBtn: {
    width: '100%',
    padding: '8px',
    backgroundColor: 'transparent',
    color: 'var(--accent-blue)',
    border: '1px solid var(--accent-blue)',
    borderRadius: '6px',
    fontSize: '0.8rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'var(--font-sans)',
    transition: 'all var(--transition-fast)',
  },
};

export default Watchlist;
