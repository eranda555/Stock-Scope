/* ═══════════════════════════════════════════════════════════════
   FinancialHealth - Financial health analysis display
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';

interface FinancialHealthProps {
  currency: string;
}

const MOCK_HEALTH = {
  label: 'Healthy',
  score: 0.83,
  explanation:
    'The company looks financially solid, with enough cushion and decent profitability.',
  metrics: {
    'Cash cushion': '2.45',
    'Debt load': '0.62',
    'Operating margin': '24.5%',
    'Profit margin': '18.2%',
    'Returns on assets': '8.7%',
    'Free cash flow': 'LKR 45.2B',
  },
};

const getScoreColor = (score: number): string => {
  if (score >= 0.7) return 'var(--accent-green)';
  if (score >= 0.4) return 'var(--accent-amber)';
  return 'var(--accent-red)';
};

const getLabelChip = (label: string): { color: string; className: string } => {
  switch (label) {
    case 'Healthy':
      return { color: 'var(--accent-green)', className: 'chip chip--green' };
    case 'Mixed':
      return { color: 'var(--accent-amber)', className: 'chip chip--amber' };
    default:
      return { color: 'var(--accent-red)', className: 'chip chip--red' };
  }
};

const FinancialHealth: React.FC<FinancialHealthProps> = ({ currency }) => {
  const health = MOCK_HEALTH;
  const chip = getLabelChip(health.label);
  const scoreColor = getScoreColor(health.score);

  const formatMetricValue = (key: string, value: string): string => {
    if (key === 'Free cash flow' && value.startsWith('LKR')) return value;
    if (key === 'Free cash flow' && currency === 'LKR') return `LKR ${value}`;
    if (key === 'Free cash flow') return `$${value}`;
    return value;
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Financial Health</h3>
          <p style={styles.subtitle}>
            Whether the business looks sturdy enough to handle setbacks
          </p>
        </div>
        <div>
          <span className={chip.className}>{health.label}</span>
        </div>
      </div>

      {/* Score Bar */}
      <div style={styles.scoreSection}>
        <div style={styles.scoreLabel}>
          Health Score
          <span style={{ color: scoreColor, fontWeight: 700, marginLeft: 8 }}>
            {(health.score * 100).toFixed(0)}%
          </span>
        </div>
        <div style={styles.scoreBarBg}>
          <div
            style={{
              ...styles.scoreBarFill,
              width: `${health.score * 100}%`,
              backgroundColor: scoreColor,
            }}
          />
        </div>
      </div>

      {/* Explanation */}
      <div style={styles.explanationCard}>
        <p style={styles.explanationText}>{health.explanation}</p>
      </div>

      {/* Metrics Grid */}
      <div style={styles.metricsGrid}>
        {Object.entries(health.metrics).map(([key, value]) => (
          <div key={key} style={styles.metricCard}>
            <div style={styles.metricLabel}>{key}</div>
            <div style={styles.metricValue}>
              {formatMetricValue(key, value)}
            </div>
          </div>
        ))}
      </div>

      <div style={styles.note}>
        Simple read: a stronger cash cushion, manageable debt, and healthy margins
        usually make the company easier to hold through rough patches.
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {},
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
  },
  subtitle: {
    fontSize: '0.82rem',
    color: 'var(--text-muted)',
  },
  scoreSection: {
    marginBottom: 'var(--space-5)',
  },
  scoreLabel: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    marginBottom: 8,
    display: 'flex',
    alignItems: 'center',
  },
  scoreBarBg: {
    height: 8,
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  scoreBarFill: {
    height: '100%',
    borderRadius: 4,
    transition: 'width var(--transition-slow)',
  },
  explanationCard: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    padding: '14px 16px',
    marginBottom: 'var(--space-5)',
    borderLeft: '3px solid var(--accent-blue)',
  },
  explanationText: {
    color: 'var(--text-secondary)',
    fontSize: '0.9rem',
    lineHeight: 1.6,
    margin: 0,
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
    gap: 'var(--space-3)',
    marginBottom: 'var(--space-5)',
  },
  metricCard: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    padding: '12px 14px',
    border: '1px solid var(--border)',
  },
  metricLabel: {
    fontSize: '0.72rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 6,
  },
  metricValue: {
    fontSize: '1rem',
    fontWeight: 600,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)',
  },
  note: {
    padding: '12px 0',
    fontSize: '0.82rem',
    color: 'var(--text-muted)',
    borderTop: '1px solid var(--border)',
    lineHeight: 1.5,
  },
};

export default FinancialHealth;
