# False Positive Resolution — Implementation Plan

## 🎯 What Problem Are We Solving?

In your **SentinelAI** fraud detection system, when a transaction is flagged as `HIGH` risk, it could be:

- ✅ **Actual Fraud** → Alert is correct → SAR filed
- ❌ **False Positive** → Alert is WRONG → Legitimate user is incorrectly blocked/flagged

Right now your system has **no way to handle the second case**. Once the model raises a HIGH alert, there is no feedback loop to:
- Let an analyst clear the alert
- Restore the customer's reputation
- Tell the system "this was wrong — don't repeat this mistake"

This plan adds that complete **False Positive Resolution Loop**.

---

## 🤔 WHY Are We Doing This? (Business Justification)

| Problem Without FP Resolution | Impact |
|---|---|
| Legitimate customers are flagged and stay flagged | Customer loses trust, may leave bank |
| Analyst has no way to close the alert | Alert queue grows forever — analyst burnout |
| Model keeps making the same mistake | Model accuracy degrades over time |
| No audit trail of analyst decisions | Compliance/regulatory failure |
| No feedback to recalibrate weights | System cannot self-improve |

> **Key Insight**: In real AML systems (NICE Actimize, FISERV, Oracle FCCM), the **False Positive Rate (FPR)** is the most important KPI. Industry average FPR is 95% — meaning 95 of every 100 alerts are FALSE. Without a resolution flow, your analysts are paralyzed.

---

## 📐 Architecture: How It Works

```
HIGH Alert Raised by Model
          │
          ▼
┌─────────────────────────┐
│  Investigation Dashboard │  ← Analyst sees the alert
│  (InvestigationsPage)    │
└─────────────┬───────────┘
              │
      Analyst Clicks one of:
      ┌───────┴────────┐
      ▼                ▼
[✅ Clear as FP]  [🚨 Confirm Fraud]
      │                │
      ▼                ▼
PATCH /transactions/{id}/review
  { status: "false_positive" }   { status: "confirmed_fraud" }
      │                │
      ▼                ▼
 DB updated          DB updated
 risk_score ↓        SAR flag set
 FP logged           Pattern library updated
      │
      ▼
 Customer profile risk score adjusted down
 (FLAG_IMPACT reversed for each cleared flag)
```

---

## 📦 Proposed Changes

---

### 1. Backend Model — `TransactionModel`

#### [MODIFY] [`transaction.py`](file:///c:/Users/R%20KARTHIK/Documents/aml-demo-01/fsi-aml-fraud-detection-main/backend/models/transaction.py)

Add a new **review fields** to the `TransactionModel`. These fields are optional so existing documents are not broken.

```python
# Add to TransactionModel:
review_status: Optional[str] = None       # "pending" | "false_positive" | "confirmed_fraud" | "under_review"
reviewed_by: Optional[str] = None         # Analyst name/ID
reviewed_at: Optional[datetime] = None    # Timestamp of review
analyst_notes: Optional[str] = None       # Free text explanation
```

**Why**: Without this, we have nowhere in MongoDB to store the analyst's decision. Every reviewed transaction needs a clear `review_status` field so the UI can filter "pending", "cleared", "confirmed" alerts.

---

### 2. Backend Service — `FraudDetectionService`

#### [MODIFY] [`fraud_detection.py`](file:///c:/Users/R%20KARTHIK/Documents/aml-demo-01/fsi-aml-fraud-detection-main/backend/services/fraud_detection.py)

Add a new method `resolve_false_positive()`:

```python
async def resolve_false_positive(
    self,
    transaction_id: str,
    customer_id: str,
    cleared_flags: List[str],
    analyst_notes: str
) -> Dict[str, Any]:
    """
    Called when an analyst marks a HIGH alert as a False Positive.
    
    What it does:
    1. Marks the transaction review_status = "false_positive"
    2. Reverses FLAG_IMPACT on the customer's riskProfile for each cleared flag
    3. Logs the FP event for audit trail
    """
    # Step 1: Reverse flag impact on customer risk profile
    # FLAG_IMPACT = 2.5 was ADDED per flag when the alert fired
    # We SUBTRACT it now since the flags were wrong
    impact_reversal = FLAG_IMPACT * len(cleared_flags)
    
    self.db_client.get_collection(
        db_name=self.customer_db_name,
        collection_name=self.customer_collection
    ).update_one(
        {"id": customer_id},
        {
            "$inc": {"riskProfile.components.activity.score": -impact_reversal},
            "$push": {
                "riskProfile.falsePositiveHistory": {
                    "transaction_id": transaction_id,
                    "cleared_flags": cleared_flags,
                    "impact_reversed": impact_reversal,
                    "timestamp": datetime.utcnow()
                }
            }
        }
    )
    
    return {"status": "resolved", "impact_reversed": impact_reversal}
```

**Why**: The `FLAG_IMPACT = 2.5` constant in your code is what INFLATES the customer's risk score when a flag fires. If the flag was wrong, we must subtract it back. Without this, a customer who gets 3 false flags will permanently carry an inflated risk score of +7.5 that they don't deserve.

---

### 3. Backend Route — `transaction.py`

#### [MODIFY] [`transaction.py`](file:///c:/Users/R%20KARTHIK/Documents/aml-demo-01/fsi-aml-fraud-detection-main/backend/routes/transaction.py)

Add two new endpoints:

**Endpoint 1 — Review a transaction (FP or Confirmed Fraud)**
```python
@router.patch("/{transaction_id}/review")
async def review_transaction(
    transaction_id: str,
    review_data: dict = Body(...),
    db: MongoDBAccess = Depends(get_db),
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service)
):
    """
    Analyst marks a HIGH-alert transaction as:
    - "false_positive"    → clears the alert, reverses risk score
    - "confirmed_fraud"   → confirms the flag, escalates to SAR
    - "under_review"      → marks as being investigated
    """
    review_status = review_data.get("status")       # e.g. "false_positive"
    analyst_notes = review_data.get("notes", "")
    reviewed_by   = review_data.get("reviewed_by", "analyst")
    
    # Update the transaction document
    db.get_collection(...).update_one(
        {"_id": transaction_id},
        {"$set": {
            "review_status": review_status,
            "analyst_notes": analyst_notes,
            "reviewed_by": reviewed_by,
            "reviewed_at": datetime.utcnow()
        }}
    )
    
    # If False Positive → reverse customer risk score
    if review_status == "false_positive":
        txn = db.get_collection(...).find_one({"_id": transaction_id})
        cleared_flags = txn.get("risk_assessment", {}).get("flags", [])
        customer_id = txn.get("customer_id") or txn.get("payer", {}).get("accountId")
        
        await fraud_service.resolve_false_positive(
            transaction_id=transaction_id,
            customer_id=customer_id,
            cleared_flags=cleared_flags,
            analyst_notes=analyst_notes
        )
    
    return {"message": f"Transaction marked as {review_status}", "transaction_id": transaction_id}
```

**Endpoint 2 — Get all alerts pending review**
```python
@router.get("/alerts/pending")
async def get_pending_alerts(db: MongoDBAccess = Depends(get_db)):
    """Returns all HIGH-risk transactions not yet reviewed"""
    alerts = db.get_collection(...).find({
        "risk_assessment.level": "high",
        "review_status": {"$in": [None, "pending"]}
    }).sort("timestamp", -1).limit(100)
    
    return mongo_json(list(alerts))
```

**Why**: Without a `PATCH` endpoint, the frontend has no API to send the analyst's decision to. Without the pending alerts endpoint, the Investigation Dashboard can't know which alerts still need human attention.

---

### 4. Frontend — `InvestigationsPage.jsx`

#### [MODIFY] [`InvestigationsPage.jsx`](file:///c:/Users/R%20KARTHIK/Documents/aml-demo-01/fsi-aml-fraud-detection-main/frontend/components/investigations/InvestigationsPage.jsx)

Add **review action buttons** to each HIGH-risk transaction card:

```jsx
// New function to call the review API
const handleReviewTransaction = async (transactionId, status, notes = "") => {
  const response = await fetch(`/api/fraud/transactions/${transactionId}/review`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      status,             // "false_positive" | "confirmed_fraud" | "under_review"
      notes,
      reviewed_by: currentUser?.name || "analyst"
    })
  });
  
  if (response.ok) {
    // Refresh the transaction list to show updated status
    refreshTransactions();
    showToast(`Transaction marked as ${status}`);
  }
};

// Add to each HIGH-risk transaction row/card:
<div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
  <Button
    id={`btn-clear-fp-${txn._id}`}
    variant="default"
    leftGlyph={<Icon glyph="Checkmark" />}
    onClick={() => handleReviewTransaction(txn._id, 'false_positive')}
    style={{ background: '#00684A', color: 'white' }}
  >
    ✅ Clear — Not Fraud
  </Button>
  
  <Button
    id={`btn-confirm-fraud-${txn._id}`}
    variant="danger"
    leftGlyph={<Icon glyph="Warning" />}
    onClick={() => handleReviewTransaction(txn._id, 'confirmed_fraud')}
  >
    🚨 Confirm Fraud
  </Button>
  
  <Button
    id={`btn-under-review-${txn._id}`}
    variant="default"
    onClick={() => handleReviewTransaction(txn._id, 'under_review')}
  >
    🔍 Under Review
  </Button>
</div>
```

Add a **status badge** to each transaction to show current review state:

```jsx
const REVIEW_STATUS_BADGE = {
  false_positive: { color: 'green', label: 'Cleared — False Positive' },
  confirmed_fraud: { color: 'red', label: 'Confirmed Fraud' },
  under_review: { color: 'yellow', label: 'Under Review' },
  pending: { color: 'gray', label: 'Pending Review' }
};
```

**Why**: Without these buttons, the analyst can SEE the alert but cannot DO anything about it. The investigation workflow is read-only and broken. Adding these buttons makes the system actionable and completes the human-in-the-loop workflow.

---

### 5. Frontend — New `FalsePositiveModal.jsx` Component

#### [NEW] `frontend/components/investigations/FalsePositiveModal.jsx`

A confirmation modal that appears when the analyst clicks "Clear — Not Fraud". It asks:
- Why is this a false positive? (dropdown: `customer_traveled`, `new_device`, `unusual_but_legit`, `other`)
- Free text notes
- Confirm button

**Why**: We want the analyst to give a reason before clearing. This reason is stored in `analyst_notes` and builds a **feedback dataset** that can later be used to retrain the model or adjust the weights (`WEIGHT_AMOUNT`, `WEIGHT_LOCATION`, etc.) in `fraud_detection.py`.

---

## 🔁 Complete Data Flow (End to End)

```
1. Transaction arrives → FraudDetectionService.evaluate_transaction()
2. Flags fire → risk_score = HIGH (e.g. score: 86)
   - FLAG_IMPACT (+2.5) added to customer risk profile per flag
3. Transaction stored in MongoDB with review_status = null (pending)
4. InvestigationsPage shows HIGH alert in red
5. Analyst clicks "✅ Clear — Not Fraud"
6. FalsePositiveModal opens → analyst picks reason + notes → submits
7. PATCH /transactions/{id}/review  { status: "false_positive", notes: "..." }
8. Backend:
   a. Sets review_status = "false_positive" on transaction
   b. Calls resolve_false_positive() on FraudDetectionService
   c. Subtracts FLAG_IMPACT × num_flags from customer's risk profile
   d. Logs FP event to customer's falsePositiveHistory[]
9. Frontend refreshes → transaction now shows "Cleared — False Positive" badge
10. Customer's risk score is restored to pre-alert level
```

---

## ✅ Verification Plan

### Automated (Backend)
- Unit test `resolve_false_positive()` — verify risk score is decremented correctly
- Test `PATCH /transactions/{id}/review` returns 200 with correct body
- Test `GET /transactions/alerts/pending` returns only unreviewed HIGH alerts

### Manual (UI)
1. Run the transaction simulator → generate a HIGH alert
2. Go to Investigations page → see the alert appear with review buttons
3. Click "✅ Clear — Not Fraud" → confirm in modal
4. Verify transaction now shows "Cleared" badge
5. Check customer profile in Entities page → verify risk score decreased
6. Verify audit trail in `falsePositiveHistory[]` in MongoDB

---

## 📋 Files Changed Summary

| File | Action | Purpose |
|---|---|---|
| `backend/models/transaction.py` | MODIFY | Add `review_status`, `reviewed_by`, `reviewed_at`, `analyst_notes` fields |
| `backend/services/fraud_detection.py` | MODIFY | Add `resolve_false_positive()` method |
| `backend/routes/transaction.py` | MODIFY | Add `PATCH /{id}/review` and `GET /alerts/pending` endpoints |
| `frontend/components/investigations/InvestigationsPage.jsx` | MODIFY | Add action buttons + status badges |
| `frontend/components/investigations/FalsePositiveModal.jsx` | NEW | Confirmation modal with reason picker |

---

> [!IMPORTANT]
> **Approve to proceed?** Once you say yes, I will implement all 5 changes above in sequence and verify each step.
