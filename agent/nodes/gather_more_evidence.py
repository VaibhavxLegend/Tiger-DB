"""Gather more evidence node: Request additional evidence when uncertain"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState, EvidenceRequest, Evidence
from agent.schemas.evidence_request import EvidenceRequestOutput
from rag.retriever import retrieve_policy_context_for_case
from anthropic import Anthropic
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

def gather_more_evidence_node(state: CaseState) -> CaseState:
    """
    LLM: Select evidence action, simulate response, append to evidence
    FR5: Uncertainty-driven evidence loop
    
    Uses prompt from agent/prompts/gather_evidence_prompt.md
    Output schema: agent/schemas/evidence_request.py::EvidenceRequestOutput
    """
    
    print(f"\n[GATHER EVIDENCE] Requesting additional evidence (iteration {state.iteration_count + 1}/3)...")
    
    # Build evidence summary
    evidence_summary = "\n".join([
        f"{i+1}. {ev.claim} (source: {ev.source}, ref: {ev.ref})"
        for i, ev in enumerate(state.evidence)
    ])
    
    # Get policy context
    print("  - Retrieving policy context...")
    policy_context = retrieve_policy_context_for_case(
        pattern=state.pattern if state.pattern else "unknown",
        entities=[state.card_id],
        risk_signals=[],
        fraud_probability=state.fraud_probability
    )
    
    # Format policy excerpts
    policy_summary = ""
    if policy_context.get("relevant_rules"):
        policy_summary = "\n".join([
            f"- {chunk['title']}: {chunk['text'][:200]}..."
            for chunk in policy_context["relevant_rules"][:2]
        ])
    
    # Build prompt
    prompt = f"""You are a fraud investigation analyst. The current assessment shows insufficient evidence or low confidence. Your role is to select one additional evidence-gathering action that will help resolve the uncertainty.

## Case Information
- Case ID: {state.case_id}
- Fraud Probability: {state.fraud_probability:.2f}
- Confidence: {state.confidence:.2f}
- Pattern: {state.pattern if state.pattern else "unknown"}
- Iteration: {state.iteration_count + 1} / 3

## Current Evidence
{evidence_summary}

## Relevant Policy Context
{policy_summary if policy_summary else "General fraud patterns apply"}

## Available Actions
- customer_validation: Ask the cardholder if they made this transaction
- step_up_auth: Require one-time passcode or app confirmation
- analyst_info: Request additional information from a human analyst

## Task
Select ONE evidence-gathering action that will help resolve the uncertainty.

Return ONLY a valid JSON object matching this schema:
{{
  "evidence_type": "customer_validation|step_up_auth|analyst_info",
  "justification": "Why this evidence is needed, citing policy rule",
  "simulated_response": "Assumed response for this request",
  "expected_impact": "How this evidence will affect the assessment"
}}

IMPORTANT:
- Follow R1: verify before blocking on weak signal (fraud prob < 0.70)
- Follow R8: escalate when uncertain and exposure > $500
- Customer validation preferred for single-signal cases
- Step-up auth for card testing patterns
- Analyst info for complex/conflicting evidence"""

    # Deterministic evidence type selection
    print("  - Selecting evidence type (rule-based)...")

    pattern = state.pattern or "none"
    num_signals = len(state.graph_evidence.get("transaction", {}).get("risk_signals", []))
    iteration = state.iteration_count

    # Rotate: first ask customer, then analyst on repeat
    if iteration == 0 and pattern in ("card_not_present_new_device", "none"):
        ev_type = "customer_validation"
        simulated = "Customer confirmed they made the transaction. No dispute raised."
    elif pattern == "card_testing":
        ev_type = "step_up_auth"
        simulated = "Step-up authentication challenge sent; customer did not respond within timeout."
    else:
        ev_type = "analyst_info"
        simulated = "Analyst reviewed signals and recommends closing as uncertain pending additional monitoring."

    request = EvidenceRequest(
        type=ev_type,
        asked_after_step=state.iteration_count,
        assumed_response=simulated
    )
    state.evidence_requests.append(request)

    source = "customer" if ev_type == "customer_validation" else "external"
    state.evidence.append(Evidence(
        claim=f"{ev_type}: {simulated}",
        source=source,
        ref=f"evidence_request:{len(state.evidence_requests)}",
        entity_ids=[state.customer_id]
    ))

    print(f"  ✓ Evidence request created:")
    print(f"    - Type: {ev_type}")
    print(f"    - Simulated response: {simulated[:80]}...")
    
    # Increment iteration count
    state.iteration_count += 1
    
    # Update status
    state.status = "gathering_evidence"
    
    state.log_transition("gather_more_evidence", {
        "iteration": state.iteration_count,
        "requests_count": len(state.evidence_requests),
        "evidence_count": len(state.evidence)
    })
    
    return state
