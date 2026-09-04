"use client";

import { useState } from 'react';
import Button from '@leafygreen-ui/button';
import Icon from '@leafygreen-ui/icon';
import FalsePositiveModal from '../investigations/FalsePositiveModal';

const FLAG_SHORT = {
  unusual_amount: 'Unusual Amt',
  velocity_alert: 'Velocity',
  unknown_device: 'Unknown Dev',
  unexpected_location: 'Unexp. Loc',
  matches_fraud_pattern: 'Fraud Match',
};

function ScoreBadge({ score }) {
  const color = score >= 90 ? '#ef4444' : score >= 80 ? '#f59e0b' : '#10b981';
  const bg = score >= 90 ? 'rgba(239,68,68,0.12)' : score >= 80 ? 'rgba(245,158,11,0.12)' : 'rgba(16,185,129,0.12)';
  const ring = score >= 90 ? 'rgba(239,68,68,0.3)' : score >= 80 ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.3)';
  const glow = score >= 90 ? '0 0 10px rgba(239,68,68,0.3)' : score >= 80 ? '0 0 10px rgba(245,158,11,0.3)' : 'none';
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: '48px', padding: '4px 12px', borderRadius: '20px',
      background: bg, border: `1px solid ${ring}`,
      color, fontSize: '13px', fontWeight: 800,
      fontVariantNumeric: 'tabular-nums', boxShadow: glow,
    }}>
      {score}
    </div>
  );
}

function FlagPill({ flag }) {
  return (
    <span style={{
      display: 'inline-block', padding: '3px 8px', borderRadius: '5px',
      background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
      color: '#fca5a5', fontSize: '10px', fontWeight: 600,
      marginRight: '4px', marginBottom: '2px', whiteSpace: 'nowrap', letterSpacing: '0.2px',
    }}>
      {FLAG_SHORT[flag] || flag}
    </span>
  );
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
}

function formatAmount(n) {
  return n >= 1_000_000
    ? `₹${(n / 1_000_000).toFixed(2)}M`
    : n >= 1000
    ? `₹${(n / 1000).toFixed(1)}K`
    : `₹${n}`;
}

const TH_STYLE = {
  textAlign: 'left', padding: '10px 16px',
  fontSize: '10px', fontWeight: 700, color: '#334155',
  textTransform: 'uppercase', letterSpacing: '1px',
  borderBottom: '1px solid rgba(0,0,0,0.05)',
  whiteSpace: 'nowrap', background: 'rgba(0,0,0,0.01)',
};

export default function RecentHighRiskTable({ transactions, onRefresh }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedTxnId, setSelectedTxnId] = useState(null);
  
  const handleReviewTransaction = async (transactionId, status, notes = "") => {
    try {
      const response = await fetch(`/api/fraud/transactions/${transactionId}/review`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status,
          notes,
          reviewed_by: "analyst" // Or current user if available
        })
      });
      
      if (response.ok) {
        if (onRefresh) onRefresh();
        // Fallback if no refresh prop provided
        else window.location.reload(); 
      } else {
        console.error("Failed to update transaction review status");
      }
    } catch (error) {
      console.error("Error updating transaction:", error);
    }
  };

  return (
    <div style={{
      background: '#ffffff', border: '1px solid rgba(0,0,0,0.08)',
      borderRadius: '22px', overflow: 'hidden',
      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
    }}>
      {/* Header */}
      <div style={{
        padding: '22px 26px 18px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: '1px solid rgba(0,0,0,0.05)',
      }}>
        <div>
          <div style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.3px' }}>
            Recent High-Risk Transactions
          </div>
          <div style={{ fontSize: '12px', color: '#475569', marginTop: '3px' }}>
            Latest flagged activity requiring analyst review
          </div>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '5px 14px', borderRadius: '20px',
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
          fontSize: '12px', fontWeight: 700, color: '#fca5a5',
        }}>
          <div style={{
            width: '6px', height: '6px', borderRadius: '50%',
            background: '#ef4444', boxShadow: '0 0 6px #ef4444',
          }} />
          {transactions.length} alerts
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%', borderCollapse: 'collapse',
          fontFamily: "'Inter',sans-serif",
        }}>
          <thead>
            <tr>
              <th style={TH_STYLE}>Transaction</th>
              <th style={TH_STYLE}>Payer</th>
              <th style={TH_STYLE}>Amount</th>
              <th style={TH_STYLE}>Risk Score</th>
              <th style={TH_STYLE}>Flags</th>
              <th style={TH_STYLE}>Time</th>
              <th style={TH_STYLE}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn, i) => (
              <tr
                key={txn.txnId}
                style={{
                  borderBottom: i < transactions.length - 1 ? '1px solid rgba(0,0,0,0.03)' : 'none',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0.02)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                <td style={{ padding: '13px 16px' }}>
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '6px',
                    fontSize: '12px', color: '#0284c7', fontWeight: 700,
                    background: 'rgba(2,132,199,0.06)',
                    border: '1px solid rgba(2,132,199,0.15)',
                    padding: '3px 10px', borderRadius: '6px',
                  }}>
                    {txn.txnId}
                  </div>
                </td>
                <td style={{ padding: '13px 16px', fontSize: '13px', color: '#475569', fontWeight: 500 }}>
                  {txn.payer}
                </td>
                <td style={{ padding: '13px 16px', fontSize: '14px', color: '#0f172a', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                  {formatAmount(txn.amount)}
                </td>
                <td style={{ padding: '13px 16px' }}>
                  <ScoreBadge score={txn.riskScore} />
                </td>
                <td style={{ padding: '10px 16px', maxWidth: '200px' }}>
                  {txn.flags.map((f) => <FlagPill key={f} flag={f} />)}
                </td>
                <td style={{ padding: '13px 16px', fontSize: '11px', color: '#334155', whiteSpace: 'nowrap', fontVariantNumeric: 'tabular-nums' }}>
                  {formatDate(txn.createdAt)}
                </td>
                <td style={{ padding: '13px 16px' }}>
                  {txn.review_status ? (
                    <span style={{
                      display: 'inline-block', padding: '4px 8px', borderRadius: '4px',
                      fontSize: '11px', fontWeight: 600,
                      background: txn.review_status === 'false_positive' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                      color: txn.review_status === 'false_positive' ? '#059669' : '#dc2626',
                    }}>
                      {txn.review_status === 'false_positive' ? 'Cleared' : 'Confirmed'}
                    </span>
                  ) : (
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <Button
                        id={`btn-clear-fp-${txn.txnId}`}
                        variant="default"
                        size="xsmall"
                        leftGlyph={<Icon glyph="Checkmark" size={14} />}
                        onClick={() => { setSelectedTxnId(txn.txnId); setModalOpen(true); }}
                        style={{ background: '#00684A', color: 'white', borderColor: '#00684A' }}
                      >
                        Clear
                      </Button>
                      <Button
                        id={`btn-confirm-fraud-${txn.txnId}`}
                        variant="danger"
                        size="xsmall"
                        leftGlyph={<Icon glyph="Warning" size={14} />}
                        onClick={() => handleReviewTransaction(txn.txnId, 'confirmed_fraud')}
                      >
                        Confirm
                      </Button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <FalsePositiveModal 
        open={modalOpen} 
        setOpen={setModalOpen}
        transactionId={selectedTxnId}
        onSubmit={(id, reason, notes) => handleReviewTransaction(id, 'false_positive', notes)}
      />
    </div>
  );
}
