/* ═══════════════════════════════════════════════════════════════
   MarketOverview - CSE Market Dashboard
   Shows key metrics, gainers, losers, and most active tables
   ═══════════════════════════════════════════════════════════════ */

import React, { useEffect, useState } from 'react';
import type { MarketOverviewResponse, CseCompany } from '../services/api';
import { fetchCseMarketOverview } from '../services/api';

interface MarketOverviewProps {
  onSelectTicker: (ticker: string) => void;
}

/* ── Mock data for initial development ── */
const MOCK_MARKET: MarketOverviewResponse = {
  summary: {
    companiesTrading: 287,
    advancers: 112,
    decliners: 68,
    totalVolume: 45218652,
    totalMarketCap: 3852000000000,
    totalTurnover: 1245000000,
  },
  gainers: [
    { symbol: 'JKL.N0000', name: 'John Keells Holdings', price: 204.50, percentageChange: 5.2, change: 10.10 },
    { symbol: 'COMB.N0000', name: 'Commercial Bank', price: 98.20, percentageChange: 4.8, change: 4.50 },
    { symbol: 'LOLC.N0000', name: 'LOLC Holdings', price: 385.00, percentageChange: 4.1, change: 15.20 },
    { symbol: 'SAMP.N0000', name: 'Sampath Bank', price: 72.60, percentageChange: 3.9, change: 2.73 },
    { symbol: 'DIAL.N0000', name: 'Dialog Axiata', price: 11.20, percentageChange: 3.7, change: 0.40 },
    { symbol: 'HNB.N0000', name: 'Hatton National Bank', price: 185.40, percentageChange: 3.2, change: 5.75 },
    { symbol: 'CTC.N0000', name: 'Ceylon Tobacco', price: 1250.00, percentageChange: 2.8, change: 34.10 },
    { symbol: 'GRAN.N0000', name: 'Carson Cumberbatch', price: 335.00, percentageChange: 2.5, change: 8.18 },
    { symbol: 'NEST.N0000', name: 'Nestle Lanka', price: 1268.50, percentageChange: 2.3, change: 28.50 },
    { symbol: 'MEL.N0000', name: 'Millennium Housing', price: 18.20, percentageChange: 2.1, change: 0.37 },
  ],
  losers: [
    { symbol: 'EXPO.N0000', name: 'Expolanka Holdings', price: 152.30, percentageChange: -4.5, change: -7.18 },
    { symbol: 'RICH.N0000', name: 'Richard Pieris', price: 21.40, percentageChange: -3.8, change: -0.85 },
    { symbol: 'HAYC.N0000', name: 'Hayleys', price: 95.60, percentageChange: -3.2, change: -3.16 },
    { symbol: 'ACL.N0000', name: 'ACL Cables', price: 82.10, percentageChange: -2.9, change: -2.45 },
    { symbol: 'JETS.N0000', name: 'Jetwing Symphony', price: 17.80, percentageChange: -2.7, change: -0.49 },
    { symbol: 'LLUB.N0000', name: 'Lanka Lubricants', price: 117.40, percentageChange: -2.5, change: -3.01 },
    { symbol: 'CIC.N0000', name: 'CIC Holdings', price: 65.30, percentageChange: -2.3, change: -1.54 },
    { symbol: 'TKYO.N0000', name: 'Tokyo Cement', price: 46.70, percentageChange: -2.1, change: -1.00 },
    { symbol: 'CHEM.N0000', name: 'Chemical Industries', price: 88.90, percentageChange: -1.9, change: -1.72 },
    { symbol: 'PCH.N0000', name: 'PCH Holdings', price: 53.20, percentageChange: -1.7, change: -0.92 },
  ],
  mostActive: [
    { symbol: 'JKL.N0000', name: 'John Keells Holdings', price: 204.50, sharevolume: 2850000 },
    { symbol: 'COMB.N0000', name: 'Commercial Bank', price: 98.20, sharevolume: 1950000 },
    { symbol: 'LOLC.N0000', name: 'LOLC Holdings', price: 385.00, sharevolume: 1420000 },
    { symbol: 'SAMP.N0000', name: 'Sampath Bank', price: 72.60, sharevolume: 1280000 },
    { symbol: 'HNB.N0000', name: 'Hatton National Bank', price: 185.40, sharevolume: 950000 },
    { symbol: 'DIAL.N0000', name: 'Dialog Axiata', price: 11.20, sharevolume: 4200000 },
    { symbol: 'EXPO.N0000', name: 'Expolanka Holdings', price: 152.30, sharevolume: 880000 },
    { symbol: 'HAYC.N0000', name: 'Hayleys', price: 95.60, sharevolume: 620000 },
    { symbol: 'NEST.N0000', name: 'Nestle Lanka', price: 1268.50, sharevolume: 185000 },
    { symbol: 'CTC.N0000', name: 'Ceylon Tobacco', price: 1250.00, sharevolume: 142000 },
  ],
};

/* ── Format helpers ── */
const formatLKR = (value: number): string => {
  if (value >= 1e9) return `LKR ${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `LKR ${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `LKR ${(value / 1e3).toFixed(1)}K`;
  return `LKR ${value.toFixed(2)}`;
};

const formatVolume = (value: number): string => {
  return value.toLocaleString('en-US', { maximumFractionDigits: 0 });
};

/* ── Component ── */
const MarketOverview: React.FC<MarketOverviewProps> = ({ onSelectTicker }) => {
  const [data, setData] = useState<MarketOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const result = await fetchCseMarketOverview();
        setData(result);
        setError(null);
      } catch {
        // Fall back to mock data when backend is unavailable
        setData(MOCK_MARKET);
        setError(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="skeleton" style={{ height: 80, marginBottom: 12 }} />
        ))}
      </div>
    );
  }

  if (!data) {
    return <div style={styles.errorText}>Unable to load market data.</div>;
  }

  const { summary, gainers, losers, mostActive } = data;

  return (
    <div>
      {/* Hero Section */}
      <div style={styles.hero}>
        <h2 style={styles.heroTitle}>CSE Market Overview</h2>
        <p style={styles.heroSubtext}>
          Colombo Stock Exchange &bull; Live market summary
        </p>
      </div>

      {/* Key Metrics Row */}
      <div style={styles.metricsGrid}>
        <MetricCard
          label="Companies Trading"
          value={String(summary.companiesTrading)}
          color="var(--accent-blue)"
        />
        <MetricCard
          label="Advancers / Decliners"
          value={`${summary.advancers} / ${summary.decliners}`}
          color={summary.advancers > summary.decliners ? 'var(--accent-green)' : 'var(--accent-red)'}
        />
        <MetricCard
          label="Total Volume"
          value={formatVolume(summary.totalVolume)}
          color="var(--accent-cyan)"
        />
        <MetricCard
          label="Market Cap"
          value={formatLKR(summary.totalMarketCap)}
          color="var(--accent-purple)"
        />
        <MetricCard
          label="Turnover"
          value={formatLKR(summary.totalTurnover)}
          color="var(--accent-amber)"
        />
      </div>

      {/* Tables Row */}
      <div style={styles.tablesGrid}>
        {/* Top Gainers */}
        <div style={styles.tableCard}>
          <h3 style={styles.tableTitle}>
            <span style={{ color: 'var(--accent-green)' }}>▲</span> Top Gainers
          </h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Symbol</th>
                <th style={styles.thRight}>Price (LKR)</th>
                <th style={styles.thRight}>Change</th>
              </tr>
            </thead>
            <tbody>
              {gainers.map((c: CseCompany) => (
                <tr
                  key={c.symbol}
                  style={styles.tr}
                  onClick={() => onSelectTicker(`CSE:${c.symbol}`)}
                >
                  <td style={styles.td}>
                    <span style={styles.symbolLink}>{c.symbol}</span>
                  </td>
                  <td style={styles.tdRight}>{c.price?.toFixed(2)}</td>
                  <td style={{ ...styles.tdRight, color: 'var(--accent-green)' }}>
                    +{c.percentageChange?.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Top Losers */}
        <div style={styles.tableCard}>
          <h3 style={styles.tableTitle}>
            <span style={{ color: 'var(--accent-red)' }}>▼</span> Top Losers
          </h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Symbol</th>
                <th style={styles.thRight}>Price (LKR)</th>
                <th style={styles.thRight}>Change</th>
              </tr>
            </thead>
            <tbody>
              {losers.map((c: CseCompany) => (
                <tr
                  key={c.symbol}
                  style={styles.tr}
                  onClick={() => onSelectTicker(`CSE:${c.symbol}`)}
                >
                  <td style={styles.td}>
                    <span style={styles.symbolLink}>{c.symbol}</span>
                  </td>
                  <td style={styles.tdRight}>{c.price?.toFixed(2)}</td>
                  <td style={{ ...styles.tdRight, color: 'var(--accent-red)' }}>
                    {c.percentageChange?.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Most Active */}
        <div style={styles.tableCard}>
          <h3 style={styles.tableTitle}>
            <span style={{ color: 'var(--accent-amber)' }}>●</span> Most Active
          </h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Symbol</th>
                <th style={styles.thRight}>Price (LKR)</th>
                <th style={styles.thRight}>Volume</th>
              </tr>
            </thead>
            <tbody>
              {mostActive.map((c: CseCompany) => (
                <tr
                  key={c.symbol}
                  style={styles.tr}
                  onClick={() => onSelectTicker(`CSE:${c.symbol}`)}
                >
                  <td style={styles.td}>
                    <span style={styles.symbolLink}>{c.symbol}</span>
                  </td>
                  <td style={styles.tdRight}>{c.price?.toFixed(2)}</td>
                  <td style={styles.tdRight}>{formatVolume(c.sharevolume || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

/* ── Metric Card Sub-component ── */
interface MetricCardProps {
  label: string;
  value: string;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, color }) => (
  <div style={styles.metricCard}>
    <div style={styles.metricLabel}>{label}</div>
    <div style={{ ...styles.metricValue, color }}>{value}</div>
    <div
      style={{
        ...styles.metricBar,
        backgroundColor: color,
        opacity: 0.3,
      }}
    />
  </div>
);

/* ── Styles ── */
const styles: Record<string, React.CSSProperties> = {
  loadingContainer: {
    padding: '20px 0',
  },
  errorText: {
    color: 'var(--accent-red)',
    textAlign: 'center',
    padding: '40px',
    fontSize: '1rem',
  },
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
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 'var(--space-4)',
    marginBottom: 'var(--space-8)',
  },
  metricCard: {
    backgroundColor: 'var(--bg-card)',
    borderRadius: 'var(--radius-md)',
    padding: '18px 20px',
    border: '1px solid var(--border)',
    position: 'relative',
    overflow: 'hidden',
  },
  metricLabel: {
    fontSize: '0.78rem',
    fontWeight: 500,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 6,
  },
  metricValue: {
    fontSize: '1.35rem',
    fontWeight: 700,
    fontFamily: 'var(--font-mono)',
  },
  metricBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  tablesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
    gap: 'var(--space-6)',
  },
  tableCard: {
    backgroundColor: 'var(--bg-card)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border)',
    padding: 'var(--space-5)',
  },
  tableTitle: {
    fontSize: '0.92rem',
    fontWeight: 600,
    marginBottom: 'var(--space-4)',
    color: 'var(--text-primary)',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '8px 4px',
    fontSize: '0.72rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    borderBottom: '1px solid var(--border)',
  },
  thRight: {
    textAlign: 'right',
    padding: '8px 4px',
    fontSize: '0.72rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    borderBottom: '1px solid var(--border)',
  },
  tr: {
    cursor: 'pointer',
    transition: 'background-color var(--transition-fast)',
  },
  td: {
    padding: '8px 4px',
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border)',
  },
  tdRight: {
    padding: '8px 4px',
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    textAlign: 'right',
    fontFamily: 'var(--font-mono)',
    borderBottom: '1px solid var(--border)',
  },
  symbolLink: {
    color: 'var(--accent-blue)',
    fontWeight: 500,
  },
};

export default MarketOverview;
