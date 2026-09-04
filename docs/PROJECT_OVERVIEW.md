# Sentinel-AI — Autonomous Financial Crime Investigation Agent

> **Problem Statement Mapping & Technical Walkthrough**

---

## 🔍 Problem Statement (Recap)

> *"Financial institutions detect millions of fraud signals daily, but investigation workflows remain **manual, slow, and expensive**. Compliance teams must analyze contextual data, justify decisions to regulators, and manage large backlogs."*

**Required Capabilities:**
1. Detect anomalies
2. Gather contextual evidence
3. Assess regulatory risk
4. Generate audit-ready explanations
5. Recommend actions (block / monitor / escalate)

**Expected Impact:**
- Faster investigations
- Reduced false positives
- Improved compliance readiness
- Lower fraud losses

---

## How Sentinel-AI Solves the Problem

Sentinel-AI is a **multi-agent, graph-driven autonomous investigation system** built on:

| Layer | Technology |
|---|---|
| Orchestration | LangGraph StateGraph with parallel fan-out |
| LLM Backend | AWS Bedrock (Claude) |
| Database | MongoDB Atlas (vector + full-text + graph) |
| API | FastAPI (Python) |
| Frontend | Next.js |
| Persistence | MongoDB (checkpointing + case storage) |

The system takes a **fraud alert as input** and, fully autonomously, produces a **regulatory-ready SAR (Suspicious Activity Report)** with a human review gate before final filing — no manual investigation needed for the bulk of the workflow.

---

## Section 1: Agentic Investigation Pipeline

**Solves:** Manual, slow investigation workflows → replaces them with an autonomous multi-agent pipeline.

### What It Does

The investigation pipeline is a **LangGraph StateGraph** composed of specialized agent nodes wired together. Every fraud alert enters the graph and flows through structured stages automatically.

### The Pipeline Flow (Node by Node)

```
START
  │
  ▼
[Triage Agent] ──── risk < 25 ────► [Auto-Close] ──► [Finalize] ──► END
  │
  │ risk >= 25
  ▼
[Data Gathering] ── parallel fan-out ──────────────────────────────┐
  ├─► fetch_entity_profile                                          │
  ├─► fetch_transactions                                            │
  ├─► fetch_network                                                 │
  └─► fetch_watchlist                                               │
                                   ◄──────────────────────────────-┘
  ▼
[Assemble Case + Typology Classification] ── single LLM call ──────
  │
  ├──────────────────────────────────────────────────────┐
  ▼                                                      ▼
[Network Analyst]                             [Temporal Analyst]
(graph metrics, centrality,                   (structuring, velocity,
 shell indicators)                             dormancy, round-trips)
  │                                                      │
  └──────────────────────┬───────────────────────────────┘
                         ▼
               [Trail Follower Agent]
               (ownership chains, selects top 3 leads)
                         │
                         ▼
             [Dispatch Sub-Investigations] ── parallel fan-out ─────┐
               ├─► mini_investigate (lead 1)                        │
               ├─► mini_investigate (lead 2)                        │
               └─► mini_investigate (lead 3)                        │
                                            ◄───────────────────────┘
                         ▼
               [Narrative Agent — SAR Writer]
               (FinCEN-compliant, evidence-cited)
                         │
                         ▼
               [Validation Agent — QA]
               (routes back to narrative if issues found)
                         │
                         ▼
               [Human Review] <-- interrupt_before gate
                         │
                         ▼
               [Finalize → MongoDB persistence]
                         │
                        END
```

### Key Agent Nodes Explained

| Node | File | Role |
|---|---|---|
| triage_node | nodes/triage.py | Scores risk 0-100, auto-closes false positives (< 25), reducing backlog |
| dispatch_data_tasks | nodes/data_gatherer.py | Parallel fan-out fetches entity, transactions, network, watchlist simultaneously |
| assemble_case_node | nodes/data_gatherer.py | LLM builds 360 degree case file + classifies crime typology in a single pass |
| network_analyst_node | nodes/network_analyst.py | Computes degree centrality, network risk score, shell structure indicators |
| temporal_analyst_node | nodes/temporal_analyst.py | Pure-compute node: structuring, velocity spikes, dormancy bursts, round-trip patterns |
| trail_follower_node | nodes/trail_follower.py | Traces ownership chains via MongoDB graphLookup, LLM selects top 3 suspicious leads |
| mini_investigate_node | nodes/sub_investigator.py | Rapid triage of each connected entity: no_concern / monitor / escalate / investigate_further |
| narrative_node | nodes/narrative.py | FinCEN SAR narrative (who/what/when/where/why/how) with full evidence citations |
| validation_node | nodes/validator.py | Checks factual accuracy, citation completeness, regulatory compliance; loops back if issues |
| human_review_node | nodes/human_review.py | Analyst approves or rejects before final filing (interrupt_before gate) |
| finalize_node | nodes/finalize.py | Writes full case document to MongoDB with pipeline metrics and full audit trail |

### Why This Directly Solves the Problem
- **Speed**: Parallel fan-out runs data gathering in seconds vs. hours manually
- **False positives**: Triage auto-closes low-risk alerts without human intervention
- **Audit-ready**: Every decision is logged in agent_audit_log with timestamps, token usage, and reasoning
- **Durable**: MongoDB checkpoint-based state means investigations survive server restarts

---

## Section 2: Entity Management

**Solves:** "Analyze contextual data" — understanding WHO is being investigated.

### What It Does

Entity Management is the **foundation of all investigations**. Every entity (individual, corporation, PEP, shell company) is stored in MongoDB's sentinelaiEntities collection with a rich schema.

### Core Schema
```
Entity:
  ├── entityId (unique identifier)
  ├── entityType (individual / corporation / pep / shell_company / ...)
  ├── riskAssessment
  │     ├── overall.score (0-100)
  │     ├── overall.level (low / medium / high / critical)
  │     └── factors (PEP, sanctions, transaction_patterns, ...)
  ├── watchlistStatus (sanctions, PEP lists, adverse media)
  ├── transactionSummary (volume, count, high_risk_count)
  └── relationships → links to other entities
```

### API Endpoints
- GET /entities/{entity_id} — full entity profile
- POST /entities/ — create new entity
- PUT /entities/{entity_id} — update entity
- GET /entities/search/ — search across entities

### Role in the Agent Pipeline
- get_entity_profile tool (called in data gathering) fetches the full 360 degree profile
- Risk score directly feeds the Triage Agent's disposition decision
- Entity type context helps the Narrative Agent explain why behavior is unusual

### Why This Directly Solves the Problem
- Gives agents the **who** — name, type, risk level, account history
- Risk scoring enables **automated prioritization** of alerts
- Watchlist status enables **immediate sanctions detection**

---

## Section 3: Entity Resolution

**Solves:** Duplicate detection, identity verification, and master data management — reduces false positives caused by duplicate records.

### What It Does

Entity Resolution prevents duplicate entities from being created during onboarding (e.g., "John Smith" vs "J. Smith" vs "John A. Smith"). It also enables merging of confirmed duplicates into a single master record.

### How It Works

```
Onboarding Request → Atlas Search (fuzzy match) → Confidence Scoring
                           │
                      Match found?
                     /             \
              Yes (merge)        No (create new)
```

**Matching uses:**
- **Atlas Search** — fuzzy name/address matching with configurable boost factors
- **Vector Search** — semantic similarity via behavioral embeddings
- **Hybrid Search** — combines both scores for final confidence

### API Endpoints
- POST /entities/onboarding/find_matches — find potential duplicates
- POST /entities/resolve — merge duplicate entities
- GET /api/v1/resolution/comprehensive-search — multi-strategy search

### Why This Directly Solves the Problem
- **Reduces false positives** — avoids investigating the same person twice under different records
- **Data quality** — ensures agents work on clean, consolidated entity data
- **Compliance** — master data management is a regulatory audit requirement

---

## Section 4: Network / Relationship Analysis

**Solves:** "Gather contextual evidence" — understanding connections between entities (shell companies, beneficial ownership, counterparties).

### What It Does

Tracks and analyzes **relationships between entities** — who owns whom, who transacts with whom, and which entities form suspicious clusters.

### Relationship Types Tracked
```
Ownership: owns, controls, ubo_of, parent_of_subsidiary, shareholder_of
Corporate: director_of, nominee_director, board_member_of
Transaction: counterparty_of, high_risk_counterparty
Risk: potential_beneficial_owner_of, proxy_of
```

### Graph Analysis (network_analyst_node)
- **Degree centrality** — is this entity a hub? (high centrality = possible money mule or coordinator)
- **Network risk score** — weighted average of connected entity risks
- **Shell structure indicators** — flags patterns consistent with shell company networks
- **High-risk connections count** — direct count of connections to risky entities

### Trail Following (trail_follower_node)
- Uses MongoDB's $graphLookup to trace **ownership chains up to 3 hops deep**
- LLM then selects the top 3 most suspicious leads from the chain
- Each lead gets a **mini-investigation** (sub_investigator) to assess its risk

### API Endpoints
- GET /network/{entity_id} — full network graph for an entity
- POST /network/ — trigger network analysis
- GET /relationships/ — list relationships

### Why This Directly Solves the Problem
- **Layering detection** — identifies money moving through chains of entities
- **Shell company detection** — shell structure indicators flag opaque ownership
- **Escalation evidence** — network data feeds directly into the SAR narrative
- **Ownership transparency** — exposes beneficial ownership for regulatory compliance

---

## Section 5: Temporal Analysis

**Solves:** Detecting structuring, velocity anomalies, and behavioral pattern changes over time.

### What It Does

The temporal_analyst_node is a **pure-compute node** (no LLM, just MongoDB aggregation pipelines) that detects time-based suspicious patterns in transaction data.

### Patterns Detected

| Pattern | How Detected | Fraud Signal |
|---|---|---|
| Structuring | Transactions $8k–$10k grouped by day | Breaking up payments to avoid reporting threshold |
| Velocity anomalies | Z-score > 2.0 vs. 90-day baseline | Sudden spike in transaction volume |
| Dormancy bursts | > 30 day gap then sudden activity | Dormant account suddenly activated |
| Off-hours activity | % of volume during 10pm–6am / weekends | Unusual timing for account type |
| Round-trip patterns | Money sent to A, returned from A within 7 days | Layering / circular transactions |

### Why This Directly Solves the Problem
- **Structuring** is one of the most common money laundering methods — this detects it automatically
- **Velocity anomalies** surface account takeover and sudden fraud
- **Dormancy bursts** catch "sleeper" fraud accounts
- All findings are **evidence-cited** in the final SAR narrative

---

## Section 6: SAR Narrative Generation

**Solves:** "Generate audit-ready explanations" and "justify decisions to regulators."

### What It Does

The narrative_node uses an LLM to write a **FinCEN-compliant Suspicious Activity Report (SAR) narrative** using ONLY facts from the investigation evidence. No fabrication is allowed — every claim must carry a citation tag.

### Narrative Structure
```
Introduction
  └── Who is being reported, risk summary, reason for filing

Body
  └── Chronological evidence:
       ├── Entity profile & risk assessment       [entity_profile]
       ├── Specific transactions                  [transaction:TXN-XXXXXXXX]
       ├── Sanctions/watchlist hits               [watchlist:LIST_NAME]
       ├── Crime typology classification          [typology_classification]
       ├── Network analysis findings              [network_analysis]
       ├── Temporal pattern findings              [temporal_analysis]
       ├── Ownership chain findings               [trail_analysis]
       └── Sub-investigation findings             [sub_investigation:ENTITY_ID]

Conclusion
  └── Actions taken/recommended, data gaps noted, supporting docs
```

### Validation Loop
- After generation, the **Validation Agent** (validation_node) checks for:
  - Factual accuracy (all claims traceable to evidence)
  - Citation completeness (all tags valid)
  - Mathematical consistency (totals match source data)
  - Regulatory compliance (FinCEN SAR format)
- If issues found → routes back to narrative_node for revision
- Only when validated → routes to human_review for analyst approval

### Why This Directly Solves the Problem
- **Eliminates manual report writing** — the most time-consuming part of investigations
- **Regulatory readiness** — follows FinCEN SAR guidelines by design
- **Evidence citations** — every claim is traceable to a specific data source for audit
- **Validation loop** — ensures quality before human review, not after

---

## Section 7: Chat Agent (Interactive Investigation)

**Solves:** Enabling compliance analysts to query the investigation interactively without running a full pipeline.

### What It Does

The Chat Agent (chat_agent.py, chat_routes.py) allows analysts to have a natural-language conversation with the investigation system. The agent has access to all investigation tools and can answer questions in real-time.

### Available Tools for the Chat Agent
- get_entity_profile — look up any entity
- query_entity_transactions — fetch transaction history
- analyze_entity_network — get network graph
- screen_watchlists — run sanctions screening
- search_typologies — look up crime typology definitions
- search_compliance_policies — look up internal compliance policies

### WebSocket Support
- The frontend connects via WebSocket (websocket-proxy.js) for real-time streaming responses
- Analysts can ask natural language questions and get instant tool-backed answers

### Why This Directly Solves the Problem
- Reduces the **backlog** — analysts can self-serve answers instead of waiting for full investigations
- **Accelerates review** — analyst can query the chat during the human review stage
- **Tool transparency** — shows which tools it used and what data it retrieved

---

## Section 8: Vector Search & Semantic Matching

**Solves:** Finding similar past cases and relevant typology patterns to enrich investigations.

### What It Does

Uses MongoDB Atlas Vector Search with **behavioral embeddings** to find semantically similar entities and transactions.

### Use Cases
- search_typologies tool — finds similar fraud typology patterns to inform case assembly
- search_compliance_policies tool — finds relevant internal policies for narrative generation
- Entity resolution — finds similar entities during onboarding by semantic similarity

### Why This Directly Solves the Problem
- **Reduces false positives** — similar past cases provide context on whether behavior was cleared before
- **Typology context** — agents understand which crime pattern they are investigating
- **Policy alignment** — narrative generation references actual compliance policies

---

## Section 9: Transaction Simulator

**Solves:** Demo and testing tool for generating realistic fraud scenarios.

### What It Does

The Transaction Simulator (frontend /transaction-simulator) generates synthetic transaction data across pre-built fraud scenarios:

| Scenario | Fraud Type |
|---|---|
| Structuring Pattern | Breaking up payments to avoid reporting |
| Shell Company Layering | Moving money through shell entities |
| PEP Abuse | Politically exposed person misusing position |
| Sanctions Evasion | Transactions involving sanctioned parties |
| Trade-Based ML | Inflated invoices for money laundering |

### Why This Directly Solves the Problem
- Demos the system to compliance teams without real sensitive data
- Tests the agent pipeline with known fraud patterns to validate detection
- Enables red team / blue team exercises for compliance readiness

---

## What We Are Using vs. What We Are Not

### CORE — Directly Required by Problem Statement

| Feature | Requirement Addressed |
|---|---|
| Triage Agent (auto-close + route) | Detect anomalies, reduce false positives |
| Data Gathering (entity, transactions, network, watchlist) | Gather contextual evidence |
| Network Analyst + Temporal Analyst | Assess regulatory risk |
| Trail Follower + Sub-Investigations | Deep contextual evidence gathering |
| SAR Narrative Generation | Audit-ready explanations |
| Validation Agent | Compliance readiness |
| Human Review Gate | Regulatory approval workflow |
| Finalize + MongoDB persistence | Investigation backlog management |
| Entity Management (CRUD + risk scoring) | Foundation for all agents |
| Relationship/Network Graph | Shell company and layering detection |
| Watchlist Screening | Sanctions compliance |

### SUPPORTING — Enhances but not strictly required

| Feature | Why It Helps |
|---|---|
| Entity Resolution | Reduces false positives from duplicate data |
| Vector Search / Semantic Matching | Improves typology detection accuracy |
| Chat Agent | Reduces analyst effort during review |
| PDF Generation | Regulatory filing output |

### DEMO ONLY — Not needed for production

| Feature | Purpose |
|---|---|
| Transaction Simulator | Demo/testing only |
| LLM Classification routes | Standalone classification without full pipeline |
| Debug routes (/debug/) | Development debugging |

---

## Architecture Summary

```
                    FRONTEND (Next.js)
        /investigations  /entities  /chat  /entity-resolution

                           |
                    HTTP / WebSocket
                           |

                  AML BACKEND (FastAPI)

        AGENT INVESTIGATION PIPELINE:
        triage → data_gathering → assemble_case
        → [network_analyst || temporal_analyst]
        → trail_follower → sub_investigations
        → narrative → validation → human_review → finalize

        Entity Management  |  Entity Resolution  |  Network Graph
        Vector Search      |  Atlas Search       |  Chat Agent

                           |

                    MONGODB ATLAS
        sentinelaiEntities   |  sentinelaiRelationships
        transactionsv2        |  sentinelaiInvestigations
        checkpoints           |  typologies  |  compliance_policies

                           |

                 AWS BEDROCK (Claude)
        Triage | Case Assembly | Trail Follower | Sub-Investigator
        Narrative Writer | Validation QA
```

---

## End-to-End Investigation: Example Flow

```
1. Alert received:
   entity_id=ENT-001, alert_type=HIGH_VOLUME_TXNS

2. Triage Agent:
   risk_score=72, disposition=investigate
   typology_hint="possible structuring"

3. Data Gathering (parallel, ~2-3 seconds):
   entity profile: corp, risk=72, medium-high
   transactions: 28 total, 5 flagged, $2.3M volume
   network: 14 connected entities, 3 shell indicators
   watchlist: 1 PEP hit (NATIONAL-PEP-RU, score=0.87)

4. Case Assembly + Typology:
   primary_typology=structuring, confidence=0.82
   secondary=[sanctions_evasion]
   key_findings=["Multiple sub-threshold transactions", "PEP connection"]

5. Network Analyst:
   centrality=0.71 (hub entity)
   network_risk_score=81.3

6. Temporal Analyst:
   structuring_indicators: 4 days with 2+ sub-threshold transactions
   dormancy_burst: 45-day gap then $890k in 3 days
   velocity z_score=3.2 (anomalous)

7. Trail Follower:
   ownership chain: ENT-001 → owns → SHL-7568 → controls → SHL-9923
   leads selected: [SHL-7568, PEP2-1EE3, CORP-4421]

8. Sub-Investigations (parallel):
   SHL-7568: risk=high, recommendation=escalate
   PEP2-1EE3: risk=critical, recommendation=escalate
   CORP-4421: risk=medium, recommendation=monitor

9. SAR Narrative:
   3200-character FinCEN-compliant report
   14 evidence citations
   All 9 mandatory sections addressed

10. Validation:
    score=0.94, is_valid=True
    routes to human_review

11. Human Review:
    Analyst approves

12. Finalize:
    CASE-A7F2C1D3 persisted to MongoDB
    status=filed
    8 LLM calls, 12 tool calls, 47 seconds total
```

---

*Sentinel-AI — AML/KYC Autonomous Investigation System | Version 1.1.0 | August 2026*
