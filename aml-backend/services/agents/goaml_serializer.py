"""goAML XML Serializer for FIU-IND STR Compliance.

Converts a finalized SentinelAI investigation case document into
goAML 4.0 XML format as required by the Financial Intelligence Unit – India
(FIU-IND) for Suspicious Transaction Report (STR) filing.

Reference: FIU-IND goAML Data Model & Reporting Instructions
           https://fiuindia.gov.in/

Usage:
    from services.agents.goaml_serializer import build_goaml_xml
    xml_bytes = build_goaml_xml(case_document)
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# FIU-IND goAML constants
# ---------------------------------------------------------------------------
GOAML_VERSION = "4.0"
REPORT_TYPE = "STR"           # Suspicious Transaction Report
REPORTING_ENTITY = "BANK"     # Change to NBFC / BROKER / INSURER as needed
INSTITUTION_NAME = "SentinelAI"
INSTITUTION_CODE = "TS360"    # Replace with actual FIU-assigned code


def _safe(value, fallback: str = "UNKNOWN") -> str:
    """Return a non-empty string safe for XML text nodes."""
    if value is None:
        return fallback
    s = str(value).strip()
    return s if s else fallback


def _format_date(dt_str: Optional[str]) -> str:
    """Normalise various date string formats to YYYY-MM-DD."""
    if not dt_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_str[:19], fmt[:len(fmt)]).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return dt_str[:10] if len(dt_str) >= 10 else dt_str


def _add_element(parent: ET.Element, tag: str, text: str = "") -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


# ---------------------------------------------------------------------------
# Top-level builder
# ---------------------------------------------------------------------------

def build_goaml_xml(case_document: dict) -> bytes:
    """Build a goAML 4.0 STR XML document from a SentinelAI case document.

    Args:
        case_document: The MongoDB document written by finalize_node.

    Returns:
        Pretty-printed XML as UTF-8 bytes.
    """
    root = ET.Element("goAML")
    root.set("version", GOAML_VERSION)
    root.set("xsi:noNamespaceSchemaLocation", "goaml.xsd")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    report = ET.SubElement(root, "Report")
    _build_header(report, case_document)
    _build_reporting_entity(report)

    entity_data = case_document.get("case_file", {}).get("entity", {})
    alert_data = case_document.get("alert_data", {})
    _build_subject(report, entity_data, alert_data)

    txn_data = case_document.get("case_file", {}).get("transactions", {})
    _build_transactions(report, txn_data, case_document)

    narrative = case_document.get("narrative", {})
    _build_narrative(report, narrative, case_document)

    typology = case_document.get("typology", {})
    _build_typology(report, typology)

    raw_xml = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(raw_xml).toprettyxml(indent="  ")
    lines = pretty.split("\n")[1:]
    final = '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(lines)
    return final.encode("utf-8")


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_header(report: ET.Element, case: dict) -> None:
    case_id = _safe(case.get("case_id"), "CASE-UNKNOWN")
    filed_at = _safe(case.get("created_at"), datetime.now(timezone.utc).isoformat())

    _add_element(report, "ReportCode", REPORT_TYPE)
    _add_element(report, "ReportIndicator", "S")
    _add_element(report, "Submission_Code", "E")
    _add_element(report, "Report_Date", _format_date(filed_at))
    _add_element(report, "Currency_Code_Local", "INR")
    _add_element(report, "FIU_Ref_Number", case_id)
    _add_element(report, "Reporting_Entity_Ref", case_id)

    human = case.get("human_decision") or {}
    analyst = _safe(human.get("analyst_id") or human.get("reviewed_by"), "SYSTEM")
    _add_element(report, "Reporting_Person", analyst)


def _build_reporting_entity(report: ET.Element) -> None:
    entity = ET.SubElement(report, "Reporting_Entity")
    _add_element(entity, "Entity_Name", INSTITUTION_NAME)
    _add_element(entity, "Entity_Code", INSTITUTION_CODE)
    _add_element(entity, "Entity_Type", REPORTING_ENTITY)
    _add_element(entity, "Country", "IN")
    _add_element(entity, "FIU_ID", INSTITUTION_CODE)


def _build_subject(report: ET.Element, entity: dict, alert: dict) -> None:
    subject = ET.SubElement(report, "Subject")

    entity_id = _safe(entity.get("entity_id") or alert.get("entity_id"))
    entity_name = _safe(entity.get("name"))
    entity_type = _safe(entity.get("entity_type"), "individual").lower()

    _add_element(subject, "Subject_Type", "I" if "individual" in entity_type else "E")
    _add_element(subject, "Subject_ID", entity_id)

    name_el = ET.SubElement(subject, "Name")
    _add_element(name_el, "Full_Name", entity_name)

    _add_indian_ids(subject, entity)

    addresses = entity.get("addresses", [])
    if addresses:
        addr_el = ET.SubElement(subject, "Address")
        addr_str = addresses[0] if isinstance(addresses[0], str) else str(addresses[0])
        _add_element(addr_el, "Address_Line", addr_str[:200])
        _add_element(addr_el, "Country", "IN")

    risk_score = str(entity.get("risk_score", ""))
    if risk_score:
        _add_element(subject, "Risk_Score", risk_score)
    _add_element(subject, "Risk_Level", _safe(entity.get("risk_level"), "unknown").upper())


def _add_indian_ids(subject: ET.Element, entity: dict) -> None:
    """Attach PAN, Aadhaar (masked), GSTIN as goAML identifier elements."""
    identifiers = entity.get("identifiers", [])
    if not isinstance(identifiers, list):
        return

    doc_type_map = {
        "PAN": "TAX_ID",
        "AADHAAR": "NATIONAL_ID",
        "GSTIN": "BUSINESS_REG",
        "PASSPORT": "PASSPORT",
        "DRIVING_LICENSE": "DRIVING_LICENSE",
    }

    for id_rec in identifiers:
        if not isinstance(id_rec, dict):
            continue
        id_type = _safe(id_rec.get("type", "")).upper()
        id_value = _safe(id_rec.get("value", ""))
        if not id_value or id_value == "UNKNOWN":
            continue

        id_el = ET.SubElement(subject, "Identification")
        _add_element(id_el, "Identification_Type", doc_type_map.get(id_type, "OTHER"))
        _add_element(id_el, "Identification_Number", id_value)
        _add_element(id_el, "Issuing_Country", "IN")


def _build_transactions(report: ET.Element, txn_summary: dict, case: dict) -> None:
    txn_el = ET.SubElement(report, "Transactions")

    total_count = txn_summary.get("total_count", 0)
    total_volume = txn_summary.get("total_volume", 0.0)
    flagged = txn_summary.get("flagged_transactions", [])

    _add_element(txn_el, "Total_Transaction_Count", str(total_count))
    _add_element(txn_el, "Total_Transaction_Volume", f"{total_volume:.2f}")
    _add_element(txn_el, "Currency_Code", "INR")
    _add_element(txn_el, "High_Risk_Transaction_Count",
                 str(txn_summary.get("high_risk_count", len(flagged))))

    for txn in flagged[:20]:
        txn_detail = ET.SubElement(txn_el, "Transaction")
        _add_element(txn_detail, "Transaction_ID", _safe(txn.get("transactionId")))
        _add_element(txn_detail, "Amount", f"{txn.get('amount', 0):.2f}")
        _add_element(txn_detail, "Currency_Code", "INR")
        _add_element(txn_detail, "Date_Transaction",
                     _format_date(str(txn.get("timestamp", ""))))
        _add_element(txn_detail, "Transaction_Type",
                     _safe(txn.get("type", txn.get("transactionType"))))
        _add_element(txn_detail, "From_Entity",
                     _safe(txn.get("fromEntityId", txn.get("from"))))
        _add_element(txn_detail, "To_Entity",
                     _safe(txn.get("toEntityId", txn.get("to"))))

        tags = txn.get("tags", [])
        if tags:
            _add_element(txn_detail, "Suspicion_Indicators",
                         "; ".join(str(t) for t in tags[:5]))


def _build_narrative(report: ET.Element, narrative: dict, case: dict) -> None:
    narr_el = ET.SubElement(report, "Narrative")

    intro = _safe(narrative.get("introduction"), "No introduction.")
    body = _safe(narrative.get("body"), "No body narrative.")
    conclusion = _safe(narrative.get("conclusion"), "No conclusion.")
    full_text = f"{intro}\n\n{body}\n\n{conclusion}"

    _add_element(narr_el, "Narrative_Text", full_text[:32000])

    human = case.get("human_decision") or {}
    action_taken = _safe(
        human.get("analyst_notes") or human.get("decision"), "Referred for STR filing."
    )
    _add_element(narr_el, "Action_Taken", action_taken[:2000])
    _add_element(narr_el, "Date_Suspicious_Activity_Began",
                 _format_date(case.get("created_at", "")))
    _add_element(narr_el, "Date_Filed",
                 datetime.now(timezone.utc).strftime("%Y-%m-%d"))


def _build_typology(report: ET.Element, typology: dict) -> None:
    typ_el = ET.SubElement(report, "Crime_Type")

    primary = _safe(typology.get("primary_typology"), "UNKNOWN").upper()
    confidence = typology.get("confidence", 0)
    red_flags = typology.get("red_flags", [])

    _add_element(typ_el, "Primary_Crime_Type", primary)
    _add_element(typ_el, "Confidence_Score", f"{confidence:.2f}")
    _add_element(typ_el, "Red_Flags", "; ".join(str(f) for f in red_flags[:10]))

    secondary = typology.get("secondary_typologies", [])
    if secondary:
        _add_element(typ_el, "Secondary_Crime_Types",
                     ", ".join(str(s).upper() for s in secondary[:3]))
