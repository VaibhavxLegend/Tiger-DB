"""Trigger node: Initialize case from case_pack entry"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState

def trigger_node(state: CaseState) -> CaseState:
    """
    Initialize case investigation
    FR1: Trigger intake
    
    Sets initial case status and logs the trigger event
    """
    
    print(f"\n[TRIGGER] Opening case {state.case_id}...")
    print(f"  - Flagged transaction: {state.flagged_txn_id}")
    print(f"  - Card: {state.card_id}")
    print(f"  - Customer: {state.customer_id}")
    print(f"  - Risk score: {state.risk_score}")
    print(f"  - Trigger: {state.trigger_text}")
    
    # Set initial status
    state.status = "investigating"
    
    # Initialize graph_evidence dict for storing raw tool outputs
    state.graph_evidence = {}
    
    # Log the trigger
    state.log_transition("trigger", {
        "case_id": state.case_id,
        "flagged_txn_id": state.flagged_txn_id,
        "trigger_type": state.trigger_type,
        "risk_score": state.risk_score
    })
    
    print(f"  ✓ Case opened with status: {state.status}")
    
    return state
