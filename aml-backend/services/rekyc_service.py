"""Re-KYC Periodic Review Utility.

Implements the RBI KYC Master Direction (2016, updated 2023) re-KYC schedule:
  - Low Risk    : once every 10 years
  - Medium Risk : once every 8 years
  - High Risk   : once every 2 years

Also covers PMLA 2002 Section 12 record-keeping (5-year retention).

Usage:
    from services.rekyc_service import RekycService
    service = RekycService()
    due = service.get_due_entities(db)          # Returns entities overdue for re-KYC
    schedule = service.get_entity_schedule(doc) # Returns schedule for a single entity
"""

import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RBI KYC Master Direction re-KYC intervals (in days)
# ---------------------------------------------------------------------------
REKYC_INTERVALS: dict[str, int] = {
    "low":      10 * 365,   # 10 years  — PMLA / RBI low-risk customers
    "medium":    8 * 365,   # 8 years   — Standard risk customers
    "high":      2 * 365,   # 2 years   — High-risk customers (PEP, adverse media)
    "critical":  1 * 365,   # 1 year    — Conservative policy for critical-risk entities
    "unknown":   5 * 365,   # 5 years   — Fallback (matches PMLA record-retention)
}

# PMLA Section 12 mandatory record retention period (days)
PMLA_RECORD_RETENTION_DAYS = 5 * 365  # 5 years


@dataclass
class RekycSchedule:
    entity_id: str
    entity_name: str
    risk_level: str
    last_kyc_date: Optional[datetime]
    next_kyc_due: Optional[datetime]
    days_until_due: Optional[int]         # Negative = overdue
    overdue: bool
    retention_expiry: Optional[datetime]  # PMLA 5-year record expiry
    regulatory_basis: str
    rekyc_interval_days: int


class RekycService:
    """Service for computing RBI-compliant re-KYC schedules."""

    def get_entity_schedule(self, entity_doc: dict) -> RekycSchedule:
        """Compute the re-KYC schedule for a single entity document."""
        entity_id   = entity_doc.get("entityId", "")
        name_raw    = entity_doc.get("name", {})
        entity_name = (
            name_raw.get("full", "")
            if isinstance(name_raw, dict)
            else str(name_raw)
        )

        risk_level = (
            entity_doc.get("riskAssessment", {})
                      .get("overall", {})
                      .get("level", "unknown")
        ).lower()

        # Normalise risk level
        if risk_level not in REKYC_INTERVALS:
            risk_level = "unknown"

        interval_days = REKYC_INTERVALS[risk_level]

        # Determine last KYC date from multiple possible sources
        last_kyc_date = self._extract_last_kyc_date(entity_doc)

        next_kyc_due = None
        days_until_due = None
        overdue = False

        if last_kyc_date:
            next_kyc_due = last_kyc_date + timedelta(days=interval_days)
            now = datetime.now(timezone.utc)
            days_until_due = (next_kyc_due - now).days
            overdue = days_until_due < 0

        # PMLA 5-year retention expiry from entity creation
        created_at = self._parse_dt(entity_doc.get("createdAt"))
        retention_expiry = (
            created_at + timedelta(days=PMLA_RECORD_RETENTION_DAYS)
            if created_at else None
        )

        regulatory_basis = (
            f"RBI KYC Master Direction 2016 (updated 2023) — "
            f"{risk_level.title()} Risk: re-KYC every "
            f"{interval_days // 365} year(s)"
        )

        return RekycSchedule(
            entity_id=entity_id,
            entity_name=entity_name,
            risk_level=risk_level,
            last_kyc_date=last_kyc_date,
            next_kyc_due=next_kyc_due,
            days_until_due=days_until_due,
            overdue=overdue,
            retention_expiry=retention_expiry,
            regulatory_basis=regulatory_basis,
            rekyc_interval_days=interval_days,
        )

    def get_due_entities(
        self,
        db,
        collection: str = "sentinelaiEntities",
        overdue_only: bool = False,
        days_lookahead: int = 90,
        limit: int = 100,
    ) -> list[dict]:
        """Query MongoDB for entities whose re-KYC is due soon.

        Args:
            db: PyMongo database instance
            collection: MongoDB collection name
            overdue_only: If True, only return entities already overdue
            days_lookahead: Include entities due within this many days (default 90)
            limit: Maximum records to return

        Returns:
            List of entity summary dicts with re-KYC schedule info,
            sorted by urgency (most overdue first).
        """
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_lookahead)

        results = []
        cursor = db[collection].find(
            {},
            {
                "_id": 0,
                "entityId": 1,
                "name": 1,
                "riskAssessment.overall": 1,
                "createdAt": 1,
                "updatedAt": 1,
                "customerInfo": 1,
                "status": 1,
            },
            limit=limit * 3,  # Fetch more to allow filtering
        )

        for doc in cursor:
            schedule = self.get_entity_schedule(doc)
            if schedule.next_kyc_due is None:
                continue  # Skip entities with no KYC date recorded

            if overdue_only and not schedule.overdue:
                continue
            elif not overdue_only and schedule.next_kyc_due > cutoff:
                continue

            results.append({
                "entity_id": schedule.entity_id,
                "entity_name": schedule.entity_name,
                "risk_level": schedule.risk_level,
                "last_kyc_date": schedule.last_kyc_date.isoformat() if schedule.last_kyc_date else None,
                "next_kyc_due": schedule.next_kyc_due.isoformat() if schedule.next_kyc_due else None,
                "days_until_due": schedule.days_until_due,
                "overdue": schedule.overdue,
                "regulatory_basis": schedule.regulatory_basis,
                "rekyc_interval_years": schedule.rekyc_interval_days // 365,
                "retention_expiry": schedule.retention_expiry.isoformat() if schedule.retention_expiry else None,
            })

            if len(results) >= limit:
                break

        # Sort: overdue entities first (most overdue at top), then soonest due
        results.sort(key=lambda r: r.get("days_until_due", 9999))
        return results

    def _extract_last_kyc_date(self, entity_doc: dict) -> Optional[datetime]:
        """Extract the last KYC date from entity document.

        Checks multiple candidate fields in priority order.
        """
        candidate_fields = [
            # Explicit KYC date fields
            ("customerInfo", "lastKycDate"),
            ("customerInfo", "kycDate"),
            ("customerInfo", "kycVerifiedAt"),
            # Fall back to entity update date
            (None, "updatedAt"),
            (None, "createdAt"),
        ]

        for parent_key, field_key in candidate_fields:
            if parent_key:
                parent = entity_doc.get(parent_key, {})
                raw = (parent or {}).get(field_key)
            else:
                raw = entity_doc.get(field_key)

            if raw:
                dt = self._parse_dt(raw)
                if dt:
                    return dt

        return None

    @staticmethod
    def _parse_dt(raw) -> Optional[datetime]:
        """Parse various datetime representations to UTC datetime."""
        if raw is None:
            return None
        if isinstance(raw, datetime):
            return raw.replace(tzinfo=timezone.utc) if raw.tzinfo is None else raw
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return None
            # Try fromisoformat first (handles most ISO 8601 variants in Python 3.11+)
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            except ValueError:
                pass
            # Fallback format list
            for fmt in (
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ):
                try:
                    dt = datetime.strptime(raw[:len(fmt)], fmt)
                    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
                except ValueError:
                    continue
        return None



# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_rekyc_service: Optional[RekycService] = None


def get_rekyc_service() -> RekycService:
    global _rekyc_service
    if _rekyc_service is None:
        _rekyc_service = RekycService()
    return _rekyc_service
