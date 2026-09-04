"""Re-KYC Periodic Review API Routes.

Endpoints:
  GET  /rekyc/due                          - List entities due for re-KYC
  GET  /rekyc/overdue                      - List entities overdue for re-KYC
  GET  /rekyc/entity/{entity_id}/schedule  - Get re-KYC schedule for one entity
  GET  /rekyc/summary                      - Dashboard summary counts by risk tier

RBI Reference: KYC Master Direction 2016 (updated 2023)
  Low Risk    : every 10 years
  Medium Risk : every  8 years
  High Risk   : every  2 years
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from dependencies import get_mongo_client, DB_NAME
from services.rekyc_service import get_rekyc_service, REKYC_INTERVALS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rekyc", tags=["re-kyc"])

ENTITIES_COLLECTION = "sentinelaiEntities"


@router.get(
    "/due",
    summary="List entities due for re-KYC within a lookahead window",
)
async def get_due_entities(
    days_lookahead: int = Query(
        default=90,
        ge=1,
        le=3650,
        description="Include entities due within this many days (default 90)",
    ),
    limit: int = Query(default=50, ge=1, le=500),
):
    """Returns entities whose RBI re-KYC is due within `days_lookahead` days.

    Sorted by urgency — entities closest to or past their due date appear first.
    """
    client = get_mongo_client()
    db = client[DB_NAME]
    service = get_rekyc_service()

    try:
        due = service.get_due_entities(
            db,
            collection=ENTITIES_COLLECTION,
            overdue_only=False,
            days_lookahead=days_lookahead,
            limit=limit,
        )
    except Exception as exc:
        logger.exception("Re-KYC due query failed")
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "query": {"days_lookahead": days_lookahead, "limit": limit},
        "count": len(due),
        "entities": due,
        "regulatory_basis": "RBI KYC Master Direction 2016 (updated 2023)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/overdue",
    summary="List entities already overdue for re-KYC",
)
async def get_overdue_entities(
    limit: int = Query(default=50, ge=1, le=500),
):
    """Returns entities whose re-KYC deadline has already passed.

    These entities require immediate action under RBI KYC Master Direction.
    Banks must re-KYC before processing further high-value transactions.
    """
    client = get_mongo_client()
    db = client[DB_NAME]
    service = get_rekyc_service()

    try:
        overdue = service.get_due_entities(
            db,
            collection=ENTITIES_COLLECTION,
            overdue_only=True,
            days_lookahead=0,
            limit=limit,
        )
    except Exception as exc:
        logger.exception("Re-KYC overdue query failed")
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "count": len(overdue),
        "entities": overdue,
        "regulatory_note": (
            "Overdue re-KYC may trigger RBI supervisory action under "
            "RBI KYC Master Direction 2016 Clause 38."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/entity/{entity_id}/schedule",
    summary="Get the re-KYC schedule for a single entity",
)
async def get_entity_rekyc_schedule(entity_id: str):
    """Returns the full RBI re-KYC schedule for one entity including:
    - Risk tier and applicable interval
    - Last KYC date (from customerInfo or entity record)
    - Next re-KYC due date
    - Days until due (negative = overdue)
    - PMLA 5-year record retention expiry
    """
    client = get_mongo_client()
    db = client[DB_NAME]

    doc = db[ENTITIES_COLLECTION].find_one(
        {"entityId": entity_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(
            status_code=404, detail=f"Entity '{entity_id}' not found."
        )

    service = get_rekyc_service()
    schedule = service.get_entity_schedule(doc)

    return {
        "entity_id": schedule.entity_id,
        "entity_name": schedule.entity_name,
        "risk_level": schedule.risk_level,
        "rekyc_interval_years": schedule.rekyc_interval_days // 365,
        "last_kyc_date": schedule.last_kyc_date.isoformat() if schedule.last_kyc_date else None,
        "next_kyc_due": schedule.next_kyc_due.isoformat() if schedule.next_kyc_due else None,
        "days_until_due": schedule.days_until_due,
        "overdue": schedule.overdue,
        "retention_expiry": schedule.retention_expiry.isoformat() if schedule.retention_expiry else None,
        "regulatory_basis": schedule.regulatory_basis,
        "pmla_record_retention": "5 years from creation (PMLA 2002 Section 12)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/summary",
    summary="Re-KYC dashboard summary counts by risk tier",
)
async def rekyc_summary():
    """Returns aggregate counts for re-KYC status across all entities.

    Useful for the compliance dashboard to show how many entities in each
    risk tier are overdue, due soon (90 days), or current.
    """
    client = get_mongo_client()
    db = client[DB_NAME]
    service = get_rekyc_service()

    try:
        overdue = service.get_due_entities(
            db, ENTITIES_COLLECTION, overdue_only=True, days_lookahead=0, limit=10000
        )
        due_90 = service.get_due_entities(
            db, ENTITIES_COLLECTION, overdue_only=False, days_lookahead=90, limit=10000
        )
    except Exception as exc:
        logger.exception("Re-KYC summary failed")
        raise HTTPException(status_code=500, detail=str(exc))

    # Build breakdown by risk tier
    def _count_by_risk(entities: list[dict]) -> dict:
        counts: dict[str, int] = {}
        for e in entities:
            rl = e.get("risk_level", "unknown")
            counts[rl] = counts.get(rl, 0) + 1
        return counts

    return {
        "overdue": {
            "total": len(overdue),
            "by_risk_level": _count_by_risk(overdue),
        },
        "due_within_90_days": {
            "total": len(due_90),
            "by_risk_level": _count_by_risk(due_90),
        },
        "rbi_intervals": {
            k: f"{v // 365} year(s)" for k, v in REKYC_INTERVALS.items()
        },
        "regulatory_basis": "RBI KYC Master Direction 2016 (updated 2023)",
        "pmla_retention": "5 years (PMLA 2002 Section 12)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
