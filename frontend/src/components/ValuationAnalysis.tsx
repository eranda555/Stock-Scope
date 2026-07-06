/* ═══════════════════════════════════════════════════════════════
   ValuationAnalysis - Valuation analysis display
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface ValuationAnalysisProps {
  currentPrice: number;
  currency: string;
}

const MOCK_VALUATION = {
  label: 'Fair value',
  score: 0.6,
  explanation:
    'The stock does not look obviously cheap or expensive at the moment.',
  currentPrice: 204.50,
  estimatedFairValue: 218.75,
  upsidePct: 6.97,
  metrics: {
    'P/E': '15.2',
    'Forward P/E': '12.8',
    'Price / Book': '1.85',
    'Price / Sales': '2.1',
    'PEG': '1.45',
    'Upside to fair value': '6.97%',
  },
};

const getLabelChip = (label: string): { color: string; className: string } => {
  switch (label) {
    case 'Looks attractive':
      return { color: 'var(--accent-green)', className: 'chip chip--green' };
    case 'Fair value':
      return { color: 'var(--accent-amber)', className: 'chip chip--amber' };
    default:
      return { color: 'var(--accent-red)', className: 'chip chip--red' };
  }
};

const ValuationAnalysis: React.FC<ValuationAnalysisProps> = ({ currency }) => {
  const val = MOCK_VALUATION;
  const chip = getLabelChip(val.label);
  const pricePrefix = currency === 'LKR' ? 'LKR ' : '$';

  const chartData = [
    {
      name: 'Current Price',
      value: val.currentPrice,
      fill: 'var(--accent-blue)',
    },
    {
      name: 'Fair Value',
      value: val.estimatedFairValue,
      fill: 'var(--accent-green)',
    },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={styles.tooltip}>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          {payload[0].payload.name}
        </div>
        <div style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
          {pricePrefix}
          {Number(payload[0].value).toFixed(2)}
        </div>
      </div>
    );
  };

  const getScoreColor = (score: number): string => {
    if (score >= 0.7) return 'var(--accent-green)';
    if (score >= 0.4) return 'var(--accent-amber)';
    return 'var(--accent-red)';
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Valuation</h3>
          <p style={styles.subtitle}>
            Whether the stock looks cheap, fair, or expensive compared with its own earnings signals
          </p>
        </div>
        <div>
          <span className={chip.className}>{val.label}</span>
        </div>
      </div>

      {/* Score Bar */}
      <div style={styles.scoreSection}>
        <div style={styles.scoreLabel}>
          Value Score
          <span style={{ color: getScoreColor(val.score), fontWeight: 700, marginLeft: 8 }}>
            {(val.score * 100).toFixed(0)}%
          </span>
        </div>
        <div style={styles.scoreBarBg}>
          <div
            style={{
              ...styles.scoreBarFill,
              width: `${val.score * 100}%`,
              backgroundColor: getScoreColor(val.score),
            }}
          />
        </div>
      </div>

      {/* Explanation */}
      <div style={styles.explanationCard}>
        <p style={styles.explanationText}>{val.explanation}</p>
      </div>

      {/* Bar Chart */}
      <div style={styles.chartContainer}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
              tickFormatter={(v: number) => `${pricePrefix}${v.toFixed(0)}`}
              stroke="var(--border)"
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
              stroke="var(--border)"
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={36}>
              {chartData.map((entry, index) => (
                <rect key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics Grid */}
      <div style={styles.metricsGrid}>
        {Object.entries(val.metrics).map(([key, value]) => (
          <div key={key} style={styles.metricCard}>
            <div style={styles.metricLabel}>{key}</div>
            <div style={styles.metricValue}>{value}</div>
          </div>
        ))}
      </div>

      <div style={styles.note}>
        Beginner takeaway: if the fair-value bar is well above the current price,
        the market may be pricing in extra upside. If it is below,
        the stock may already be expensive.
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
  chartContainer: {
    marginBottom: 'var(--space-5)',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
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
    fontSize: '0.95rem',
    fontWeight: 600,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)',
  },
  tooltip: {
    backgroundColor: 'var(--bg-elevated)',
    border: '1px solid var(--border-light)',
    borderRadius: '8px',
    padding: '10px 14px',
    boxShadow: 'var(--shadow-lg)',
  },
  note: {
    padding: '12px 0',
    fontSize: '0.82rem',
    color: 'var(--text-muted)',
    borderTop: '1px solid var(--border)',
    lineHeight: 1.5,
  },
};

export default ValuationAnalysis;
