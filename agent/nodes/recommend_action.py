"""Recommend action node: Select next-best-actions with policy check"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState, Action
from agent.policy_engine import get_approval_route, should_file_sar

def recommend_action_node(state: CaseState) -> CaseState:
    """
    Recommend actions from taxonomy, cross-check with policy_engine
    FR6: Next-best-action recommendation
    
    For hackathon speed: Using deterministic policy rules instead of LLM
    Can be upgraded to LLM-based post-hackathon
    """
    
    print(f"\n[RECOMMEND] Determining next-best-actions for case {state.case_id}...")
    
    actions = []
    
    # Determine actions based on verdict and pattern
    if state.verdict == "fraud" and state.fraud_probability > 0.85:
        # High confidence fraud
        print("  - High confidence fraud detected")
        
        # Block card
        actions.append(Action(
            action="BLOCK_CARD",
            route=get_approval_route("BLOCK_CARD", state.exposure_usd),
            reason=f"R2: Fraud probability {state.fraud_probability:.2f}, pattern: {state.pattern}"
        ))
        
        # Create case
        actions.append(Action(
            action="CREATE_CASE",
            route="auto",
            reason="R2: Document confirmed fraud"
        ))
        
        # File SAR if required
        has_shared = len(state.connected_card_ids) > 1 or len(state.connected_device_profiles) > 0
        if should_file_sar(state.fraud_probability, state.exposure_usd, has_shared, False, False):
            actions.append(Action(
                action="FILE_REPORT",
                route="L2",
                reason=f"R2: Exposure ${state.exposure_usd:.2f} or shared origin"
            ))
        
        # Monitor connected cards if any
        if len(state.connected_card_ids) > 1:
            actions.append(Action(
                action="MONITOR_CONNECTED_CARDS",
                route="auto",
                reason="R6: Shared device/origin detected"
            ))
    
    elif state.verdict == "uncertain" or (state.verdict == "fraud" and state.fraud_probability < 0.70):
        # Uncertain or low confidence
        print("  - Uncertain verdict, requesting verification")
        
        # Verify with customer first (R1)
        actions.append(Action(
            action="VERIFY_WITH_CUSTOMER",
            route="auto",
            reason="R1: Verify before block on weak signal"
        ))
        
        # Monitor card
        actions.append(Action(
            action="MONITOR_CARD",
            route="auto",
            reason="R4: Monitor while awaiting verification"
        ))
        
        # Escalate if exposed
        if state.exposure_usd > 500:
            actions.append(Action(
                action="ESCALATE_TO_ANALYST",
                route="auto",
                reason="R8: Uncertain and exposure exceeds $500"
            ))
    
    elif state.verdict == "legitimate":
        # Low fraud probability
        print("  - Likely legitimate transaction")
        
        actions.append(Action(
            action="ALLOW_TRANSACTION",
            route="auto",
            reason=f"Fraud probability {state.fraud_probability:.2f}, insufficient evidence of fraud"
        ))
        
        actions.append(Action(
            action="CLOSE_NO_FRAUD",
            route="auto",
            reason="R3: Evidence supports legitimate activity"
        ))
    
    else:
        # Fallback: escalate
        print("  - Unclear situation, escalating")
        actions.append(Action(
            action="ESCALATE_TO_ANALYST",
            route="auto",
            reason="Unable to determine clear recommendation"
        ))
    
    # Store actions
    if len(state.evidence_requests) == 0:
        # Initial actions (before evidence gathering)
        state.initial_actions = actions
        print(f"  ✓ Initial actions: {len(actions)} recommended")
    else:
        # Final actions (after evidence gathering)
        state.final_actions = actions
        print(f"  ✓ Final actions: {len(actions)} recommended")
    
    # If no final actions yet, copy initial to final
    if not state.final_actions:
        state.final_actions = state.initial_actions.copy()
    
    state.log_transition("recommend_action", {
        "actions_count": len(actions),
        "actions": [a.action for a in actions]
    })
    
    for action in actions:
        print(f"    - {action.action} ({action.route}): {action.reason}")
    
    return state
