/* ═══════════════════════════════════════════════════════════════
   ScenarioProjection - Bull / Base / Bear scenario projections
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
  Area,
  AreaChart,
} from 'recharts';

interface ScenarioProjectionProps {
  currentPrice: number;
  currency: string;
}

const generateScenarioData = (currentPrice: number) => {
  const data = [];
  const now = new Date();
  const volatility = currentPrice * 0.005;

  for (let i = 0; i <= 30; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];

    const baseChange = Math.sin(i / 10) * currentPrice * 0.03 + (i / 30) * currentPrice * 0.02;
    const base = currentPrice + baseChange;

    const spread = volatility * Math.sqrt(i + 1) * 1.25;
    const bull = base * (1 + spread / currentPrice);
    const bear = base * (1 - spread / currentPrice);

    data.push({
      date: dateStr,
      base: Math.round(base * 100) / 100,
      bull: Math.round(bull * 100) / 100,
      bear: Math.round(bear * 100) / 100,
    });
  }
  return data;
};

const ScenarioProjection: React.FC<ScenarioProjectionProps> = ({
  currentPrice,
  currency,
}) => {
  const pricePrefix = currency === 'LKR' ? 'LKR ' : '$';
  const scenarioData = generateScenarioData(currentPrice);

  const lastBase = scenarioData[scenarioData.length - 1]?.base || currentPrice;
  const lastBull = scenarioData[scenarioData.length - 1]?.bull || currentPrice;
  const lastBear = scenarioData[scenarioData.length - 1]?.bear || currentPrice;

  const scenarios = [
    {
      label: 'Bull',
      value: lastBull,
      color: 'var(--accent-green)',
      description: `If the trend improves, the stock could reach about ${pricePrefix}${lastBull.toFixed(2)}.`,
    },
    {
      label: 'Base',
      value: lastBase,
      color: 'var(--accent-blue)',
      description: `The middle path suggests about ${pricePrefix}${lastBase.toFixed(2)}.`,
    },
    {
      label: 'Bear',
      value: lastBear,
      color: 'var(--accent-red)',
      description: `If conditions weaken, the stock could slip toward ${pricePrefix}${lastBear.toFixed(2)}.`,
    },
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={styles.tooltip}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4 }}>
          {label}
        </div>
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
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Bull / Base / Bear Scenarios</h3>
          <p style={styles.subtitle}>
            A simple range of possible paths, not a promise of what will happen
          </p>
        </div>
        <span className="chip chip--blue">30-day projection</span>
      </div>

      {/* Chart */}
      <div style={styles.chartContainer}>
        <ResponsiveContainer width="100%" height={380}>
          <AreaChart data={scenarioData}>
            <defs>
              <linearGradient id="colorBull" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent-green)" stopOpacity={0.15} />
                <stop offset="95%" stopColor="var(--accent-green)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="date"
              tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
              tickFormatter={(val: string) => {
                const d = new Date(val);
                return `${d.getMonth() + 1}/${d.getDate()}`;
              }}
              stroke="var(--border)"
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
              tickFormatter={(val: number) => `${pricePrefix}${val.toFixed(0)}`}
              stroke="var(--border)"
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="bull"
              stroke="var(--accent-green)"
              strokeWidth={2}
              fill="url(#colorBull)"
              name="Bull"
            />
            <Line
              type="monotone"
              dataKey="base"
              stroke="var(--accent-blue)"
              strokeWidth={2.5}
              strokeDasharray="6 3"
              dot={false}
              name="Base"
            />
            <Line
              type="monotone"
              dataKey="bear"
              stroke="var(--accent-red)"
              strokeWidth={2}
              dot={false}
              name="Bear"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Scenario Cards */}
      <div style={styles.scenarioGrid}>
        {scenarios.map((scenario) => (
          <div
            key={scenario.label}
            style={{
              ...styles.scenarioCard,
              borderTopColor: scenario.color,
            }}
          >
            <div style={styles.scenarioHeader}>
              <span
                style={{
                  ...styles.scenarioDot,
                  backgroundColor: scenario.color,
                }}
              />
              <span style={styles.scenarioLabel}>{scenario.label}</span>
            </div>
            <div style={{ ...styles.scenarioValue, color: scenario.color }}>
              {pricePrefix}
              {scenario.value.toFixed(2)}
            </div>
            <div style={styles.scenarioDesc}>{scenario.description}</div>
          </div>
        ))}
      </div>

      <div style={styles.note}>
        Beginner takeaway: the base case is the middle path, the bull case is the optimistic
        path, and the bear case is the caution path. These are model-based projections, not
        financial advice.
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
  chartContainer: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    padding: 'var(--space-4)',
    border: '1px solid var(--border)',
    marginBottom: 'var(--space-5)',
  },
  tooltip: {
    backgroundColor: 'var(--bg-elevated)',
    border: '1px solid var(--border-light)',
    borderRadius: '8px',
    padding: '10px 14px',
    boxShadow: 'var(--shadow-lg)',
  },
  scenarioGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 'var(--space-4)',
    marginBottom: 'var(--space-5)',
  },
  scenarioCard: {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-sm)',
    padding: '16px',
    border: '1px solid var(--border)',
    borderTop: '3px solid',
  },
  scenarioHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  scenarioDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
  },
  scenarioLabel: {
    fontSize: '0.78rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  },
  scenarioValue: {
    fontSize: '1.25rem',
    fontWeight: 700,
    fontFamily: 'var(--font-mono)',
    marginBottom: 8,
  },
  scenarioDesc: {
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

export default ScenarioProjection;
