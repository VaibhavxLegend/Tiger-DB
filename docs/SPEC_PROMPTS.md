# LLM Prompt Specifications

This document defines the exact prompt contracts for every LLM-driven node in the investigation workflow. Prompts are stored as templates in `agent/prompts/` and must be used exactly as specified here.

## Overview

Four LLM-driven nodes require structured prompts:
1. **assess_uncertainty**: Pattern matching, risk/confidence assessment
2. **gather_more_evidence**: Evidence action selection when uncertain
3. **recommend_action**: Next-best-action recommendations
4. **explain**: Case narrative and explanation generation

Each node has:
- System prompt (role, constraints)
- User prompt template (with placeholders)
- Output schema (pydantic model)
- Guardrails (validation rules)

## 1. Assess Uncertainty Node

**File**: `agent/prompts/assess_prompt.md`
**Schema**: `agent/schemas/assessment.py::AssessmentOutput`

### System Prompt
```
You are a fraud investigation analyst. Your role is to assess whether a flagged transaction is fraudulent based on graph evidence, policy documents, and prior case outcomes.

You must:
- Assess fraud probability and your confidence level honestly
- Identify the fraud pattern (or mark as undocumented/none)
- Determine if you have sufficient evidence to make a recommendation
- Cite specific evidence items by their ref IDs
- Never make up entity IDs - only use IDs from the evidence
```

### User Prompt Template
Inputs:
- `case_id`, `flagged_txn_id`, `card_id`, `customer_id`
- `risk_score`, `trigger_text`
- `evidence_summary`: Formatted list of Evidence objects
- `policy_context`: Retrieved policy and typology excerpts
- `prior_cases`: Retrieved similar closed cases

Outputs: AssessmentOutput JSON

### Guardrails
- Fraud probability < 0.15 with 2+ evidence → "legitimate"
- Fraud probability 0.15-0.85 → "uncertain"
- Fraud probability > 0.85 with 2+ evidence → "fraud"
- Confidence < 0.6 → `sufficient_evidence = false`
- Pattern "undocumented" requires `pattern_description`
- Never cite evidence refs not in input

### Safe Default (on validation failure)
```json
{
  "pattern": "none",
  "fraud_probability": 0.5,
  "confidence": 0.3,
  "sufficient_evidence": false,
  "rationale": "Assessment failed validation",
  "affected_txn_ids": [],
  "exposure_usd": 0.0
}
```
Then recommend `ESCALATE_TO_ANALYST`.

## 2. Gather More Evidence Node

**File**: `agent/prompts/gather_evidence_prompt.md`
**Schema**: `agent/schemas/evidence_request.py::EvidenceRequestOutput`

### System Prompt
```
You are a fraud investigation analyst. The current assessment shows insufficient evidence or low confidence. Your role is to select one additional evidence-gathering action that will help resolve the uncertainty.

Available actions:
- customer_validation: Ask the cardholder if they made this transaction
- step_up_auth: Require one-time passcode or app confirmation
- analyst_info: Request additional information from a human analyst
```

### User Prompt Template
Inputs:
- `case_id`, `fraud_probability`, `confidence`, `pattern`
- `iteration_count` (current / 3 max)
- `evidence_summary`
- `policy_context`

Outputs: EvidenceRequestOutput JSON

### Guardrails
- Follow R1: verify before blocking on weak signal (fraud prob < 0.70)
- Follow R8: escalate when uncertain and exposure > $500
- Customer validation preferred for single-signal cases
- Step-up auth for card testing patterns
- Analyst info for complex/conflicting evidence

### Safe Default (on validation failure)
```json
{
  "evidence_type": "analyst_info",
  "justification": "R8: Evidence gathering failed, escalating",
  "simulated_response": "Analyst recommends closing as uncertain",
  "expected_impact": "Will mark as escalated"
}
```

## 3. Recommend Action Node

**File**: `agent/prompts/nba_prompt.md`
**Schema**: `agent/schemas/action_recommendation.py::ActionRecommendationOutput`

### System Prompt
```
You are a fraud investigation analyst. Based on the evidence and assessment, recommend the next-best-actions from the policy taxonomy. Actions will be checked against approval requirements by the policy engine.
```

### User Prompt Template
Inputs:
- `case_id`, `verdict`, `fraud_probability`, `confidence`, `pattern`, `exposure_usd`
- `evidence_summary`
- `evidence_requests` (if any)
- `policy_rules`

Outputs: ActionRecommendationOutput JSON

### Guardrails
All policy rules R1-R10 as specified in PRD Fraud Policy section.

### Safe Default (on validation failure)
```json
{
  "recommended_actions": [
    {
      "action": "ESCALATE_TO_ANALYST",
      "reason": "Action recommendation failed validation",
      "rationale": "Unable to determine safe action, escalating"
    }
  ],
  "what_changed": "",
  "file_sar": false,
  "sar_reason": "No SAR due to validation failure"
}
```

## 4. Explain Node

**File**: `agent/prompts/explain_prompt.md`
**Schema**: `agent/schemas/explanation.py::ExplanationOutput`

### System Prompt
```
You are a fraud investigation analyst writing the final case explanation. Your explanation must cite specific evidence, justify why additional evidence was requested (if any), and explain why the recommended actions follow from policy.

If a SAR is required, write a complete narrative that stands on its own: who, what, when, where, how, and why it is suspicious.
```

### User Prompt Template
Inputs:
- `case_id`, `verdict`, `fraud_probability`, `pattern`, `exposure_usd`
- `evidence_summary`
- `evidence_requests`
- `final_actions`
- `file_sar`

Outputs: ExplanationOutput JSON

### Guardrails
- Summary: 2-6 sentences
- SAR narrative: who, what, when, where, how, why
- All explanations cite evidence refs
- Action justification references policy rules

### Safe Default (on validation failure)
```json
{
  "summary": "Case investigation completed with validation errors. Recommend analyst review.",
  "sar_narrative": "",
  "evidence_explanation": "Evidence processing encountered errors",
  "uncertainty_explanation": "",
  "action_justification": "Actions could not be fully justified, case escalated"
}
```

## Validation & Retry Protocol

For ALL LLM nodes:

1. **Request structured output** with schema enforcement (Anthropic's `response_format` or equivalent)
2. **Parse and validate** against pydantic schema
3. **On validation failure**:
   - Log the error with full LLM output
   - Retry ONCE with error message appended to prompt
   - If second attempt fails, use safe default above
   - Log the failure to case `state_log`
   - NEVER crash the run
4. **Evidence citation validation**:
   - Check all `entity_ids` and `ref` values exist in context
   - Reject outputs citing non-existent entities
   - This is a validation failure → retry/fallback

## Temperature Settings

- assess_uncertainty: 0.3 (low, for reproducibility)
- gather_more_evidence: 0.4
- recommend_action: 0.2 (very low, policy-driven)
- explain: 0.5 (slightly higher for narrative quality)

## Token Budget Estimates

- assess_uncertainty: ~4000 input, ~500 output
- gather_more_evidence: ~2000 input, ~300 output
- recommend_action: ~3000 input, ~400 output
- explain: ~3500 input, ~800 output

Total per case (without evidence loop): ~12k tokens
With 3 evidence iterations: ~18k tokens
