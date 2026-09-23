"""Assess uncertainty node: LLM synthesis of risk and confidence"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState
from agent.schemas.assessment import AssessmentOutput
from rag.retriever import retrieve_similar_cases, retrieve_policy_context_for_case
from anthropic import Anthropic
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

def assess_uncertainty_node(state: CaseState) -> CaseState:
    """
    LLM: Assess risk, confidence, pattern match, sufficient evidence
    FR4: Risk & confidence assessment
    
    Uses prompt from agent/prompts/assess_prompt.md
    Output schema: agent/schemas/assessment.py::AssessmentOutput
    """
    
    print(f"\n[ASSESS] Analyzing evidence for case {state.case_id}...")
    
    # Build evidence summary
    evidence_summary = "\n".join([
        f"{i+1}. {ev.claim} (source: {ev.source}, ref: {ev.ref})"
        for i, ev in enumerate(state.evidence)
    ])
    
    # Get similar cases (now that we have initial evidence)
    print("  - Retrieving similar cases...")
    similar_cases = retrieve_similar_cases(
        entities=[state.card_id, state.customer_id],
        pattern="unknown",  # Will be refined after assessment
        top_k=3
    )
    
    # Build similar cases summary
    prior_cases_summary = ""
    if similar_cases:
        state.similar_prior_cases = [case["case_id"] for case in similar_cases]
        prior_cases_summary = "\n".join([
            f"- {case['case_id']}: {case['outcome']} ({case['pattern']}), "
            f"${case['exposure_usd']:.2f}, actions: {case['actions_taken']}"
            for case in similar_cases
        ])
    
    # Get policy context (initial, will be refined after pattern identified)
    print("  - Retrieving policy context...")
    risk_signals = state.graph_evidence.get("transaction", {}).get("risk_signals", [])
    policy_context = retrieve_policy_context_for_case(
        pattern="unknown",
        entities=[state.card_id],
        risk_signals=risk_signals,
        fraud_probability=state.risk_score if state.risk_score else 0.5
    )
    
    # Format policy excerpts
    policy_summary = ""
    if policy_context.get("relevant_rules"):
        policy_summary = "\n".join([
            f"- {chunk['title']}: {chunk['text'][:200]}..."
            for chunk in policy_context["relevant_rules"][:2]
        ])
    
    # Build prompt
    prompt = f"""You are a fraud investigation analyst. Assess whether this flagged transaction is fraudulent based on the evidence.

## Case Information
- Case ID: {state.case_id}
- Flagged Transaction: {state.flagged_txn_id}
- Card: {state.card_id}
- Customer: {state.customer_id}
- Risk Score: {state.risk_score if state.risk_score else 'N/A'}
- Trigger: {state.trigger_text}

## Evidence Gathered
{evidence_summary}

## Similar Prior Cases
{prior_cases_summary if prior_cases_summary else "No similar cases found"}

## Relevant Policy Context
{policy_summary if policy_summary else "General fraud patterns apply"}

## Task
Assess this case and provide a structured response with:
1. Pattern match (one of: card_testing, card_not_present_fraud, card_not_present_new_device, out_of_region_use, account_takeover, undocumented, none)
2. Fraud probability (0-1, be honest about uncertainty)
3. Confidence in your assessment (0-1)
4. Whether you have sufficient evidence to act (true/false)
5. Rationale citing specific evidence numbers
6. Affected transaction IDs (if fraud suspected)
7. Connected cards, devices, exposure

Return ONLY a valid JSON object matching this schema:
{{
  "pattern": "card_testing|card_not_present_fraud|card_not_present_new_device|out_of_region_use|account_takeover|undocumented|none",
  "pattern_description": "Required if pattern is 'undocumented', otherwise empty string",
  "fraud_probability": 0.0-1.0,
  "confidence": 0.0-1.0,
  "sufficient_evidence": true|false,
  "rationale": "Explain citing evidence numbers",
  "affected_txn_ids": ["transaction IDs from evidence"],
  "first_suspicious_txn_id": "ID or null",
  "connected_card_ids": ["card IDs from evidence"],
  "connected_device_profiles": ["device strings from evidence"],
  "exposure_usd": 0.0
}}

IMPORTANT: 
- Only cite evidence numbers that exist in the Evidence Gathered section
- Be conservative: if confidence < 0.6, set sufficient_evidence to false
- Pattern "undocumented" requires pattern_description explaining what you found"""

    # Deterministic rule-based assessment from graph evidence
    print("  - Running rule-based assessment...")

    # Extract graph signals
    txn_data = state.graph_evidence.get("transaction", {})
    device_data = state.graph_evidence.get("device", {})
    velocity_data = state.graph_evidence.get("velocity", {})

    risk_signals = txn_data.get("risk_signals", [])
    device_pattern = device_data.get("pattern", "")
    device_shared_count = device_data.get("shared_card_count", 1)
    velocity_pattern = velocity_data.get("pattern_detected", velocity_data.get("pattern", ""))
    velocity_ratio = velocity_data.get("velocity_ratio", velocity_data.get("ratio", 1.0))
    txn_amount = txn_data.get("amount", 0.0)
    risk_score = state.risk_score or 0.5

    # Pattern detection (priority order)
    if velocity_pattern in ("card_testing_sequence",) or "multiple_small_transactions_before_large" in risk_signals:
        state.pattern = "card_testing"
    elif device_shared_count >= 2 or device_pattern == "device_sharing_fraud_ring":
        state.pattern = "card_not_present_fraud"
    elif "new_device_for_account" in risk_signals:
        state.pattern = "card_not_present_new_device"
    elif "out_of_region" in risk_signals or "out_of_region_use" in risk_signals:
        state.pattern = "out_of_region_use"
    elif "account_takeover" in risk_signals:
        state.pattern = "account_takeover"
    else:
        state.pattern = "none"

    state.pattern_description = ""

    # Fraud probability: weighted from risk_score + signal count + velocity
    signal_boost = min(len(risk_signals) * 0.07, 0.25)
    velocity_boost = 0.15 if velocity_ratio >= 5 else (0.08 if velocity_ratio >= 2 else 0.0)
    device_boost = 0.15 if device_shared_count >= 2 else 0.0
    fraud_prob = min(risk_score + signal_boost + velocity_boost + device_boost, 0.98)
    state.fraud_probability = round(fraud_prob, 2)

    # Confidence: higher when multiple corroborating signals
    corroborating = sum([
        len(risk_signals) >= 2,
        device_shared_count >= 2,
        velocity_ratio >= 5,
        state.pattern != "none",
    ])
    state.confidence = round(min(0.55 + corroborating * 0.12, 0.95), 2)
    state.sufficient_evidence = state.confidence >= 0.6

    # Affected transactions from evidence
    state.affected_txn_ids = list({
        eid
        for ev in state.evidence
        for eid in ev.entity_ids
        if eid.isdigit()
    })
    if state.flagged_txn_id and state.flagged_txn_id not in state.affected_txn_ids:
        state.affected_txn_ids.insert(0, state.flagged_txn_id)
    state.first_suspicious_txn_id = state.affected_txn_ids[0] if state.affected_txn_ids else ""

    # Exposure
    state.exposure_usd = round(txn_amount * (1 + device_shared_count - 1), 2) if fraud_prob > 0.5 else 0.0

    # Verdict
    if fraud_prob > 0.75:
        state.verdict = "fraud"
    elif fraud_prob < 0.30:
        state.verdict = "legitimate"
    else:
        state.verdict = "uncertain"

    print(f"  ✓ Assessment complete:")
    print(f"    - Pattern: {state.pattern}")
    print(f"    - Fraud probability: {state.fraud_probability:.2f}")
    print(f"    - Confidence: {state.confidence:.2f}")
    print(f"    - Sufficient evidence: {state.sufficient_evidence}")
    print(f"    - Verdict: {state.verdict}")
    
    state.log_transition("assess_uncertainty", {
        "fraud_probability": state.fraud_probability,
        "confidence": state.confidence,
        "pattern": state.pattern,
        "sufficient_evidence": state.sufficient_evidence
    })
    
    return state
