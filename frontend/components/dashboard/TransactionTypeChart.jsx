"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = ['#6366f1', '#a855f7', '#06b6d4', '#10b981', '#f59e0b'];
const ICONS = { Purchase: '🛒', Transfer: '↔️', Withdrawal: '💳', Payment: '💸', Refund: '↩️' };

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div style={{
      background: '#ffffff', border: '1px solid rgba(0,0,0,0.08)',
      borderRadius: '12px', padding: '12px 16px', fontFamily: "'Inter',sans-serif",
      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
    }}>
      <div style={{ fontWeight: 700, color: d.payload.fill, marginBottom: '4px', fontSize: '14px' }}>
        {ICONS[d.name] || ''} {d.name}
      </div>
      <div style={{ color: '#0f172a', fontWeight: 700, fontSize: '16px' }}>
        {d.value.toLocaleString()}
        <span style={{ fontWeight: 400, color: '#64748b', fontSize: '12px', marginLeft: '6px' }}>
          ({d.payload.percent?.toFixed(1)}%)
        </span>
      </div>
    </div>
  );
}

function CustomLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.07) return null;
  const RADIAN = Math.PI / 180;
  const r = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + r * Math.cos(-midAngle * RADIAN);
  const y = cy + r * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="rgba(255,255,255,0.9)" textAnchor="middle"
      dominantBaseline="central" fontSize={12} fontWeight={700} fontFamily="'Inter',sans-serif">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export default function TransactionTypeChart({ data }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  const chartData = data.map((d) => ({
    ...d, name: d.type, value: d.count, percent: (d.count / total) * 100,
  }));

  return (
    <div style={{
      background: '#ffffff', border: '1px solid rgba(0,0,0,0.08)',
      borderRadius: '22px', padding: '28px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* BG glow */}
      <div style={{
        position: 'absolute', top: '-40px', right: '-40px', width: '200px', height: '200px',
        borderRadius: '50%', background: 'rgba(99,102,241,0.06)', filter: 'blur(40px)', pointerEvents: 'none',
      }} />

      <div style={{ marginBottom: '22px' }}>
        <div style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.3px' }}>
          Transaction Mix
        </div>
        <div style={{ fontSize: '12px', color: '#475569', marginTop: '3px' }}>
          Volume by transaction category
        </div>
      </div>

      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
        {/* Donut */}
        <div style={{ flex: '0 0 160px', height: '160px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData} cx="50%" cy="50%"
                innerRadius={48} outerRadius={75}
                paddingAngle={3} dataKey="value"
                labelLine={false} label={CustomLabel}
                strokeWidth={0}
              >
                {chartData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend list */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {chartData.map((d, i) => (
            <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '10px', height: '10px', borderRadius: '50%', flexShrink: 0,
                background: COLORS[i], boxShadow: `0 0 8px ${COLORS[i]}80`,
              }} />
              <div style={{ flex: 1, fontSize: '13px', color: '#94a3b8', fontWeight: 500 }}>
                {ICONS[d.name] || ''} {d.name}
              </div>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>
                {d.percent.toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Total */}
      <div style={{
        marginTop: '18px', paddingTop: '14px',
        borderTop: '1px solid rgba(0,0,0,0.05)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontSize: '12px', color: '#475569' }}>Total transactions</span>
        <span style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>{total.toLocaleString()}</span>
      </div>
    </div>
  );
}
