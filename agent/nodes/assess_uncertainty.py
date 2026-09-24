"""Assess uncertainty node: LLM synthesis of risk and confidence"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState
from agent.schemas.assessment import AssessmentOutput
from rag.retriever import retrieve_similar_cases, retrieve_policy_context_for_case
from dotenv import load_dotenv
import json
from agent.llm_util import get_structured_llm
from agent.schemas.assessment import AssessmentOutput

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

    print("  - Running LLM-based assessment (Gemini)...")
    llm = get_structured_llm(AssessmentOutput, model_name="gemini-1.5-flash", temperature=0.0)
    response = llm.invoke(prompt)
    assessment = response.parsed if hasattr(response, "parsed") else response

    state.pattern = assessment.pattern
    state.pattern_description = assessment.pattern_description
    state.fraud_probability = assessment.fraud_probability
    state.confidence = assessment.confidence
    state.sufficient_evidence = assessment.sufficient_evidence
    state.affected_txn_ids = assessment.affected_txn_ids or [state.flagged_txn_id]
    state.first_suspicious_txn_id = assessment.first_suspicious_txn_id or ""
    state.exposure_usd = assessment.exposure_usd

    if state.fraud_probability > 0.75:
        state.verdict = "fraud"
    elif state.fraud_probability < 0.30:
        state.verdict = "legitimate"
    else:
        state.verdict = "uncertain"

    print(f"  ✓ LLM Assessment complete:")
    print(f"    - Pattern: {state.pattern}")
    print(f"    - Fraud probability: {state.fraud_probability:.2f}")
    print(f"    - Confidence: {state.confidence:.2f}")
    print(f"    - Verdict: {state.verdict}")

    state.log_transition("assess_uncertainty", {
        "fraud_probability": state.fraud_probability,
        "confidence": state.confidence,
        "pattern": state.pattern,
        "sufficient_evidence": state.sufficient_evidence,
        "llm_used": True
    })
    return state
