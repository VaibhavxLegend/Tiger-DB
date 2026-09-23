"""
LangGraph state machine for fraud investigation workflow
Phase 3: Agent State Machine
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langgraph.graph import StateGraph, END
from agent.state import CaseState

from agent.nodes.trigger import trigger_node
from agent.nodes.investigate import investigate_node
from agent.nodes.assess_uncertainty import assess_uncertainty_node
from agent.nodes.gather_more_evidence import gather_more_evidence_node
from agent.nodes.recommend_action import recommend_action_node
from agent.nodes.explain import explain_node
from agent.nodes.update_memory import update_memory_node

def should_gather_evidence(state: CaseState) -> str:
    """Conditional edge: sufficient evidence?"""
    if state.sufficient_evidence or state.iteration_count >= 3:
        return "recommend_action"
    return "gather_more_evidence"

def build_investigation_graph():
    """Construct the investigation state machine"""
    workflow = StateGraph(CaseState)
    
    # Add nodes
    workflow.add_node("trigger", trigger_node)
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("assess_uncertainty", assess_uncertainty_node)
    workflow.add_node("gather_more_evidence", gather_more_evidence_node)
    workflow.add_node("recommend_action", recommend_action_node)
    workflow.add_node("explain", explain_node)
    workflow.add_node("update_memory", update_memory_node)
    
    # Add edges
    workflow.set_entry_point("trigger")
    workflow.add_edge("trigger", "investigate")
    workflow.add_edge("investigate", "assess_uncertainty")
    
    # Conditional edge
    workflow.add_conditional_edges(
        "assess_uncertainty",
        should_gather_evidence,
        {
            "recommend_action": "recommend_action",
            "gather_more_evidence": "gather_more_evidence"
        }
    )
    
    workflow.add_edge("gather_more_evidence", "assess_uncertainty")
    workflow.add_edge("recommend_action", "explain")
    workflow.add_edge("explain", "update_memory")
    workflow.add_edge("update_memory", END)
    
    return workflow.compile()

if __name__ == "__main__":
    graph = build_investigation_graph()
    print("Investigation graph compiled successfully, nodes imported.")
