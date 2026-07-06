/* ═══════════════════════════════════════════════════════════════
   CompanyProfile - Displays company information overview
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';

interface CompanyProfileProps {
  name: string;
  sector: string;
  industry: string;
  country: string;
  marketCap: number;
  currency: string;
  ticker: string;
  market: string;
}

const formatMarketCap = (value: number, currency: string): string => {
  const prefix = currency === 'LKR' ? 'LKR ' : '$';
  if (value >= 1e12) return `${prefix}${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `${prefix}${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${prefix}${(value / 1e6).toFixed(2)}M`;
  return `${prefix}${value.toLocaleString()}`;
};

const CompanyProfile: React.FC<CompanyProfileProps> = ({
  name,
  sector,
  industry,
  country,
  marketCap,
  currency,
  ticker,
  market,
}) => {
  const infoItems = [
    { label: 'Company', value: name },
    { label: 'Ticker', value: ticker },
    { label: 'Market', value: market === 'CSE' ? 'Colombo Stock Exchange' : 'US Markets' },
    { label: 'Sector', value: sector },
    { label: 'Industry', value: industry },
    { label: 'Country', value: country },
    { label: 'Market Cap', value: formatMarketCap(marketCap, currency) },
  ];

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Company Overview</h3>
          <p style={styles.subtitle}>
            Key information about the company and its market position
          </p>
        </div>
        <div style={styles.badges}>
          <span className="chip chip--green">{name}</span>
          <span className="chip chip--blue">{market === 'CSE' ? 'CSE' : 'US'}</span>
        </div>
      </div>

      <div style={styles.grid}>
        {infoItems.map((item) => (
          <div key={item.label} style={styles.infoCard}>
            <div style={styles.infoLabel}>{item.label}</div>
            <div style={styles.infoValue}>{item.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginBottom: 'var(--space-6)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 'var(--space-5)',
    flexWrap: 'wrap',
    gap: 'var(--space-3)',
  },
  title: {
    fontSize: '1.08rem',
    fontWeight: 600,
    marginBottom: 4,
    color: 'var(--text-primary)',
  },
  subtitle: {
    fontSize: '0.82rem',
    color: 'var(--text-muted)',
  },
  badges: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
    gap: 'var(--space-3)',
  },
  infoCard: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    padding: '12px 14px',
    border: '1px solid var(--border)',
  },
  infoLabel: {
    fontSize: '0.72rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 4,
  },
  infoValue: {
    fontSize: '0.9rem',
    fontWeight: 500,
    color: 'var(--text-primary)',
  },
};

export default CompanyProfile;
