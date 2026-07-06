/* ═══════════════════════════════════════════════════════════════
   TechnicalAnalysis - Technical indicators display
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

const MOCK_TECHNICAL = {
  trend: 'Uptrend',
  momentum: 'Strong',
  rsi: 62.4,
  macd: 1.85,
  macdSignal: 1.42,
  macdHistogram: 0.43,
};

const generateRSIData = () => {
  return Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    rsi: 50 + Math.sin(i / 5) * 15 + (Math.random() - 0.5) * 8,
  }));
};

const generateMACDData = () => {
  return Array.from({ length: 30 }, (_, i) => {
    const macd = Math.sin(i / 4) * 2 + 1.5;
    const signal = Math.sin(i / 4 - 0.5) * 1.5 + 1.2;
    return {
      day: i + 1,
      macd: Math.round(macd * 100) / 100,
      signal: Math.round(signal * 100) / 100,
      histogram: Math.round((macd - signal) * 100) / 100,
    };
  });
};

const TechnicalAnalysis: React.FC = () => {
  const tech = MOCK_TECHNICAL;
  const rsiData = generateRSIData();
  const macdData = generateMACDData();

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={styles.tooltip}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Day {label}</div>
        {payload.map((entry: any) => (
          <div key={entry.name} style={{ color: entry.color, fontSize: '0.82rem' }}>
            {entry.name}: {Number(entry.value).toFixed(2)}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Technical Analysis</h3>
          <p style={styles.subtitle}>
            The stock's recent trend and momentum
          </p>
        </div>
        <div style={styles.badges}>
          <span className="chip chip--green">{tech.trend}</span>
          <span className={tech.momentum === 'Strong' ? 'chip chip--green' : 'chip chip--amber'}>
            {tech.momentum} Momentum
          </span>
        </div>
      </div>

      {/* Trend & Momentum */}
      <div style={styles.statsRow}>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Trend</div>
          <div style={styles.statValue}>{tech.trend}</div>
          <div style={styles.statDesc}>
            Price is above key moving averages, which often suggests positive momentum.
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Momentum (RSI)</div>
          <div style={styles.statValue}>{tech.rsi.toFixed(1)}</div>
          <div style={styles.statDesc}>
            RSI is leaning strong, indicating buying pressure is dominant.
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>MACD</div>
          <div style={styles.statValue}>{tech.macd.toFixed(2)}</div>
          <div style={styles.statDesc}>
            MACD is above the signal line, a bullish indication.
          </div>
        </div>
      </div>

      {/* RSI Chart */}
      <div style={styles.chartSection}>
        <h4 style={styles.chartTitle}>RSI (14)</h4>
        <div style={styles.chartContainer}>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={rsiData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="day" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} stroke="var(--border)" />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                stroke="var(--border)"
              />
              <Tooltip content={<CustomTooltip />} />
              {/* Reference lines */}
              <line x1="0" y1="70" x2="100%" y2="70" stroke="var(--accent-red)" strokeWidth={1} strokeDasharray="4 2" opacity={0.5} />
              <line x1="0" y1="30" x2="100%" y2="30" stroke="var(--accent-green)" strokeWidth={1} strokeDasharray="4 2" opacity={0.5} />
              <Line
                type="monotone"
                dataKey="rsi"
                stroke="var(--accent-purple)"
                strokeWidth={2}
                dot={false}
                name="RSI"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* MACD Chart */}
      <div style={styles.chartSection}>
        <h4 style={styles.chartTitle}>MACD</h4>
        <div style={styles.chartContainer}>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={macdData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="day" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} stroke="var(--border)" />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} stroke="var(--border)" />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="macd"
                stroke="var(--accent-blue)"
                strokeWidth={2}
                dot={false}
                name="MACD"
              />
              <Line
                type="monotone"
                dataKey="signal"
                stroke="var(--accent-amber)"
                strokeWidth={1.5}
                dot={false}
                strokeDasharray="4 2"
                name="Signal"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* MACD Histogram */}
      <div style={styles.chartSection}>
        <h4 style={styles.chartTitle}>MACD Histogram</h4>
        <div style={styles.chartContainer}>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={macdData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="day" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} stroke="var(--border)" />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} stroke="var(--border)" />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="histogram"
                fill="var(--accent-blue)"
                opacity={0.7}
                radius={[2, 2, 0, 0]}
                name="Histogram"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={styles.note}>
        Simple read: when the price stays above both moving averages, the trend is usually
        healthier. When it slips below them, momentum tends to cool off.
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
  badges: {
    display: 'flex',
    gap: 8,
  },
  statsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: 'var(--space-4)',
    marginBottom: 'var(--space-6)',
  },
  statCard: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    padding: '14px 16px',
    border: '1px solid var(--border)',
  },
  statLabel: {
    fontSize: '0.72rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 4,
  },
  statValue: {
    fontSize: '1.35rem',
    fontWeight: 700,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)',
    marginBottom: 6,
  },
  statDesc: {
    fontSize: '0.78rem',
    color: 'var(--text-muted)',
    lineHeight: 1.5,
  },
  chartSection: {
    marginBottom: 'var(--space-5)',
  },
  chartTitle: {
    fontSize: '0.85rem',
    fontWeight: 600,
    marginBottom: 'var(--space-3)',
    color: 'var(--text-secondary)',
  },
  chartContainer: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    padding: 'var(--space-4)',
    border: '1px solid var(--border)',
  },
  tooltip: {
    backgroundColor: 'var(--bg-elevated)',
    border: '1px solid var(--border-light)',
    borderRadius: '8px',
    padding: '8px 12px',
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

export default TechnicalAnalysis;
