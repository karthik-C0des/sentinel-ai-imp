"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from 'recharts';

const FLAG_LABELS = {
  unusual_amount: 'Unusual Amount',
  velocity_alert: 'Velocity Alert',
  unknown_device: 'Unknown Device',
  unexpected_location: 'Unexpected Location',
  matches_fraud_pattern: 'Fraud Pattern Match',
};

const PALETTE = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16'];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const pct = ((d.count / d._total) * 100).toFixed(1);
  return (
    <div style={{
      background: '#ffffff', border: '1px solid rgba(0,0,0,0.08)',
      borderRadius: '12px', padding: '12px 16px', fontFamily: "'Inter',sans-serif",
      fontSize: '13px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
    }}>
      <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>
        {FLAG_LABELS[d.flag] || d.flag}
      </div>
      <div style={{ color: payload[0].fill, fontWeight: 700, fontSize: '16px' }}>
        {d.count.toLocaleString()}
        <span style={{ fontWeight: 400, color: '#64748b', fontSize: '12px', marginLeft: '6px' }}>
          occurrences ({pct}%)
        </span>
      </div>
    </div>
  );
}

export default function FraudFlagsChart({ data }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  const max = Math.max(...data.map((d) => d.count));
  const chartData = data.map((d) => ({ ...d, _total: total }));

  return (
    <div style={{
      background: '#ffffff', border: '1px solid rgba(0,0,0,0.08)',
      borderRadius: '22px', padding: '28px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* BG glow */}
      <div style={{
        position: 'absolute', bottom: '-40px', left: '-40px', width: '200px', height: '200px',
        borderRadius: '50%', background: 'rgba(239,68,68,0.05)', filter: 'blur(40px)', pointerEvents: 'none',
      }} />

      <div style={{ marginBottom: '22px' }}>
        <div style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.3px' }}>
          Fraud Indicators
        </div>
        <div style={{ fontSize: '12px', color: '#475569', marginTop: '3px' }}>
          Top detected fraud flag types
        </div>
      </div>

      {/* Custom bar list (richer than recharts horizontal) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {chartData.map((d, i) => {
          const pct = (d.count / max) * 100;
          const color = PALETTE[i];
          return (
            <div key={d.flag}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 500 }}>
                  {FLAG_LABELS[d.flag] || d.flag}
                </span>
                <span style={{ fontSize: '12px', fontWeight: 700, color }}>
                  {d.count.toLocaleString()}
                </span>
              </div>
              <div style={{
                height: '8px', borderRadius: '8px',
                background: 'rgba(0,0,0,0.05)',
                position: 'relative', overflow: 'hidden',
              }}>
                <div style={{
                  position: 'absolute', inset: 0, right: `${100 - pct}%`,
                  background: `linear-gradient(90deg, ${color}aa, ${color})`,
                  borderRadius: '8px',
                  boxShadow: `0 0 12px ${color}60`,
                  transition: 'right 0.8s cubic-bezier(0.16,1,0.3,1)',
                }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Total */}
      <div style={{
        marginTop: '20px', paddingTop: '16px',
        borderTop: '1px solid rgba(0,0,0,0.05)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontSize: '12px', color: '#475569' }}>Total detections</span>
        <span style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>{total.toLocaleString()}</span>
      </div>
    </div>
  );
}
