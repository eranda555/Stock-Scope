/* ═══════════════════════════════════════════════════════════════
   PriceChart - Stock price chart with technical indicators
   Uses Recharts for interactive charting
   ═══════════════════════════════════════════════════════════════ */

import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine,
} from 'recharts';

interface PriceChartProps {
  ticker: string;
  market: string;
  currency: string;
}

/* ── Mock price data ── */
const generateMockPriceData = (ticker: string) => {
  const basePrice =
    ticker === 'AAPL' ? 178 : ticker === 'MSFT' ? 425 : ticker === 'GOOGL' ? 175 : 204;
  const volatility = basePrice * 0.02;
  const data = [];
  const startDate = new Date('2022-01-01');

  for (let i = 0; i < 90; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    const close = basePrice + (Math.random() - 0.5) * volatility * 2 + Math.sin(i / 10) * 10;
    const open = close + (Math.random() - 0.5) * volatility;
    const high = Math.max(open, close) + Math.random() * volatility;
    const low = Math.min(open, close) - Math.random() * volatility;
    const sma20 = data.length >= 20
      ? data.slice(-19).reduce((s, d) => s + d.close, close) / 20
      : close;
    const sma50 = basePrice + Math.sin(i / 25) * 15;

    data.push({
      date: date.toISOString().split('T')[0],
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      sma20: Math.round(sma20 * 100) / 100,
      sma50: Math.round(sma50 * 100) / 100,
      volume: Math.floor(Math.random() * 5000000) + 500000,
    });
  }
  return data;
};

type ChartView = 'price' | 'sma';

const PriceChart: React.FC<PriceChartProps> = ({ ticker, currency }) => {
  const [chartView, setChartView] = useState<ChartView>('price');
  const chartData = generateMockPriceData(ticker);

  const pricePrefix = currency === 'LKR' ? 'LKR ' : '$';
  const latestPrice = chartData[chartData.length - 1]?.close || 0;
  const firstPrice = chartData[0]?.close || 0;
  const changePct = ((latestPrice - firstPrice) / firstPrice) * 100;
  const isPositive = changePct >= 0;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={styles.tooltip}>
        <div style={styles.tooltipDate}>{label}</div>
        {payload.map((entry: any) => (
          <div key={entry.name} style={{ color: entry.color, fontSize: '0.82rem' }}>
            {entry.name}: {pricePrefix}
            {Number(entry.value).toFixed(2)}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Price Chart</h3>
          <p style={styles.subtitle}>
            {ticker} &bull; 90-day price history
          </p>
        </div>
        <div style={styles.priceInfo}>
          <span style={styles.currentPrice}>
            {pricePrefix}
            {latestPrice.toFixed(2)}
          </span>
          <span
            style={{
              ...styles.changeBadge,
              color: isPositive ? 'var(--accent-green)' : 'var(--accent-red)',
            }}
          >
            {isPositive ? '+' : ''}
            {changePct.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* View Toggle */}
      <div style={styles.viewToggle}>
        <button
          style={{
            ...styles.viewBtn,
            ...(chartView === 'price' ? styles.viewBtnActive : {}),
          }}
          onClick={() => setChartView('price')}
        >
          Price
        </button>
        <button
          style={{
            ...styles.viewBtn,
            ...(chartView === 'sma' ? styles.viewBtnActive : {}),
          }}
          onClick={() => setChartView('sma')}
        >
          Moving Averages
        </button>
      </div>

      {/* Chart */}
      <div style={styles.chartContainer}>
        <ResponsiveContainer width="100%" height={380}>
          {chartView === 'price' ? (
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                tickFormatter={(val: string) => {
                  const d = new Date(val);
                  return `${d.getMonth() + 1}/${d.getDate()}`;
                }}
                stroke="var(--border)"
              />
              <YAxis
                domain={['auto', 'auto']}
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                tickFormatter={(val: number) => `${pricePrefix}${val.toFixed(0)}`}
                stroke="var(--border)"
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="close"
                stroke="var(--accent-blue)"
                strokeWidth={2}
                fill="url(#colorClose)"
                name="Close"
              />
            </AreaChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                tickFormatter={(val: string) => {
                  const d = new Date(val);
                  return `${d.getMonth() + 1}/${d.getDate()}`;
                }}
                stroke="var(--border)"
              />
              <YAxis
                domain={['auto', 'auto']}
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                tickFormatter={(val: number) => `${pricePrefix}${val.toFixed(0)}`}
                stroke="var(--border)"
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="close"
                stroke="var(--accent-blue)"
                strokeWidth={2}
                dot={false}
                name="Close"
              />
              <Line
                type="monotone"
                dataKey="sma20"
                stroke="var(--accent-amber)"
                strokeWidth={1.5}
                dot={false}
                strokeDasharray="4 2"
                name="20-day SMA"
              />
              <Line
                type="monotone"
                dataKey="sma50"
                stroke="var(--accent-green)"
                strokeWidth={1.5}
                dot={false}
                strokeDasharray="4 2"
                name="50-day SMA"
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Legend / Quick Stats */}
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, backgroundColor: 'var(--accent-blue)' }} />
          <span>Close Price</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, backgroundColor: 'var(--accent-amber)' }} />
          <span>20-day SMA</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, backgroundColor: 'var(--accent-green)' }} />
          <span>50-day SMA</span>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border)',
    padding: 'var(--space-5)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 'var(--space-4)',
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
  priceInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  currentPrice: {
    fontSize: '1.5rem',
    fontWeight: 700,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)',
  },
  changeBadge: {
    fontSize: '0.92rem',
    fontWeight: 600,
    fontFamily: 'var(--font-mono)',
    padding: '4px 10px',
    borderRadius: '6px',
    backgroundColor: 'var(--bg-card)',
  },
  viewToggle: {
    display: 'flex',
    gap: 2,
    marginBottom: 'var(--space-4)',
    backgroundColor: 'var(--bg-card)',
    borderRadius: '6px',
    padding: 2,
    width: 'fit-content',
  },
  viewBtn: {
    padding: '6px 14px',
    border: 'none',
    backgroundColor: 'transparent',
    color: 'var(--text-muted)',
    fontSize: '0.78rem',
    fontWeight: 500,
    cursor: 'pointer',
    borderRadius: '4px',
    fontFamily: 'var(--font-sans)',
    transition: 'all var(--transition-fast)',
  },
  viewBtnActive: {
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
  },
  chartContainer: {
    marginBottom: 'var(--space-4)',
  },
  tooltip: {
    backgroundColor: 'var(--bg-elevated)',
    border: '1px solid var(--border-light)',
    borderRadius: '8px',
    padding: '10px 14px',
    boxShadow: 'var(--shadow-lg)',
  },
  tooltipDate: {
    fontSize: '0.78rem',
    color: 'var(--text-muted)',
    marginBottom: 6,
  },
  legend: {
    display: 'flex',
    gap: 'var(--space-5)',
    flexWrap: 'wrap',
    padding: '12px 0 0',
    borderTop: '1px solid var(--border)',
    fontSize: '0.82rem',
    color: 'var(--text-secondary)',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: '50%',
  },
};

export default PriceChart;
