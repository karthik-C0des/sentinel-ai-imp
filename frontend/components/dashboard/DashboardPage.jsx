"use client";

import { useState, useMemo, useEffect, useRef } from 'react';
import { getDashboardStats } from './mockDashboardData';
import KPICards from './KPICards';
import RiskTrendChart from './RiskTrendChart';
import FraudFlagsChart from './FraudFlagsChart';
import TransactionTypeChart from './TransactionTypeChart';
import RecentHighRiskTable from './RecentHighRiskTable';

const DAY_OPTIONS = [
  { label: '7D', value: 7 },
  { label: '30D', value: 30 },
  { label: '90D', value: 90 },
];

export default function DashboardPage() {
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [visibleDays, setVisibleDays] = useState(30);
  const [mounted, setMounted] = useState(false);

  const [stats, setStats] = useState(null);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    
    // Slight delay before visual loading just to debounce
    const t = setTimeout(async () => {
      setVisibleDays(days);
      const data = await getDashboardStats(days);
      if (active) {
        setStats(data);
        setLoading(false);
      }
    }, 100);
    
    return () => {
      active = false;
      clearTimeout(t);
    };
  }, [days]);

  return (
    <div
      id="aml-dashboard"
      style={{
        minHeight: 'calc(100vh - 140px)',
        fontFamily: "'Inter', 'Euclid Circular A', sans-serif",
        color: '#0f172a',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#ffffff',
        borderRadius: '24px',
        padding: '32px 40px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.05), inset 0 0 0 1px rgba(0,0,0,0.05)',
      }}
    >
      {/* Ambient background blobs */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
        background: 'radial-gradient(ellipse 80% 60% at 20% 0%, rgba(18,184,176,0.07) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 80% 100%, rgba(99,102,241,0.06) 0%, transparent 60%), radial-gradient(ellipse 50% 40% at 50% 50%, rgba(239,68,68,0.04) 0%, transparent 60%)',
      }} />

      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* ── Header ── */}
        <div style={{
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
          marginBottom: '32px', flexWrap: 'wrap', gap: '16px',
        }}>
          <div>
            {/* Eyebrow */}
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px',
              padding: '4px 12px', borderRadius: '20px', marginBottom: '10px',
              background: 'rgba(18,184,176,0.1)', border: '1px solid rgba(18,184,176,0.25)',
              fontSize: '11px', fontWeight: 700, letterSpacing: '1.5px',
              textTransform: 'uppercase', color: '#12B8B0',
            }}>
              <span style={{
                width: '6px', height: '6px', borderRadius: '50%',
                background: '#12B8B0', boxShadow: '0 0 8px #12B8B0',
                animation: mounted ? 'pulse-dot 2s ease-in-out infinite' : 'none',
                display: 'inline-block',
              }} />
              Live Monitor
            </div>

            <h1 style={{
              fontSize: '34px', fontWeight: 900, margin: 0, lineHeight: 1,
              color: '#0f172a', letterSpacing: '-1px',
            }}>
              AML Risk Overview
            </h1>
            <p style={{ margin: '8px 0 0', fontSize: '13px', color: '#475569', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%',
                background: '#f59e0b', boxShadow: '0 0 6px #f59e0b',
              }} />
              {loading ? 'Refreshing data…' : `Sentinel AI · ${visibleDays}-day window · Live connection`}
            </p>
          </div>

          {/* Day selector */}
          <div style={{
            display: 'flex', gap: '4px', alignItems: 'center',
            background: 'rgba(0,0,0,0.03)',
            border: '1px solid rgba(0,0,0,0.08)',
            borderRadius: '14px', padding: '5px',
            backdropFilter: 'blur(16px)',
          }}>
            <span style={{ fontSize: '11px', color: '#475569', fontWeight: 600, paddingLeft: '8px', paddingRight: '4px', letterSpacing: '0.5px' }}>PERIOD</span>
            {DAY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                id={`dashboard-filter-${opt.value}d`}
                onClick={() => setDays(opt.value)}
                style={{
                  padding: '7px 18px', borderRadius: '10px', border: 'none',
                  cursor: 'pointer', fontSize: '13px', fontWeight: 700,
                  fontFamily: "'Inter', sans-serif", transition: 'all 0.25s ease',
                  background: days === opt.value
                    ? 'linear-gradient(135deg, #12B8B0 0%, #0891b2 100%)'
                    : 'transparent',
                  color: days === opt.value ? '#fff' : '#64748b',
                  boxShadow: days === opt.value ? '0 2px 12px rgba(18,184,176,0.4), inset 0 1px 0 rgba(255,255,255,0.2)' : 'none',
                  transform: days === opt.value ? 'scale(1.02)' : 'scale(1)',
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Content ── */}
        {!stats ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>Loading dashboard data...</div>
        ) : (
          <div
            style={{
              transition: 'opacity 0.3s ease',
              opacity: loading ? 0.6 : 1,
            }}
          >
            {/* KPI Row */}
            <KPICards stats={stats} />

            {/* Trend chart full width */}
            <div style={{ marginBottom: '20px' }}>
              <RiskTrendChart data={stats.daily_counts} />
            </div>

            {/* Two charts side by side */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
              gap: '20px', marginBottom: '20px',
            }}>
              <FraudFlagsChart data={stats.top_flags} />
              <TransactionTypeChart data={stats.transaction_type_breakdown} />
            </div>

            {/* High Risk Table */}
            <RecentHighRiskTable transactions={stats.recent_high_risk} />
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
        }
      `}</style>
    </div>
  );
}
