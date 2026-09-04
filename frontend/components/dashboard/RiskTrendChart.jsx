"use client";

import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';

const COLORS = { high: '#ef4444', medium: '#f59e0b', low: '#10b981' };
const GRAD_OPACITY = { high: [0.5, 0.03], medium: [0.35, 0.02], low: [0.25, 0.01] };

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s, e) => s + (e.value || 0), 0);
  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid rgba(0,0,0,0.08)',
      borderRadius: '14px', padding: '14px 18px',
      fontFamily: "'Inter',sans-serif", fontSize: '13px', color: '#0f172a',
      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
      minWidth: '170px',
    }}>
      <div style={{ fontWeight: 700, marginBottom: '10px', color: '#0f172a', fontSize: '14px' }}>{label}</div>
      {[...payload].reverse().map((entry) => (
        <div key={entry.dataKey} style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          justifyContent: 'space-between', marginBottom: '6px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: entry.color, boxShadow: `0 0 6px ${entry.color}` }} />
            <span style={{ color: '#94a3b8', fontSize: '12px' }}>{entry.name.charAt(0).toUpperCase() + entry.name.slice(1)}</span>
          </div>
          <span style={{ fontWeight: 700, color: entry.color }}>{entry.value?.toLocaleString()}</span>
        </div>
      ))}
      <div style={{
        borderTop: '1px solid rgba(0,0,0,0.07)', marginTop: '8px', paddingTop: '8px',
        display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px',
      }}>
        <span>Total</span>
        <strong style={{ color: '#0f172a' }}>{total.toLocaleString()}</strong>
      </div>
    </div>
  );
}

export default function RiskTrendChart({ data }) {
  const sampled = data.length > 30
    ? data.filter((_, i) => i % Math.ceil(data.length / 30) === 0 || i === data.length - 1)
    : data;

  // Find the day with the highest high-risk count for reference line
  const maxHighDay = sampled.reduce((m, d) => d.high > m.high ? d : m, sampled[0]);

  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid rgba(0,0,0,0.08)',
      borderRadius: '22px', padding: '28px 28px 20px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* BG accent */}
      <div style={{
        position: 'absolute', top: '-60px', right: '-60px', width: '240px', height: '240px',
        borderRadius: '50%', background: 'rgba(99,102,241,0.04)', filter: 'blur(40px)', pointerEvents: 'none',
      }} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <div style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.3px' }}>
            Risk Trend
          </div>
          <div style={{ fontSize: '12px', color: '#475569', marginTop: '3px' }}>
            Daily transaction volume by risk level
          </div>
        </div>
        <div style={{ display: 'flex', gap: '16px' }}>
          {[
            { label: 'High', color: COLORS.high },
            { label: 'Med', color: COLORS.medium },
            { label: 'Low', color: COLORS.low },
          ].map(({ label, color }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: '#64748b' }}>
              <div style={{ width: '22px', height: '3px', borderRadius: '2px', background: color, boxShadow: `0 0 6px ${color}60` }} />
              {label}
            </div>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={sampled} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <defs>
            {Object.entries(COLORS).map(([key, color]) => (
              <linearGradient key={key} id={`tg-${key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={GRAD_OPACITY[key][0]} />
                <stop offset="100%" stopColor={color} stopOpacity={GRAD_OPACITY[key][1]} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="1 8" stroke="rgba(0,0,0,0.04)" vertical={false} />
          <XAxis
            dataKey="date" tick={{ fill: '#334155', fontSize: 10, fontFamily: "'Inter',sans-serif" }}
            tickLine={false} axisLine={false} interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#334155', fontSize: 10, fontFamily: "'Inter',sans-serif" }}
            tickLine={false} axisLine={false} width={36}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(0,0,0,0.06)', strokeWidth: 1, strokeDasharray: '4 4' }} />
          <ReferenceLine x={maxHighDay?.date} stroke="rgba(239,68,68,0.2)" strokeDasharray="4 4" />
          {['low', 'medium', 'high'].map((level) => (
            <Area
              key={level} type="monotone" dataKey={level} name={level}
              stackId="1" stroke={COLORS[level]} strokeWidth={2.5}
              fill={`url(#tg-${level})`} dot={false}
              activeDot={{ r: 5, strokeWidth: 0, fill: COLORS[level], style: { filter: `drop-shadow(0 0 6px ${COLORS[level]})` } }}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
