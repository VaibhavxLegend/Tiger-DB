# Implementation Plan
## Agentic Fraud Investigation & Next-Best-Action System (TigerGraph HHGOA)

**Deadline:** Sept 24, 2026, 11:59 PM IST — plan assumes ~2 working days from now (Sept 22 evening onward). Every phase has a hard cutoff; if a phase overruns, cut scope from Section 5 (PRD) rather than extend the schedule.

---

## 0. Pre-work (before Day 1 starts — do this now, ~1 hr)

- [ ] Confirm real `transaction.csv` and `identity.csv` headers (don't assume the standard IEEE-CIS layout — verify).
- [ ] Read the dataset README fully: exact benchmark answer-file schema, how the 20 benchmark cases are structured, whether expected outcomes are provided for self-scoring.
- [ ] Spin up TigerGraph Savanna instance; confirm auto-stop/auto-start is on.
- [ ] Get Google Gemini API key + confirm `tigergraph-mcp` repo runs locally against Savanna with a trivial query.
- [ ] Create the repo with the agreed file structure (empty folders + stub files) so nobody blocks on scaffolding later.

---

## Day 1 — Data & Graph Foundation, Agent Skeleton

### Morning block (0–4 hrs): Data → Graph

- [ ] Write `graph/schema/create_vertices.gsql`, `create_edges.gsql`, `create_graph.gsql` per the agreed model (`Transaction`, `Card`, `Customer`, `Device`, `Address`, `EmailDomain`, `Case`, `FraudPattern` + edges).
- [ ] Pre-process `closed_cases_history.csv`: split `txn_ids` and `connected_card_ids` list columns into exploded rows → `data/processed/closed_cases_history_exploded.csv`.
- [ ] Write and run GSQL loading jobs (`load_transactions.gsql`, `load_identity.gsql`, `load_case_pack.gsql`, `load_closed_cases.gsql`).
- [ ] Sanity-check load: vertex/edge counts match expected row counts; spot-check a few known closed-case rings resolve to connected components in the graph.

**Exit criterion:** all four CSVs loaded into TigerGraph with correct edge cardinalities; can run a manual GSQL query and get a sensible neighborhood back.

### Afternoon block (4–8 hrs): GSQL tools + policy/typology ingestion

- [ ] Write the core GSQL installed queries: `get_txn_neighborhood`, `find_shared_devices`, `find_shared_cards`, `velocity_check`, `get_similar_past_cases`.
- [ ] Configure and test the built-in algorithms (WCC for device/card clusters, Louvain for account communities) via `graph/algorithms/algo_configs.json`; run once, confirm output is sane on a known ring from closed_cases_history.
- [ ] Stand up `mcp_server/`: wrap each GSQL query as an MCP tool with typed input/output schemas; test each tool call in isolation (no agent yet).
- [ ] Ingest fraud policy + 5 typologies + regulatory references into the vector store (`rag/policy_ingest.py`); test retrieval on a couple of sample queries ("what does policy say about card testing?").
- [ ] Parse the policy document (or make a documented assumption) into the `policy_engine` approval-required lookup table.

**Exit criterion:** every MCP tool returns correct, pre-aggregated (not raw) output; policy/typology retrieval returns relevant chunks for a test query; approval-required table exists for the full action taxonomy.

### Evening block (8–10 hrs): Agent skeleton (no real LLM calls yet)

- [ ] Define `agent/state.py` — the Case state object (evidence log, risk, confidence, pattern, actions log, approval log).
- [ ] Build the LangGraph state machine in `agent/graph.py` with all nodes stubbed (hardcoded/mocked outputs) so the full trigger→...→update_memory loop runs end-to-end on one dummy case.
- [ ] Wire the bounded evidence-loop conditional edge (max 3 iterations) and confirm it terminates correctly in both branches (sufficient immediately vs. needs looping).
- [ ] Stand up `actions/api.py` mock action endpoints.

**Exit criterion:** one full dummy case runs through every node of the state machine and produces a (stub-content) case log JSON, with the loop condition demonstrably working.

**Day 1 checkpoint (end of day):** graph loaded + queryable, tools working, agent skeleton runs end-to-end with stub logic. If behind schedule, cut: reduce to 3 GSQL queries instead of 5, skip Louvain (keep WCC only), simplify policy table to a flat dict instead of parsed-from-document.

---

## Day 2 — Real Reasoning, Benchmark, UI, Submission Assets

### Morning block (0–4 hrs): Wire real LLM calls + case memory

- [ ] Write and test `assess_uncertainty` prompt — inputs: evidence summary + retrieved policy/typology context; outputs: structured `{pattern, risk_level, confidence, sufficient_evidence, rationale}` (use structured JSON output, validate/parse defensively).
- [ ] Write and test `gather_more_evidence` node — LLM selects an evidence action from the allowed set, logs justification, calls the mock action API, appends simulated response to evidence.
- [ ] Write and test `recommend_action` node — LLM proposes action(s) from the taxonomy; cross-check every proposed action against `policy_engine` before finalizing.
- [ ] Write and test `explain` node — generates narrative citing specific evidence items and policy clauses used.
- [ ] Implement `update_memory`: on case close, embed narrative (`rag/case_memory_embed.py`), write `SIMILAR_TO`/pattern/entity edges back to the graph.
- [ ] Implement hybrid retrieval in `rag/retriever.py` (graph traversal ∪ vector similarity, de-duplicated) and plug it into the `investigate`/`assess_uncertainty` context.

**Exit criterion:** run one real (non-benchmark) case end-to-end with live LLM calls; manually review the output for coherence — evidence cited correctly, action matches evidence, explanation reads sensibly.

### Midday block (4–6 hrs): Benchmark run

- [ ] Confirm exact required answer-file format (from dataset README) and implement the serializer in `evaluation/run_benchmark.py`.
- [ ] Run all 20 benchmark cases unattended; capture per-case: investigation record, evidence, findings, decisions, actions, before/after approval routing, SAR (where required).
- [ ] Manually review a sample (5–6 cases) for quality; check against `closed_cases_history.csv` patterns for plausibility since there's no ground-truth label for the benchmark set.
- [ ] Fix any systematic issues found (e.g., a GSQL query returning empty for a whole entity type, a prompt producing malformed JSON) and re-run only the affected cases.
- [ ] Confirm each case is actually written back to the graph (not just the output file) — this is an explicit submission requirement, easy to silently miss.

**Exit criterion:** 20 valid answer files in `evaluation/output/`, each matching the required schema; cases visible as nodes in TigerGraph; at least a spot-check pass on quality.

### Afternoon block (6–9 hrs): UI

- [ ] Case list view (pull cases from a small API layer over the graph/case store).
- [ ] Case detail view: evidence panel, risk/confidence trajectory chart, action log with approval status, explanation text.
- [ ] Trigger console: manually fire a new investigation for the live demo (so the video doesn't only show pre-computed benchmark output).
- [ ] Wire WebSocket or polling so the UI shows the state machine progressing live during the demo run.

**Exit criterion:** can start a fresh case from the UI and watch it move through investigate→assess→(gather loop)→action→explain live, with the final case viewable in the case-detail view.

### Evening block (9–12 hrs): Submission assets

- [ ] Record 3–5 min demo video: (1) trigger a live case in the UI, (2) show the evidence/graph panel, (3) show an uncertain case triggering the evidence-gathering loop, (4) show final action + approval routing + explanation, (5) briefly show a benchmark output file and the case written to the graph.
- [ ] Write technical blog post: what was built, architecture (walk the repo structure), how TigerGraph is used (schema + algorithms + why graph-native reasoning), agentic capabilities (state machine, tool use, memory, policy gating), what was learned, what's next with more time.
- [ ] Draft and post social media post (X/LinkedIn) tagging @TigerGraphDB, linking blog/demo.
- [ ] Final repo cleanup: README with setup/run instructions, remove dead code/stub leftovers, confirm `.env.example` has no real secrets, confirm all 20 output files are committed.
- [ ] Submit via the form — **one submission per team, by team lead, no resubmissions** — so do a final checklist pass before submitting, not after.

**Exit criterion:** all five submission components ready (repo, 20 case outputs + graph writes, demo video, blog post, social post) with time buffer before 11:59 PM IST.

---

## Risk Register & Mitigations

| Risk | Mitigation |
|---|---|
| `transaction.csv`/`identity.csv` schema differs from assumption | Verify headers in pre-work, before any GSQL DDL is written |
| GSQL loading job list-splitting (`txn_ids`, `connected_card_ids`) breaks on malformed data | Pre-process in pandas first (`data/processed/`), validate row counts before loading, don't debug GSQL LOAD syntax under time pressure |
| LLM returns malformed JSON at assess/action nodes | Always request structured output with a strict schema + a defensive parse-and-retry wrapper; never let a bad parse silently corrupt case state |
| Evidence-gathering loop doesn't terminate | Hard iteration cap (3) enforced in code, independent of LLM behavior |
| Running out of time for real UI | Fallback: a single case-detail page (skip case-list/trigger-console polish) still satisfies "usable interface" requirement |
| Savanna instance auto-stops mid-demo | Confirm auto-start behavior beforehand; have a local screen-recording fallback captured well before the deadline in case of a live outage |
| Benchmark answer format misread | Re-verify against README literally right before building the serializer, not from memory of an earlier read |

## Team Role Split (adjust to team size)

- **Graph/data owner**: schema, loading jobs, GSQL queries/algorithms (Day 1 morning/afternoon).
- **Agent/backend owner**: LangGraph state machine, prompts, policy engine, memory wiring (Day 1 evening → Day 2 morning).
- **Full-stack/UI owner**: mock action APIs, UI, live-demo wiring (Day 2 afternoon), can start component scaffolding in parallel on Day 1.
- **All**: benchmark review, blog post, video, final submission checklist (Day 2 evening) — this should not fall on one person alone given the deadline.
