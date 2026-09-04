"use client";

import { useEffect, useRef } from 'react';

const CARDS = [
  {
    id: 'total',
    label: 'Total Transactions',
    getValue: (s) => s.total_transactions.toLocaleString(),
    getSub: () => 'in selected period',
    accent: '#6366f1',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
    sparkColor: '#6366f1',
    trend: '+8.3%',
    trendUp: true,
  },
  {
    id: 'high',
    label: 'High Risk',
    getValue: (s) => s.high_risk_count.toLocaleString(),
    getSub: (s) => `${((s.high_risk_count / s.total_transactions) * 100).toFixed(1)}% of total`,
    accent: '#ef4444',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    ),
    sparkColor: '#ef4444',
    trend: '+2.1%',
    trendUp: true,
  },
  {
    id: 'medium',
    label: 'Medium Risk',
    getValue: (s) => s.medium_risk_count.toLocaleString(),
    getSub: (s) => `${((s.medium_risk_count / s.total_transactions) * 100).toFixed(1)}% of total`,
    accent: '#f59e0b',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    ),
    sparkColor: '#f59e0b',
    trend: '-1.4%',
    trendUp: false,
  },
  {
    id: 'low',
    label: 'Low Risk',
    getValue: (s) => s.low_risk_count.toLocaleString(),
    getSub: (s) => `${((s.low_risk_count / s.total_transactions) * 100).toFixed(1)}% of total`,
    accent: '#10b981',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    ),
    sparkColor: '#10b981',
    trend: '-3.2%',
    trendUp: false,
  },
  {
    id: 'flagged',
    label: 'Flagged Value',
    getValue: (s) =>
      s.flagged_amount_total >= 1_000_000
        ? `₹${(s.flagged_amount_total / 1_000_000).toFixed(1)}M`
        : `₹${(s.flagged_amount_total / 1_000).toFixed(0)}K`,
    getSub: (s) => `${s.high_risk_count.toLocaleString()} flagged txns`,
    accent: '#a855f7',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 3h12"/>
        <path d="M6 8h12"/>
        <path d="m6 13 8.5 8"/>
        <path d="M6 13h3"/>
        <path d="M9 13c6.667 0 6.667-10 0-10"/>
      </svg>
    ),
    sparkColor: '#a855f7',
    trend: '+12.7%',
    trendUp: true,
  },
];

// Tiny inline sparkline SVG
function Sparkline({ color, up }) {
  const points = up
    ? '0,18 8,15 16,12 24,10 32,8 40,6 48,4'
    : '0,4 8,6 16,5 24,9 32,11 40,14 48,18';
  return (
    <svg width="48" height="22" viewBox="0 0 48 22" fill="none" style={{ opacity: 0.6 }}>
      <defs>
        <linearGradient id={`spark-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3"/>
          <stop offset="100%" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <polyline points={points} stroke={color} strokeWidth="2" fill="none" strokeLinejoin="round" strokeLinecap="round"/>
    </svg>
  );
}

export default function KPICards({ stats }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
      gap: '16px', marginBottom: '22px',
    }}>
      {CARDS.map((card) => (
        <div
          key={card.id}
          id={`kpi-card-${card.id}`}
          style={{
            position: 'relative', overflow: 'hidden',
            borderRadius: '20px', padding: '22px 20px 18px',
            background: '#ffffff',
            border: `1px solid rgba(0,0,0,0.08)`,
            boxShadow: `0 4px 12px rgba(0,0,0,0.05)`,
            transition: 'transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease',
            cursor: 'default',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px) scale(1.01)';
            e.currentTarget.style.boxShadow = `0 12px 24px rgba(0,0,0,0.08), 0 0 0 1px ${card.accent}40`;
            e.currentTarget.style.borderColor = `${card.accent}40`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0) scale(1)';
            e.currentTarget.style.boxShadow = `0 4px 12px rgba(0,0,0,0.05)`;
            e.currentTarget.style.borderColor = 'rgba(0,0,0,0.08)';
          }}
        >
          {/* Top-right glow */}
          <div style={{
            position: 'absolute', top: '-30px', right: '-30px',
            width: '110px', height: '110px', borderRadius: '50%',
            background: card.accent, opacity: 0.08, filter: 'blur(30px)',
            pointerEvents: 'none',
          }} />

          {/* Icon + trend row */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{
              width: '40px', height: '40px', borderRadius: '12px',
              background: `${card.accent}18`,
              border: `1px solid ${card.accent}30`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: card.accent,
            }}>
              {card.icon}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Sparkline color={card.sparkColor} up={card.trendUp} />
              <span style={{
                fontSize: '11px', fontWeight: 700,
                color: card.trendUp ? '#10b981' : '#ef4444',
                padding: '2px 6px', borderRadius: '6px',
                background: card.trendUp ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
              }}>
                {card.trend}
              </span>
            </div>
          </div>

          {/* Value */}
          <div style={{
            fontSize: '30px', fontWeight: 800, color: '#0f172a',
            letterSpacing: '-1px', lineHeight: 1,
            fontVariantNumeric: 'tabular-nums',
          }}>
            {card.getValue(stats)}
          </div>

          {/* Label */}
          <div style={{
            fontSize: '12px', fontWeight: 600, color: card.accent,
            marginTop: '8px', letterSpacing: '0.4px', textTransform: 'uppercase',
          }}>
            {card.label}
          </div>

          {/* Sub */}
          <div style={{ fontSize: '11px', color: '#475569', marginTop: '3px' }}>
            {card.getSub(stats)}
          </div>

          {/* Bottom accent line */}
          <div style={{
            position: 'absolute', bottom: 0, left: '20px', right: '20px',
            height: '2px', borderRadius: '2px',
            background: `linear-gradient(90deg, transparent, ${card.accent}60, transparent)`,
          }} />
        </div>
      ))}
    </div>
  );
}
