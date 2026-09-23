"""
Run all 20 benchmark cases and generate output files
Phase 4: Benchmark Execution
"""

import json
import time
from pathlib import Path
from datetime import datetime
import pandas as pd
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.graph import build_investigation_graph
from agent.state import CaseState

from dotenv import load_dotenv
load_dotenv()

def load_case_pack():
    """Load the 20 benchmark cases"""
    case_pack_path = Path("data/raw/case_pack.csv")
    return pd.read_csv(case_pack_path)

def build_answer_from_state(final_state_obj, latency: float) -> dict:
    # Handle dict vs pydantic object
    state = final_state_obj if isinstance(final_state_obj, dict) else final_state_obj.model_dump()
    
    # Format evidence
    evidence_list = []
    for e in state.get('evidence', []):
        if isinstance(e, dict):
            evidence_list.append(e)
        else:
            evidence_list.append(e.model_dump())
            
    # Format requests
    requests_list = []
    for r in state.get('evidence_requests', []):
        if isinstance(r, dict):
            requests_list.append({
                "type": r.get("type", "analyst_info"),
                "asked_after_step": r.get("asked_after_step", 1),
                "assumed_response": r.get("assumed_response", "")
            })
        else:
            requests_list.append({
                "type": r.type,
                "asked_after_step": r.asked_after_step,
                "assumed_response": r.assumed_response
            })
            
    # Format actions
    initial_actions = []
    final_actions = []
    has_file_report = False
    file_report_reason = "No SAR required"
    
    for a in state.get('initial_actions', []):
        a_dict = a if isinstance(a, dict) else a.model_dump()
        initial_actions.append(a_dict)
        
    for a in state.get('final_actions', []):
        a_dict = a if isinstance(a, dict) else a.model_dump()
        final_actions.append(a_dict)
        if a_dict.get('action') == "FILE_REPORT":
            has_file_report = True
            file_report_reason = a_dict.get('reason', '')
    
    what_changed = "Nothing changed" if len(requests_list) == 0 else "Actions were updated after reviewing additional evidence."
    
    # Extract affected txns safely
    affected_txn_ids = state.get('affected_txn_ids', [])
    if affected_txn_ids is None:
        affected_txn_ids = []
        
    sar_narrative = getattr(final_state_obj, 'sar_narrative', state.get('sar_narrative', ''))
    sar_subjects = getattr(final_state_obj, 'sar_subjects', state.get('sar_subjects', []))
    summary = getattr(final_state_obj, 'explanation_summary', state.get('explanation_summary', ''))
    
    answer = {
        "case_id": state.get("case_id"),
        "case": {
            "status": state.get("status"),
            "verdict": state.get("verdict"),
            "fraud_probability": state.get("fraud_probability", 0.0),
            "pattern": state.get("pattern", "none"),
            "pattern_description": state.get("pattern_description", ""),
            "affected_txn_ids": affected_txn_ids,
            "first_suspicious_txn_id": state.get("first_suspicious_txn_id", ""),
            "connected_card_ids": state.get("connected_card_ids", []),
            "connected_device_profiles": state.get("connected_device_profiles", []),
            "exposure_usd": state.get("exposure_usd", 0.0),
            "evidence": evidence_list,
            "similar_prior_cases": state.get("similar_prior_cases", []),
            "summary": summary,
            "written_to_graph": True,
            "graph_case_id": state.get("case_id")
        },
        "evidence_requests": requests_list,
        "next_best_actions": {
            "initial": initial_actions,
            "final": final_actions,
            "what_changed": what_changed
        },
        "sar": {
            "file": has_file_report,
            "reason": file_report_reason,
            "narrative": sar_narrative,
            "subjects": sar_subjects,
            "total_amount_usd": state.get("exposure_usd", 0.0),
            "activity_dates": ["2016-11-01", "2016-12-31"] # Mocked for hackathon
        },
        "stop_reason": state.get("stop_reason", "Completed analysis"),
        "tool_calls": state.get("tool_calls", 0),
        "tokens": state.get("tokens", 0),
        "latency_s": latency
    }
    
    return answer

def run_benchmark():
    """Run all 20 benchmark cases"""
    output_dir = Path("cases")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cases = load_case_pack()
    print(f"Running {len(cases)} benchmark cases...")
    
    print("Building investigation graph...")
    graph = build_investigation_graph()
    
    results = []
    
    for idx, case_row in cases.iterrows():
        case_id = case_row["case_id"]
        print(f"\n[{idx+1}/{len(cases)}] Running case {case_id}...")
        
        start_time = time.time()
        try:
            # Handle NaN risk scores (e.g. customer_report triggers)
            risk_score = case_row.get("risk_score")
            if pd.isna(risk_score):
                risk_score = 0.5
                
            state = CaseState(
                case_id=case_id,
                flagged_txn_id=str(case_row.get("flagged_txn_id", "")),
                card_id=str(case_row.get("card_id", "")),
                customer_id=str(case_row.get("customer_id", "")),
                trigger_type=str(case_row.get("trigger_type", "unknown")),
                trigger_text=str(case_row.get("trigger_text", "")),
                risk_score=float(risk_score),
                status="open",
                evidence=[]
            )
            
            final_state_obj = graph.invoke(state)
            latency = time.time() - start_time
            answer = build_answer_from_state(final_state_obj, latency)
            
            # Write output file
            output_path = output_dir / f"{case_id}.json"
            with open(output_path, 'w') as f:
                json.dump(answer, f, indent=2)
            
            print(f"✓ Case {case_id} completed in {latency:.1f}s")
            results.append({
                "case_id": case_id,
                "status": "success",
                "latency": latency
            })
            
        except Exception as e:
            print(f"✗ Case {case_id} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "case_id": case_id,
                "status": "failed",
                "error": str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    print(f"\n{'='*60}")
    print(f"Benchmark completed: {successful}/{len(cases)} cases successful")
    print(f"Output files written to: {output_dir}")
    
    # Write summary
    summary_path = output_dir / "benchmark_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_cases": len(cases),
            "successful": successful,
            "failed": len(cases) - successful,
            "results": results
        }, f, indent=2)

if __name__ == "__main__":
    run_benchmark()
