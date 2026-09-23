# Phase 0 Verification Summary

**Completed:** Phase 0 — Verify Inputs
**Date:** [Auto-generated]

## CSV Headers Verified

### transactions.csv (590,742 rows, ~708 MB)
- ✅ All 393 original Vesta columns present
- ✅ Added columns: `customer_id`, `ts`, `channel`, `risk_score`
- ✅ Schema matches README description

### identity.csv (144,432 rows)
- ✅ All 41 original columns (id_01 to id_38, DeviceType, DeviceInfo)
- ✅ Joins to transactions on TransactionID
- ✅ Online transactions only

### case_pack.csv (20 benchmark cases)
- ✅ Columns: case_id, opened_at, trigger_type, trigger_text, flagged_txn_id, card_id, customer_id, risk_score
- Cases: HHG-001 through HHG-020

### closed_cases_history.csv (5,565 finished investigations)
- ✅ Columns include txn_ids and connected_card_ids as **pipe-separated lists**
- ⚠️ **CRITICAL:** Must pre-process these list columns before GSQL loading
- ✅ 4,665 confirmed fraud, 900 cleared

## Benchmark Answer Format (from README)

**Output Location:** `evaluation/output/` or `cases/`
**Filename Pattern:** `<case_id>.json` (e.g., `HHG-001.json`)

### Required Structure

```json
{
  "case_id": "HHG-XXX",
  "case": {
    "status": "open|closed_fraud|closed_legitimate|escalated",
    "verdict": "fraud|legitimate|uncertain",
    "fraud_probability": 0.0-1.0,
    "pattern": "card_testing|card_not_present_fraud|card_not_present_new_device|out_of_region_use|account_takeover|undocumented|none",
    "pattern_description": "(required when pattern=undocumented)",
    "affected_txn_ids": ["T..."],
    "first_suspicious_txn_id": "T...",
    "connected_card_ids": ["C...-K..."],
    "connected_device_profiles": ["..."],
    "exposure_usd": 0.0,
    "evidence": [
      {
        "claim": "...",
        "source": "graph|document|customer|external",
        "ref": "query:...|document:...|evidence_request:N",
        "entity_ids": ["..."]
      }
    ],
    "similar_prior_cases": ["CC-..."],
    "summary": "2-6 sentences",
    "written_to_graph": true,
    "graph_case_id": "CASE-..."
  },
  "evidence_requests": [
    {
      "type": "customer_validation|step_up_auth|analyst_info",
      "asked_after_step": N,
      "assumed_response": "..."
    }
  ],
  "next_best_actions": {
    "initial": [
      {
        "action": "ALLOW_TRANSACTION|DECLINE_TRANSACTION|...",
        "route": "auto|L1|L2",
        "reason": "R1|R2|..."
      }
    ],
    "final": [...],
    "what_changed": "..."
  },
  "sar": {
    "file": true|false,
    "reason": "...",
    "narrative": "(who, what, when, where, how, why suspicious)",
    "subjects": ["..."],
    "total_amount_usd": 0.0,
    "activity_dates": ["YYYY-MM-DD", "YYYY-MM-DD"]
  },
  "stop_reason": "...",
  "tool_calls": N,
  "tokens": N,
  "latency_s": N.N
}
```

### Key Requirements

1. **Must write case to graph** (`written_to_graph: true`, provide `graph_case_id`)
2. **Two approval route log points**: before requesting evidence AND after receiving it
3. **Evidence must cite actual entity IDs** from the dataset
4. **SAR required when**: fraud confirmed/suspected AND (exposure > $1000 OR shared device/region OR coordinated pattern)
5. **All IDs must exist in dataset** — no made-up values

## TigerGraph Connection

✅ **Savanna Instance Configured**
- Host: `https://tg-242ab1ca-ca69-4bc6-94ee-bb8003365cae.tg-2635877100.i.tgcloud.io`
- Cloud: `true`
- API Token: present in `.env`
- MCP logging: enabled

## Critical Pre-Processing Required

Before GSQL loading, must split list columns in `closed_cases_history.csv`:
- `txn_ids`: pipe-separated → exploded rows
- `connected_card_ids`: pipe-separated → exploded rows

Output to: `data/processed/closed_cases_history_exploded.csv`

## Next Steps

✅ Phase 0 complete — all inputs verified
➡️ Proceed to scaffolding full repository structure
➡️ Then start Phase 1: Graph foundation (TigerGraph Savanna)
