/* ═══════════════════════════════════════════════════════════════
   RiskAnalysis - Risk metrics display
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';

const MOCK_RISK = {
  label: 'Moderate risk',
  score: 0.5,
  explanation:
    'This looks like a normal stock risk profile: not calm, not extreme.',
  metrics: {
    Volatility: '24.8%',
    'Largest drop': '-18.5%',
    Beta: '0.92',
    'Debt / equity': '0.62',
  },
};

const riskComparison = {
  benchmarkTicker: 'S&P 500',
  correlation: 0.72,
  relativeReturn: '+4.2%',
};

const getLabelChip = (label: string): { color: string; className: string } => {
  switch (label) {
    case 'Lower risk':
      return { color: 'var(--accent-green)', className: 'chip chip--green' };
    case 'Moderate risk':
      return { color: 'var(--accent-amber)', className: 'chip chip--amber' };
    default:
      return { color: 'var(--accent-red)', className: 'chip chip--red' };
  }
};

const getScoreColor = (score: number): string => {
  if (score >= 0.7) return 'var(--accent-green)';
  if (score >= 0.4) return 'var(--accent-amber)';
  return 'var(--accent-red)';
};

const RiskAnalysis: React.FC = () => {
  const risk = MOCK_RISK;
  const chip = getLabelChip(risk.label);
  const scoreColor = getScoreColor(risk.score);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Risk Analysis</h3>
          <p style={styles.subtitle}>
            How much the stock tends to bounce around and how sensitive it can be to market moves
          </p>
        </div>
        <div>
          <span className={chip.className}>{risk.label}</span>
        </div>
      </div>

      {/* Score Bar */}
      <div style={styles.scoreSection}>
        <div style={styles.scoreLabel}>
          Risk Score
          <span style={{ color: scoreColor, fontWeight: 700, marginLeft: 8 }}>
            {(risk.score * 100).toFixed(0)}%
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: 8 }}>
            (higher = lower risk)
          </span>
        </div>
        <div style={styles.scoreBarBg}>
          <div
            style={{
              ...styles.scoreBarFill,
              width: `${risk.score * 100}%`,
              backgroundColor: scoreColor,
            }}
          />
        </div>
      </div>

      {/* Explanation */}
      <div style={styles.explanationCard}>
        <p style={styles.explanationText}>{risk.explanation}</p>
      </div>

      {/* Metrics Grid */}
      <div style={styles.metricsGrid}>
        {Object.entries(risk.metrics).map(([key, value]) => (
          <div key={key} style={styles.metricCard}>
            <div style={styles.metricLabel}>{key}</div>
            <div style={styles.metricValue}>{value}</div>
          </div>
        ))}
      </div>

      {/* Comparison */}
      {riskComparison && (
        <div style={styles.comparisonCard}>
          <div style={styles.comparisonTitle}>Market Comparison</div>
          <div style={styles.comparisonGrid}>
            <div style={styles.comparisonItem}>
              <div style={styles.comparisonLabel}>Benchmark</div>
              <div style={styles.comparisonValue}>{riskComparison.benchmarkTicker}</div>
            </div>
            <div style={styles.comparisonItem}>
              <div style={styles.comparisonLabel}>Correlation</div>
              <div style={styles.comparisonValue}>{riskComparison.correlation.toFixed(2)}</div>
            </div>
            <div style={styles.comparisonItem}>
              <div style={styles.comparisonLabel}>Relative Return</div>
              <div style={{ ...styles.comparisonValue, color: 'var(--accent-green)' }}>
                {riskComparison.relativeReturn}
              </div>
            </div>
          </div>
          <div style={styles.comparisonNote}>
            Compared with {riskComparison.benchmarkTicker}, the stock has moved with a
            correlation of {riskComparison.correlation.toFixed(2)}. That means it often
            follows the market direction but still keeps its own personality.
          </div>
        </div>
      )}

      <div style={styles.note}>
        The stock can swing, so position size and time horizon matter more for this one.
        Lower volatility and beta generally mean a smoother ride.
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
    borderLeft: '3px solid var(--accent-amber)',
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
  comparisonCard: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    padding: '16px',
    border: '1px solid var(--border)',
    marginBottom: 'var(--space-5)',
  },
  comparisonTitle: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 'var(--space-3)',
  },
  comparisonGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 'var(--space-3)',
    marginBottom: 'var(--space-3)',
  },
  comparisonItem: {},
  comparisonLabel: {
    fontSize: '0.72rem',
    color: 'var(--text-muted)',
    marginBottom: 2,
  },
  comparisonValue: {
    fontSize: '1rem',
    fontWeight: 600,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)',
  },
  comparisonNote: {
    fontSize: '0.78rem',
    color: 'var(--text-muted)',
    lineHeight: 1.5,
  },
  note: {
    padding: '12px 0',
    fontSize: '0.82rem',
    color: 'var(--text-muted)',
    borderTop: '1px solid var(--border)',
    lineHeight: 1.5,
  },
};

export default RiskAnalysis;
