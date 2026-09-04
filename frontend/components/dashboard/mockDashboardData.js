/**
 * mockDashboardData.js -> apiDashboardData.js
 *
 * Data layer for the Risk Overview Dashboard.
 * Fetches real aggregated statistics from the MongoDB backend.
 */

export async function getDashboardStats(days = 30) {
  try {
    const res = await fetch(`/api/fraud/transactions/stats/overview?days=${days}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch stats: ${res.status}`);
    }
    const data = await res.json();
    return { ...data, days };
  } catch (error) {
    console.error("Error fetching dashboard stats:", error);
    // Return safe fallback shape to prevent crashes
    return {
      days,
      total_transactions: 0,
      high_risk_count: 0,
      medium_risk_count: 0,
      low_risk_count: 0,
      flagged_amount_total: 0,
      daily_counts: [],
      top_flags: [],
      transaction_type_breakdown: [],
      recent_high_risk: [],
    };
  }
}
