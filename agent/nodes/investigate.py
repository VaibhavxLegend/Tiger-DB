"""Investigate node: Gather evidence via MCP tools"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState, Evidence
from mcp_server.server import get_server

def investigate_node(state: CaseState) -> CaseState:
    """
    Call MCP tools to gather evidence
    FR2: Evidence gathering
    
    Tools called:
    1. get_txn_neighborhood - Transaction details and context
    2. find_shared_devices - Device clustering
    3. velocity_check - Transaction patterns
    4. get_similar_past_cases - Case memory
    """
    
    print(f"\n[INVESTIGATE] Gathering evidence for case {state.case_id}...")
    
    server = get_server()
    
    # 1. Get transaction neighborhood
    print("  - Calling get_txn_neighborhood...")
    txn_result = server.call_tool("get_txn_neighborhood", {
        "transaction_id": state.flagged_txn_id,
        "card_id": state.card_id,
        "customer_id": state.customer_id,
        "hops": 2
    })
    
    if txn_result.get("success"):
        data = txn_result["result"]
        txn = data["transaction"]
        
        # Add transaction evidence
        state.evidence.append(Evidence(
            claim=f"Transaction ${txn['amount']:.2f} via {txn['channel']}, risk score {txn['risk_score']:.2f}",
            source="graph",
            ref="query:get_txn_neighborhood",
            entity_ids=[state.flagged_txn_id]
        ))
        
        # Add risk signals as evidence
        if data.get("risk_signals"):
            state.evidence.append(Evidence(
                claim=f"Risk signals: {', '.join(data['risk_signals'])}",
                source="graph",
                ref="query:get_txn_neighborhood",
                entity_ids=[state.flagged_txn_id]
            ))
        
        # Store raw data for later use
        if not hasattr(state, 'graph_evidence'):
            state.graph_evidence = {}
        state.graph_evidence["transaction"] = data
        
        state.tool_calls += 1
        print(f"    ✓ Found {len(data.get('risk_signals', []))} risk signals")
    
    # 2. Find shared devices
    print("  - Calling find_shared_devices...")
    devices_result = server.call_tool("find_shared_devices", {
        "card_id": state.card_id,
        "time_window_hours": 168  # 7 days
    })
    
    if devices_result.get("success"):
        data = devices_result["result"]
        
        if data.get("risk_level") == "high":
            shared_cards = data.get("shared_cards", [])
            state.evidence.append(Evidence(
                claim=f"Device shared across {len(shared_cards)} cards, pattern: {data.get('pattern')}",
                source="graph",
                ref="query:find_shared_devices",
                entity_ids=[c["card_id"] for c in shared_cards]
            ))
            
            # Track connected cards
            for card_info in shared_cards:
                if card_info["card_id"] != state.card_id:
                    if card_info["card_id"] not in state.connected_card_ids:
                        state.connected_card_ids.append(card_info["card_id"])
        
        state.graph_evidence["shared_devices"] = data
        # Also expose under "device" key with the shape assess_uncertainty expects
        shared_cards = data.get("shared_cards", [])
        state.graph_evidence["device"] = {
            "pattern": data.get("pattern", "normal_usage"),
            "shared_card_count": len(shared_cards),
        }
        state.tool_calls += 1
        print(f"    ✓ Device risk level: {data.get('risk_level')}")
    
    # 3. Velocity check
    print("  - Calling velocity_check...")
    velocity_result = server.call_tool("velocity_check", {
        "card_id": state.card_id,
        "time_window_minutes": 60
    })
    
    if velocity_result.get("success"):
        data = velocity_result["result"]
        
        if data.get("pattern_detected") != "normal":
            state.evidence.append(Evidence(
                claim=f"Velocity pattern: {data['pattern_detected']}, {data['transaction_count']} txns, ratio {data.get('velocity_ratio', 1):.1f}x normal",
                source="graph",
                ref="query:velocity_check",
                entity_ids=[state.card_id]
            ))
        
        state.graph_evidence["velocity"] = data
        state.tool_calls += 1
        print(f"    ✓ Pattern detected: {data.get('pattern_detected')}")
    
    # 4. Get similar past cases (will be called after initial pattern identified)
    # This will be called from assess_uncertainty node after pattern is identified
    
    state.log_transition("investigate", {
        "evidence_gathered": len(state.evidence),
        "tool_calls": state.tool_calls,
        "risk_signals": state.graph_evidence.get("transaction", {}).get("risk_signals", [])
    })
    
    print(f"  ✓ Investigation complete: {len(state.evidence)} pieces of evidence gathered")
    
    return state
