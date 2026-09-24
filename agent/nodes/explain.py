"""Explain node: Generate human-readable explanation"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState
from agent.schemas.explanation import ExplanationOutput
from agent.llm_util import get_structured_llm
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

    print("  - Running LLM-based explanation (Gemini)...")
    llm = get_structured_llm(ExplanationOutput, model_name="gemini-1.5-flash", temperature=0.0)
    response = llm.invoke(prompt)
    explanation = response.parsed if hasattr(response, "parsed") else response

    state.explanation_summary = explanation.summary
    state.sar_narrative = explanation.sar_narrative
    state.sar_subjects = explanation.sar_subjects
    state.evidence_explanation = explanation.evidence_explanation
    state.uncertainty_explanation = explanation.uncertainty_explanation
    state.action_justification = explanation.action_justification

    print(f"  ✓ LLM Explanation generated:")
    print(f"    - Summary: {state.explanation_summary[:100]}...")
    print(f"    - SAR required: {bool(state.sar_narrative)}")

    state.log_transition("explain", {
        "explanation_generated": True,
        "sar_required": bool(state.sar_narrative),
        "summary_length": len(state.explanation_summary),
        "llm_used": True
    })
    return state
