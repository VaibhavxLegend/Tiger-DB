# Product Requirements Document
## Agentic Fraud Investigation & Next-Best-Action System (TigerGraph HHGOA)

**Version:** 1.0
**Owner:** [Team lead name]
**Target submission:** Sept 24, 2026, 11:59 PM IST

---

## 1. Problem Statement

Fraud analysts manually stitch together transaction history, device/identity signals, account relationships, prior case outcomes, and policy documents before deciding what to do about a flagged transaction. This is slow, inconsistent across analysts, hard to scale, and frequently concludes after funds have already moved. There is no "is_fraud" label in the live data — every decision must be made under uncertainty, using a risk score and circumstantial graph evidence rather than ground truth.

## 2. Goal

Build an agent that takes a fraud trigger (risk signal, customer report, or analyst request), investigates it using TigerGraph as the evidentiary substrate, reasons about uncertainty, decides when it has enough evidence to act, recommends/executes next-best-action(s) within defined policy and approval constraints, and leaves behind a complete, explainable, and reusable case record.

## 3. Users / Personas

| Persona | Need |
|---|---|
| Fraud analyst | Wants a pre-investigated case with clear evidence, risk rationale, and a recommended action they can approve/reject in seconds |
| Fraud ops lead | Wants to see aggregate patterns, case throughput, and where the agent asks for human approval vs. acts autonomously |
| Hackathon judge | Wants to see the full trigger→case→evidence→uncertainty→action→explanation→memory loop demonstrated cleanly on the 20 benchmark cases |

## 4. In Scope

- Ingest and graph-model the four provided datasets (case_pack, closed_cases_history, identity, transaction).
- Investigate a triggered case: pull transaction neighborhood, device/card/account links, prior similar cases.
- Detect the five documented fraud typologies (and flag undocumented pattern candidates as anomalies) using GSQL/graph algorithms.
- Assess risk and confidence; explicitly represent "insufficient evidence" as a state, not a forced guess.
- Request additional evidence via controlled, policy-approved actions (simulated) when uncertain, then re-assess.
- Recommend and/or execute next-best-action(s): allow/block transaction, block/monitor account, warn customer, create case, file SAR, request more evidence, escalate to analyst.
- Enforce policy: which actions are agent-executable vs. require human approval, recorded before and after any evidence request.
- Maintain case memory: embed and graph-link closed cases so future investigations retrieve and use prior outcomes.
- Produce one answer file per benchmark case in the required format, write each case to the graph, generate a SAR when policy requires it.
- Provide an analyst-facing UI showing the investigation, evidence, uncertainty, and recommended actions.
- Deliver GitHub repo, benchmark outputs, demo video, technical blog post, social post.

## 5. Out of Scope

- Real production integrations (core banking, real SAR filing, real card-network APIs) — all actions are stubbed/mocked.
- Training a custom fraud-classification ML model from scratch — the system leans on the risk score, graph structure, and LLM reasoning over GraphRAG context rather than a new supervised model.
- Full multi-tenant, multi-institution deployment concerns (auth, scaling, SRE).
- Real-time streaming ingestion — the benchmark is a static batch of 20 cases; the system should still be *architected* to extend to streaming later, but that extension is not built now.

## 6. Functional Requirements

### FR1 — Trigger intake
The system must accept a case trigger from any of: a risk-score signal (from case_pack.csv), a customer report, or an analyst request, and open a `Case` node in the graph with an initial status.

### FR2 — Evidence gathering
The system must, via TigerGraph MCP tool calls, retrieve: the flagged transaction and its k-hop neighborhood (card, device, address, email domain), any accounts/cards linked through shared device/shared card/shared address, and prior cases connected to any of these entities.

### FR3 — Pattern identification
The system must compare gathered evidence against the five documented fraud typologies and surface a best-match pattern (or "unclassified / novel pattern candidate") with supporting evidence citations.

### FR4 — Risk & confidence assessment
The system must output a risk level and a confidence level (not just risk) and must be able to represent "not enough evidence to act" as a distinct outcome from "cleared" or "confirmed fraud."

### FR5 — Uncertainty-driven evidence loop
When confidence is below a defined threshold, the system must select one or more controlled evidence-gathering actions (e.g., ask account owner to validate, request step-up authentication, request analyst input), log the reason, simulate the response, and re-run assessment. This loop must terminate (max iterations) to avoid infinite gathering.

### FR6 — Next-best-action recommendation
The system must recommend one or more actions from the defined action taxonomy, each tagged with whether it is agent-executable or requires human approval per policy, and must record the approval route *both* before requesting additional evidence and after receiving it (per submission spec).

### FR7 — Case record maintenance
Every state transition (evidence added, risk/confidence updated, action recommended/taken, approval status) must be appended to an immutable case log, both in the graph (`Case` node + edges) and in the per-case answer file.

### FR8 — Case memory
On case closure, the system must store a case embedding (from the narrative/notes) and link the case in the graph to the entities and pattern it touched, so future investigations can retrieve it via both graph traversal and vector similarity.

### FR9 — SAR generation
When policy indicates a Suspicious Activity Report is required (per the fraud policy document, via GraphRAG), the system must generate a SAR document as part of the case output.

### FR10 — Explainability
For every case, the system must produce a human-readable explanation covering: what evidence was used, why (if applicable) additional evidence was requested, and why the specific action(s) were recommended.

### FR11 — Benchmark execution
The system must run unattended against all 20 provided benchmark cases and produce one answer file per case in the exact format specified in the dataset README.

### FR12 — UI
The system must expose a UI showing, for any case: the evidence graph/timeline, the risk/confidence trajectory, the recommended action(s) with approval status, and the explanation.

## 7. Non-Functional Requirements

- **Explainability over black-box accuracy** — every LLM-driven decision must cite the graph/RAG evidence it used; no unsupported claims.
- **Determinism where possible** — graph queries and policy checks must be deterministic; only synthesis/explanation/action-selection under ambiguity uses the LLM.
- **Auditability** — case logs are append-only; nothing is silently overwritten.
- **Reasonable latency** — a single case investigation should complete in well under 2 minutes end-to-end (bounded evidence-loop iterations, capped tool calls).
- **Reproducibility** — running the benchmark twice on the same graph state should produce materially the same recommendation (temperature kept low for assessment/action nodes).

## 8. Success Metrics (mapped to judging weights)

| Judging criterion | Weight | What we optimize for |
|---|---|---|
| Investigation accuracy | 25% | Correct pattern match + well-cited evidence per case, benchmarked against the five documented typologies and closed-case history |
| Next-best-action | 25% | Actions match policy, uncertainty is handled (evidence requested when warranted, not skipped or over-requested), recommendations update as new evidence arrives |
| Case summary & explainability | 10% | Clear, evidence-grounded narrative; clean case progression log |
| Agentic design & engineering | 15% | Clean state machine, real tool use (not decorative), memory actually retrieved and used, policy/permission gating visibly enforced |
| Innovation | 15% | Hybrid graph+vector case memory, graph-algorithm-driven ring detection, GraphRAG context pre-aggregation |
| Demo quality | 10% | End-to-end run visible in under 5 minutes, UI clearly shows the loop |

## 9. Constraints & Assumptions

- Savanna free tier used for TigerGraph; auto-stop/auto-start enabled to avoid burning hours during dev.
- No ground-truth fraud label exists outside closed_cases_history.csv and the benchmark's expected answers (if provided) — pattern-matching against closed cases is the primary accuracy proxy during development.
- `transaction.csv` schema assumed to follow the standard IEEE-CIS Vesta layout unless the actual header differs (must confirm on first load).
- Team has ~2 days of build time; scope in Section 4/5 is set accordingly and should not expand without cutting something else.

## 10. Open Questions

- Exact benchmark answer-file schema (must re-read dataset README before finalizing `evaluation/output/case_*.json` format).
- Whether the benchmark provides expected outcomes for self-scoring, or only inputs.
- Whether policy doc explicitly enumerates which actions require human approval, or whether that mapping must be inferred and documented as an assumption.
