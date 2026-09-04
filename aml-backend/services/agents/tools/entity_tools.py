"""Tools for querying the entities collection."""

import logging
from langchain_core.tools import tool
from dependencies import get_mongo_client, DB_NAME

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Indian Watchlist Registry
# Maps list ID prefixes/names to their regulatory source and severity.
# Used by screen_watchlists and indian_watchlist_screen to classify hits.
# ---------------------------------------------------------------------------
_INDIAN_LIST_REGISTRY: dict[str, dict] = {
    # ── FATF / UN ──────────────────────────────────────────────────────────
    "UN-CONSOLIDATED": {
        "source": "UN Security Council",
        "type": "SANCTIONS",
        "severity": "CRITICAL",
        "authority": "UN SC Res. 1267/1989/2253",
        "filing_required": True,
    },
    "UNSCL": {
        "source": "UN Security Council Consolidated List",
        "type": "SANCTIONS",
        "severity": "CRITICAL",
        "authority": "UN SC Res. 1267",
        "filing_required": True,
    },
    # ── MHA / UAPA (India – Ministry of Home Affairs) ─────────────────────
    "MHA-UAPA": {
        "source": "MHA – Unlawful Activities Prevention Act Designated List",
        "type": "TERRORIST_FINANCING",
        "severity": "CRITICAL",
        "authority": "UAPA 1967, Section 35",
        "filing_required": True,
    },
    "MHA-DESIGNATED": {
        "source": "MHA Designated Terrorist / Organisation",
        "type": "TERRORIST_FINANCING",
        "severity": "CRITICAL",
        "authority": "UAPA 1967",
        "filing_required": True,
    },
    # ── ED / CBI (Enforcement Directorate / Central Bureau) ───────────────
    "ED-PMLA-WANTED": {
        "source": "Enforcement Directorate – PMLA Proclaimed Offenders",
        "type": "PMLA_WANTED",
        "severity": "HIGH",
        "authority": "PMLA 2002 Section 82",
        "filing_required": True,
    },
    "CBI-WANTED": {
        "source": "CBI – Red Corner / Wanted List",
        "type": "FUGITIVE",
        "severity": "HIGH",
        "authority": "CrPC Section 82",
        "filing_required": True,
    },
    # ── SEBI (Securities and Exchange Board of India) ──────────────────────
    "SEBI-DEFAULTER": {
        "source": "SEBI – Debarred / Defaulter Entities",
        "type": "REGULATORY_SANCTION",
        "severity": "HIGH",
        "authority": "SEBI Act 1992, Section 11",
        "filing_required": False,
    },
    "SEBI-DEBARRED": {
        "source": "SEBI – Debarred Persons List",
        "type": "REGULATORY_SANCTION",
        "severity": "HIGH",
        "authority": "SEBI Act 1992",
        "filing_required": False,
    },
    # ── RBI (Reserve Bank of India) ────────────────────────────────────────
    "RBI-WILFUL-DEFAULT": {
        "source": "RBI – Wilful Defaulter List",
        "type": "CREDIT_RISK",
        "severity": "MEDIUM",
        "authority": "RBI Master Circular on Wilful Defaulters",
        "filing_required": False,
    },
    "RBI-FRAUD-REGISTRY": {
        "source": "RBI – Central Fraud Registry",
        "type": "FRAUD",
        "severity": "HIGH",
        "authority": "RBI Circular RBI/2016-17/338",
        "filing_required": True,
    },
    # ── I4C / Cybercrime (MHA – Indian Cyber Crime Coordination Centre) ────
    "I4C-MULE": {
        "source": "I4C – Suspected Mule Account Registry",
        "type": "CYBERCRIME",
        "severity": "HIGH",
        "authority": "I4C / MHA – 1930 Helpline",
        "filing_required": True,
    },
    # ── PEP lists ──────────────────────────────────────────────────────────
    "NATIONAL-PEP": {
        "source": "Domestic PEP List – Indian Political Figures",
        "type": "PEP",
        "severity": "MEDIUM",
        "authority": "RBI KYC Master Direction 2016 (updated 2023)",
        "filing_required": False,
    },
    "NATIONAL-PEP-IN": {
        "source": "Domestic PEP List – India",
        "type": "PEP",
        "severity": "MEDIUM",
        "authority": "RBI KYC Master Direction",
        "filing_required": False,
    },
}

# Fallback for unknown / global list prefixes
_GLOBAL_LIST_REGISTRY: dict[str, dict] = {
    "OFAC": {"source": "OFAC SDN List", "type": "SANCTIONS", "severity": "CRITICAL"},
    "EU-CONSOLIDATED": {"source": "EU Consolidated Sanctions", "type": "SANCTIONS", "severity": "CRITICAL"},
    "HMT": {"source": "UK HM Treasury Sanctions", "type": "SANCTIONS", "severity": "CRITICAL"},
}


def _classify_hit(list_id: str) -> dict:
    """Return the regulatory metadata for a given watchlist list_id."""
    # Try exact match first
    if list_id in _INDIAN_LIST_REGISTRY:
        return _INDIAN_LIST_REGISTRY[list_id]
    # Try prefix match
    for prefix, meta in _INDIAN_LIST_REGISTRY.items():
        if list_id.upper().startswith(prefix):
            return meta
    for prefix, meta in _GLOBAL_LIST_REGISTRY.items():
        if list_id.upper().startswith(prefix):
            return meta
    return {"source": "Unknown List", "type": "UNKNOWN", "severity": "LOW"}


@tool
def get_entity_profile(entity_id: str) -> dict:
    """Look up a single entity by entityId.

    Returns riskAssessment, watchlistMatches, customerInfo, addresses,
    identifiers, name, entityType, and scenarioKey.
    """
    client = get_mongo_client()
    doc = client[DB_NAME]["sentinelaiEntities"].find_one(
        {"entityId": entity_id},
        {
            "_id": 0,
            "entityId": 1,
            "entityType": 1,
            "scenarioKey": 1,
            "status": 1,
            "name": 1,
            "dateOfBirth": 1,
            "addresses": 1,
            "identifiers": 1,
            "contactInfo": 1,
            "customerInfo": 1,
            "uboInfo": 1,
            "riskAssessment": 1,
            "watchlistMatches": 1,
        },
    )
    if not doc:
        return {"error": f"Entity {entity_id} not found"}
    return doc


@tool
def screen_watchlists(entity_id: str) -> dict:
    """Check an entity's watchlistMatches for sanctions / PEP hits.

    Enriches each hit with its Indian regulatory source classification
    (UN/UAPA/ED/SEBI/RBI/I4C) and flags STR-filing-required status.

    Returns structured screening results including list IDs,
    match scores, confirmation status, and Indian regulatory metadata.
    """
    client = get_mongo_client()
    doc = client[DB_NAME]["sentinelaiEntities"].find_one(
        {"entityId": entity_id},
        {"_id": 0, "watchlistMatches": 1, "riskAssessment.overall": 1, "name.full": 1},
    )
    if not doc:
        return {"screened": False, "error": f"Entity {entity_id} not found"}

    matches = doc.get("watchlistMatches", [])
    hits = []
    filing_required = False
    critical_hits = []

    for m in matches:
        list_id = m.get("listId", "")
        reg_meta = _classify_hit(list_id)
        if reg_meta.get("filing_required"):
            filing_required = True
        if reg_meta.get("severity") == "CRITICAL":
            critical_hits.append(list_id)

        hits.append({
            "list_id": list_id,
            "match_score": m.get("matchScore", 0),
            "status": m.get("status", "unknown"),
            "details": m.get("details", {}),
            # Indian regulatory enrichment
            "regulatory_source": reg_meta.get("source", "Unknown"),
            "list_type": reg_meta.get("type", "UNKNOWN"),
            "severity": reg_meta.get("severity", "LOW"),
            "legal_authority": reg_meta.get("authority", ""),
            "str_filing_required": reg_meta.get("filing_required", False),
        })

    return {
        "screened": True,
        "entity_name": doc.get("name", {}).get("full", ""),
        "risk_level": doc.get("riskAssessment", {}).get("overall", {}).get("level", "unknown"),
        "hit_count": len(hits),
        "clean": len(hits) == 0,
        "str_filing_required": filing_required,
        "critical_hit_count": len(critical_hits),
        "critical_lists": critical_hits,
        "hits": hits,
    }


@tool
def indian_watchlist_screen(entity_id: str) -> dict:
    """Perform a focused Indian regulatory watchlist check for an entity.

    Returns a compliance summary organised by Indian regulatory body:
      - MHA_UAPA   : UAPA designated terrorist / organisation
      - ED_PMLA    : ED proclaimed offenders (PMLA wanted)
      - SEBI       : SEBI debarred / defaulter entities
      - RBI        : RBI wilful defaulters / fraud registry
      - I4C        : Suspected mule account registry (cybercrime)
      - PEP        : Domestic PEP (Indian political figures)
      - GLOBAL     : UN / OFAC / EU sanctions

    Also surfaces Indian identifiers (PAN, Aadhaar, GSTIN) for cross-checking.
    """
    client = get_mongo_client()
    doc = client[DB_NAME]["sentinelaiEntities"].find_one(
        {"entityId": entity_id},
        {
            "_id": 0,
            "watchlistMatches": 1,
            "identifiers": 1,
            "riskAssessment.overall": 1,
            "name": 1,
            "entityType": 1,
        },
    )
    if not doc:
        return {"screened": False, "error": f"Entity {entity_id} not found"}

    matches = doc.get("watchlistMatches", [])
    buckets: dict[str, list] = {
        "MHA_UAPA": [], "ED_PMLA": [], "SEBI": [],
        "RBI": [], "I4C": [], "PEP": [], "GLOBAL": [], "OTHER": [],
    }

    for m in matches:
        list_id = m.get("listId", "").upper()
        meta = _classify_hit(list_id)
        hit_type = meta.get("type", "UNKNOWN")

        entry = {
            "list_id": list_id,
            "match_score": m.get("matchScore", 0),
            "status": m.get("status", "unknown"),
            "regulatory_source": meta.get("source", "Unknown"),
            "severity": meta.get("severity", "LOW"),
            "str_filing_required": meta.get("filing_required", False),
        }

        if hit_type == "TERRORIST_FINANCING":
            buckets["MHA_UAPA"].append(entry)
        elif hit_type == "PMLA_WANTED":
            buckets["ED_PMLA"].append(entry)
        elif hit_type == "REGULATORY_SANCTION":
            buckets["SEBI"].append(entry)
        elif hit_type in ("CREDIT_RISK", "FRAUD"):
            buckets["RBI"].append(entry)
        elif hit_type == "CYBERCRIME":
            buckets["I4C"].append(entry)
        elif hit_type == "PEP":
            buckets["PEP"].append(entry)
        elif hit_type == "SANCTIONS":
            buckets["GLOBAL"].append(entry)
        else:
            buckets["OTHER"].append(entry)

    # Extract Indian identifiers for cross-referencing
    identifiers = doc.get("identifiers", [])
    id_summary = {}
    for id_rec in (identifiers if isinstance(identifiers, list) else []):
        id_type = str(id_rec.get("type", "")).upper()
        id_value = id_rec.get("value", "")
        if id_type in ("PAN", "AADHAAR", "GSTIN") and id_value:
            id_summary[id_type] = id_value

    total_hits = sum(len(v) for v in buckets.values())
    str_required = any(
        h.get("str_filing_required")
        for bucket in buckets.values()
        for h in bucket
    )

    return {
        "screened": True,
        "jurisdiction": "IN",
        "entity_id": entity_id,
        "entity_name": (doc.get("name") or {}).get("full", ""),
        "risk_level": doc.get("riskAssessment", {}).get("overall", {}).get("level", "unknown"),
        "total_hits": total_hits,
        "clean": total_hits == 0,
        "str_filing_required": str_required,
        "indian_identifiers": id_summary,
        "hits_by_regulator": buckets,
        "compliance_summary": {
            "mha_uapa_hits": len(buckets["MHA_UAPA"]),
            "ed_pmla_hits": len(buckets["ED_PMLA"]),
            "sebi_hits": len(buckets["SEBI"]),
            "rbi_hits": len(buckets["RBI"]),
            "i4c_cybercrime_hits": len(buckets["I4C"]),
            "pep_hits": len(buckets["PEP"]),
            "global_sanctions_hits": len(buckets["GLOBAL"]),
        },
    }
