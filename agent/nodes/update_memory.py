"""Update memory node: Write case to graph and vector store"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.state import CaseState
from rag.case_memory_embed import embed_case, update_case_graph_links
import json

def update_memory_node(state: CaseState) -> CaseState:
    """
    Write case outcome to graph and embed in vector store
    FR8: Case memory
    FR7: Case record maintenance
    """
    print(f"\n[MEMORY] Archiving case {state.case_id}...")
    
    # Update status based on verdict
    if state.verdict == "fraud":
        state.status = "closed"
    elif state.verdict == "legitimate":
        state.status = "closed"
    else:
        state.status = "closed" # or escalated
    
    # Entities dict to pass
    entities = {
        "cards": list(set([state.card_id] + state.connected_card_ids)),
        "devices": state.connected_device_profiles,
        "customer": state.customer_id
    }
    
    # Embed the case
    embed_case(
        case_id=state.case_id,
        narrative=getattr(state, 'explanation_summary', 'No summary generated'),
        entities=entities
    )
    
    # Update graph
    update_case_graph_links(
        case_id=state.case_id,
        entities=entities,
        pattern=state.pattern
    )
    
    state.log_transition("update_memory", {
        "written_to_graph": True,
        "written_to_vector_store": True,
        "status": state.status
    })
    
    print(f"  ✓ Case {state.case_id} archived successfully.")
    
    return state
