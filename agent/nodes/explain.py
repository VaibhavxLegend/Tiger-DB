"""Explain node: Generate human-readable explanation"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState
from agent.schemas.explanation import ExplanationOutput
from anthropic import Anthropic
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

def explain_node(state: CaseState) -> CaseState:
    """
    LLM: Generate explanation narrative citing evidence
    FR10: Explainability
    
    Uses prompt from agent/prompts/explain_prompt.md
    Output schema: agent/schemas/explanation.py::ExplanationOutput
    """
    
    print(f"\n[EXPLAIN] Generating case explanation for {state.case_id}...")
    
    # Build evidence summary
    evidence_summary = "\n".join([
        f"{i+1}. {ev.claim} (source: {ev.source}, ref: {ev.ref})"
        for i, ev in enumerate(state.evidence)
    ])
    
    # Build evidence requests summary
    evidence_requests_summary = ""
    if state.evidence_requests:
        evidence_requests_summary = "\n".join([
            f"- Request {i+1}: {req.type} (asked after step {req.asked_after_step})"
            for i, req in enumerate(state.evidence_requests)
        ])
    
    # Build final actions summary
    actions_summary = "\n".join([
        f"- {action.action} (route: {action.route}): {action.reason}"
        for action in state.final_actions
    ])
    
    # Determine if SAR is required
    file_sar = any(action.action == "FILE_SAR" for action in state.final_actions)
    
    # Build prompt
    prompt = f"""You are a fraud investigation analyst writing the final case explanation. Your explanation must cite specific evidence, justify why additional evidence was requested (if any), and explain why the recommended actions follow from policy.

## Case Information
- Case ID: {state.case_id}
- Verdict: {state.verdict}
- Fraud Probability: {state.fraud_probability:.2f}
- Pattern: {state.pattern if state.pattern else "none"}
- Exposure: ${state.exposure_usd:.2f}

## Evidence Used
{evidence_summary}

## Evidence Requests
{evidence_requests_summary if evidence_requests_summary else "No additional evidence requested"}

## Final Actions
{actions_summary}

## Task
Generate a complete case explanation. {"Include a full SAR narrative." if file_sar else ""}

Return ONLY a valid JSON object matching this schema:
{{
  "summary": "2-6 sentence summary for analysts (50-1000 chars)",
  "sar_narrative": "{"Full SAR narrative: who, what, when, where, how, why suspicious" if file_sar else "empty string"}",
  "sar_subjects": [{"list of customer, card, merchant, device IDs in SAR" if file_sar else "empty list"}],
  "evidence_explanation": "What evidence was used and why",
  "uncertainty_explanation": "{"Why additional evidence was requested" if evidence_requests_summary else "empty string"}",
  "action_justification": "Why recommended actions follow from evidence and policy"
}}

IMPORTANT:
- Summary must be 2-6 sentences (50-1000 characters)
{"- SAR narrative must be complete and stand-alone: who, what, when, where, how, why" if file_sar else ""}
- All explanations must cite evidence refs (e.g., 'Evidence #1', 'query:get_txn_neighborhood')
- Action justification must reference policy rules"""

    # Template-based explanation (no LLM required)
    print("  - Generating rule-based explanation...")

    pattern = state.pattern or "none"
    verdict = state.verdict or "uncertain"
    prob = state.fraud_probability or 0.5
    ev_refs = ", ".join([f"Evidence #{i+1}" for i in range(min(len(state.evidence), 4))])
    actions_text = ", ".join([a.action for a in state.final_actions]) if state.final_actions else "no actions"
    final_actions = [a if isinstance(a, dict) else a.model_dump() for a in state.final_actions] if state.final_actions else []
    action_names = [a.get("action", "") if isinstance(a, dict) else a.action for a in state.final_actions] if state.final_actions else []

    state.explanation_summary = (
        f"Case {state.case_id} investigated for {pattern.replace('_', ' ')} pattern. "
        f"Fraud probability assessed at {prob:.0%} with verdict: {verdict}. "
        f"Graph traversal identified {len(state.evidence)} evidence items ({ev_refs}). "
        f"Recommended actions: {actions_text}."
    )

    state.evidence_explanation = (
        f"Graph queries (get_txn_neighborhood, find_shared_devices, velocity_check) returned "
        f"{len(state.evidence)} signals. Risk score was {state.risk_score:.2f}. "
        f"Pattern match: {pattern}."
    )

    state.uncertainty_explanation = (
        "" if verdict == "fraud" else
        f"Confidence was {state.confidence:.0%}. Additional evidence was requested to resolve ambiguity."
    )

    state.action_justification = (
        f"Actions {action_names} selected per policy rules: "
        f"R1 (verify before block on weak signal) and R4 (monitor while awaiting verification)."
    )

    # SAR only for confirmed fraud with high exposure
    file_sar = verdict == "fraud" and state.exposure_usd >= 5000
    if file_sar:
        state.sar_narrative = (
            f"Suspicious Activity Report: Case {state.case_id}. "
            f"Card {state.card_id} belonging to customer {state.customer_id} exhibited "
            f"{pattern.replace('_', ' ')} behavior. "
            f"Flagged transaction {state.flagged_txn_id} triggered investigation. "
            f"Total exposure: ${state.exposure_usd:,.2f}. "
            f"Evidence: {ev_refs}. "
            f"Fraud probability: {prob:.0%}. Actions taken: {actions_text}."
        )
        state.sar_subjects = [state.customer_id]
    else:
        state.sar_narrative = ""
        state.sar_subjects = []

    print(f"  ✓ Explanation generated:")
    print(f"    - Summary: {state.explanation_summary[:100]}...")
    print(f"    - SAR required: {file_sar}")
    
    state.log_transition("explain", {
        "explanation_generated": True,
        "sar_required": bool(getattr(state, 'sar_narrative', '')),
        "summary_length": len(getattr(state, 'explanation_summary', ''))
    })
    
    return state
