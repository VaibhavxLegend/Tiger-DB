# Architecture Document

## Agentic Fraud Investigation & Next-Best-Action System (TigerGraph HHGOA)

---

## 1. Architecture Overview

The system is a **graph-native, state-machine-orchestrated agent**. TigerGraph is not a passive data store queried by an LLM — it is the primary reasoning substrate for relationship and pattern detection (via GSQL + built-in graph algorithms), while the LLM is reserved for synthesis, uncertainty judgment, and natural-language explanation, per the challenge's explicit guidance that the LLM should not replace graph analysis.

```text
┌────────────────────────────────────────────────────────────┐
│                     UI (Next.js)                           │
│  Case list · Evidence panel · Risk/confidence gauge ·      │
│  Action log & approval status · Chat / trigger console     │
└───────────────────────┬────────────────────────────────────┘
                        │ REST + WebSocket (case status stream)
┌───────────────────────▼───────────────────────────────────────┐
│              Orchestration Layer — LangGraph                  │
│                                                               │
│  trigger → investigate → assess_uncertainty                   │
│                 ▲               │                             │
│                 │         No    ▼                             │
│    gather_more_evidence ───── sufficient?                     │   
│                                 │Yes                          │
│                                 │                             │
│                                 ▼                             │
│                     recommend_action → explain → update_memory│
│                                                               │
│  Cross-cutting: policy_engine (approval gating on every       │
│  action node), case_state (single source of truth object)     │
└───────┬───────────────┬───────────────┬───────────────┬───────┘
        │               │               │               │
        ▼               ▼               ▼               ▼
┌────────────────┐ ┌────────────┐ ┌─────────────┐ ┌────────────────┐
│ TigerGraph MCP │ │ GraphRAG   │ │ Case Memory │ │ Mock Action    │
│ tools (GSQL,   │ │ (policy +  │ │ (vector +   │ │ APIs (block,   │
│ algorithms)    │ │ typology   │ │ graph       │ │ notify, step-  │
│                │ │ retrieval) │ │ retrieval)  │ │ up, escalate)  │
└───────┬────────┘ └─────┬──────┘ └──────┬──────┘ └────────────────┘
        │                │               │
        ▼                ▼               ▼
┌─────────────────────────────────────────────────┐
│         TigerGraph (Savanna) — the graph        │
│  Transactions · Cards · Customers · Devices ·   │
│  Addresses · Cases · FraudPatterns · edges      │
└─────────────────────────────────────────────────┘
```

## 2. Components

### 2.1 TigerGraph (data + reasoning layer)

- **Schema**: entity/relationship model described in the prior data-mapping discussion — `Transaction`, `Card`, `Customer`, `Device`, `Address`, `EmailDomain`, `Case`, `FraudPattern` vertices; `MADE_BY`, `OWNED_BY`, `USES_DEVICE`, `FROM_ADDR`, `USES_EMAIL`, `PART_OF_CASE`, `LINKED_CARD`, `MATCHED_PATTERN`, `SIMILAR_TO` edges.
- **GSQL installed queries** act as the deterministic "tools" the agent calls: k-hop neighborhood retrieval, shared-device/shared-card ring detection, transaction velocity checks against the risk score, prior-similar-case lookup.
- **Built-in graph algorithms**: weakly-connected-components (device/card clusters), Louvain (account communities), PageRank-style centrality (hub accounts), shortest-path (money-movement tracing). These run server-side in TigerGraph — never reimplemented in Python — so results are fast and consistent.
- Rationale for Savanna over Community Edition: no install/infra debugging under a 2-day deadline; auto-stop/auto-start keeps free-tier usage controlled.

### 2.2 TigerGraph MCP tool layer

- Wraps each GSQL query as a typed MCP tool (`get_txn_neighborhood`, `find_shared_devices`, `find_shared_cards`, `velocity_check`, `get_similar_past_cases`, `run_community_detection`).
- Tool outputs are **pre-aggregated summaries**, not raw rows — e.g., "device X seen on 6 distinct cards in 48h" rather than 6 raw transaction dumps — so the LLM receives structured, low-noise context (this is the explicit GraphRAG requirement: pass relevant context, not raw data).
- Tool calls and their arguments/results are logged verbatim into the case record, satisfying explainability ("what evidence was used").

### 2.3 GraphRAG layer

Two retrieval tracks feeding one context builder, merged before being handed to the LLM:

1. **Structured (graph) retrieval** — output of the MCP tool layer above.
2. **Unstructured (document) retrieval** — the fraud policy document, five documented typology descriptions, and regulatory references are chunked and embedded (local vector store — Chroma, no external infra needed). Retrieval is keyed off the candidate pattern name and the entities involved, so only relevant policy clauses are pulled in, not the whole document.

The context builder assembles a single structured object (evidence summary + relevant policy/typology excerpts + prior similar case outcomes) that is passed to the LLM at the `assess_uncertainty` and `recommend_action` nodes.

### 2.4 Case memory

- **Graph side**: closed cases are linked via `PART_OF_CASE`, `LINKED_CARD`, `MATCHED_PATTERN` edges to the entities they touched, and via a computed `SIMILAR_TO` edge to other cases sharing a device/card/pattern. This lets a new case query "what happened last time this device/card showed up."
- **Vector side**: `analyst_notes` and a generated case narrative are embedded on case closure; retrieval at investigation time is by semantic similarity to the current case's evidence summary.
- Hybrid retrieval (graph traversal ∪ vector similarity, de-duplicated) is what's passed into GraphRAG context as "prior similar cases," including their outcome and actions taken — this directly informs next-best-action ("in N similar past cases, action X was taken and confirmed correct in Y of them").

### 2.5 Orchestration layer (LangGraph)

State machine nodes map directly to the required investigation flow:

| Node | Responsibility | LLM used? |
| --- | --- | --- |
| `trigger` | Opens `Case` vertex, records trigger type/source | No |
| `investigate` | Calls MCP tools to pull neighborhood, shared-entity clusters, prior cases | No (tool orchestration only) |
| `assess_uncertainty` | Synthesizes evidence + GraphRAG context into risk level, confidence level, pattern match, and a `sufficient_evidence` boolean | Yes |
| `gather_more_evidence` | Selects a controlled evidence action (validate txn, step-up auth, ask analyst), simulates the response, logs justification | Yes (selection) + stub API (execution) |
| `recommend_action` | Chooses next-best-action(s) from the defined taxonomy, checks `policy_engine` for approval requirement | Yes (selection) + deterministic policy check |
| `explain` | Generates the human-readable narrative citing evidence, uncertainty, and rationale | Yes |
| `update_memory` | Writes case outcome to graph, embeds case narrative into vector store | No |

The conditional edge between `assess_uncertainty` and `gather_more_evidence` is bounded (max iterations, e.g. 3) to guarantee termination per FR5.

### 2.6 Policy engine

A small deterministic module, not an LLM call: given an action name, returns whether it is agent-executable or requires human approval, sourced from the fraud policy document (parsed once at setup into a lookup table, with GraphRAG as fallback for anything not explicitly enumerated). This is checked and logged at two points per the submission spec: before any additional evidence is requested, and after evidence is received / before the final action is taken.

### 2.7 Mock action APIs

FastAPI service exposing stubbed endpoints matching the action taxonomy (`allow_txn`, `block_txn`, `block_account`, `monitor_account`, `warn_customer`, `create_case`, `file_report`, `request_more_evidence`, `escalate_to_analyst`). Each returns a simulated result and a fixed latency, so the agent's logic (checking approval status, waiting/acting) is exercised realistically without touching real systems.

### 2.8 UI

Next.js dashboard, single case-detail view as the centerpiece: evidence panel (graph excerpt + policy citations), a risk/confidence trajectory (updates across the evidence-gathering loop), the action log with approval status per action, and the generated explanation. A case-list view and a simple trigger console (to fire a new investigation manually during the demo) round it out.

## 3. Data Flow (single case, happy path)

1. `case_pack.csv` row → `trigger` node creates `Case` vertex with `risk_score`, `flagged_txn_id`.
2. `investigate` node calls MCP tools → neighborhood, shared-device/card clusters, prior similar cases returned as structured summaries.
3. GraphRAG context builder merges structured summaries + retrieved policy/typology excerpts + prior case outcomes.
4. `assess_uncertainty` LLM call returns `{pattern, risk_level, confidence, sufficient_evidence, rationale}`.
5. If `sufficient_evidence` is false → `gather_more_evidence` (policy check logged) → simulated response appended to evidence → back to step 3.
6. Once sufficient → `recommend_action` LLM call returns ranked action(s) with rationale; `policy_engine` tags each as auto/approval-required (logged).
7. `explain` node produces the case narrative; `file_report` triggered if policy requires a SAR.
8. `update_memory` writes case outcome + embeddings; case status set to closed/escalated.
9. Case log serialized to `evaluation/output/case_<id>.json` in the required benchmark format.

## 4. Key Design Decisions & Rationale

- **LangGraph over a custom orchestrator or a multi-agent framework (CrewAI, etc.)**: the required flow is already a directed graph with one conditional loop — LangGraph maps to it exactly, and gives free state logging per transition, which doubles as the audit trail.
- **Deterministic graph queries + algorithms, LLM only for synthesis/decision-under-ambiguity**: matches the challenge's explicit instruction and keeps benchmark runs reproducible.
- **Pre-aggregated GraphRAG context, not raw row dumps**: required by the challenge, and also keeps prompt size and latency bounded across 20 benchmark cases.
- **Hybrid (graph + vector) case memory** instead of vector-only: lets the agent answer both "who else touched this exact device/card" (graph) and "what case narratives read similarly" (vector) — most fraud rings are found by the former, novel/evolving patterns by the latter.
- **Bounded evidence-gathering loop**: avoids runaway cost/latency and forces the agent to reach a defensible conclusion, which is explicitly what "success" means per the challenge brief.
- **Savanna, not Community Edition**: removes infrastructure risk under a 2-day deadline.

## 5. Non-Functional / Cross-Cutting Concerns

- **Auditability**: every node writes to an append-only case log (both graph-side and file-side); nothing is mutated in place.
- **Idempotency**: re-running a case should not duplicate `Case`/`Evidence` vertices — loading jobs and case-creation logic key off `case_id`.
- **Cost/latency control**: MCP tool calls and LLM calls are counted per case; evidence loop capped at 3 iterations; benchmark run logs total tool/LLM calls per case for the blog post's "what we'd improve" section.
- **Security posture (documented, not deeply implemented given scope)**: mock action APIs simulate an approval gate rather than executing anything real; no real PII leaves the sandboxed dataset.

## 6. Mapping to Repository Structure

Each architectural component above corresponds directly to a top-level folder in the repo (`graph/`, `mcp_server/`, `rag/`, `agent/`, `actions/`, `ui/`, `evaluation/`) as previously laid out, so the blog post's architecture section can walk the folder structure as a proxy for this document.
