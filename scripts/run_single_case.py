import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.graph import build_investigation_graph
from agent.state import CaseState

def run():
    print("Building investigation graph...")
    graph = build_investigation_graph()
    
    print("\nStarting end-to-end case run...")
    # Initialize a mock CaseState
    state = CaseState(
        case_id="CASE-9999",
        flagged_txn_id="TXN-001",
        card_id="C12345-K1",
        customer_id="CUS-001",
        trigger_type="HIGH_RISK_SCORE",
        trigger_text="High risk score (0.95)",
        risk_score=0.95,
        status="open",
        evidence=[]
    )
    
    # We load the dotenv so if the user has an API key in .env it gets picked up
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        final_state = graph.invoke(state)
        
        print("\n================== FINAL STATE ==================")
        print(f"Case ID : {final_state.get('case_id') if isinstance(final_state, dict) else final_state.case_id}")
        
        # When LangGraph returns a dictionary vs Pydantic model
        if isinstance(final_state, dict):
            print(f"Verdict : {final_state.get('verdict')}")
            print(f"Pattern : {final_state.get('pattern')}")
            print(f"Confidence : {final_state.get('confidence')}")
            print(f"Sufficient Evidence: {final_state.get('sufficient_evidence')}")
            print(f"Status : {final_state.get('status')}")
            print(f"Final Actions:")
            for a in final_state.get('final_actions', []):
                print(f"  - {a.action} (Route: {a.route})")
        else:
            print(f"Verdict : {final_state.verdict}")
            print(f"Pattern : {final_state.pattern}")
            print(f"Confidence : {final_state.confidence}")
            print(f"Sufficient Evidence: {final_state.sufficient_evidence}")
            print(f"Status : {final_state.status}")
            print(f"Final Actions:")
            for a in final_state.final_actions:
                print(f"  - {a.action} (Route: {a.route})")
                
    except Exception as e:
        print(f"\nError running case: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: Make sure GOOGLE_API_KEY is available in your environment or .env file.")

if __name__ == "__main__":
    run()
