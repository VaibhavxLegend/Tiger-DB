"""
Run all 20 benchmark cases and generate output files
Phase 4: Benchmark Execution
"""

import json
import time
from pathlib import Path
from datetime import datetime
import pandas as pd

# TODO: Import agent graph and state
# from agent.graph import build_investigation_graph
# from agent.state import CaseState

def load_case_pack():
    """Load the 20 benchmark cases"""
    case_pack_path = Path("data/raw/case_pack.csv")
    return pd.read_csv(case_pack_path)

def run_single_case(case_row: dict) -> dict:
    """
    Run investigation for a single case
    
    Returns answer file dict matching required format
    """
    start_time = time.time()
    
    # TODO: Implement
    # 1. Initialize CaseState from case_row
    # 2. Run investigation graph
    # 3. Extract results
    # 4. Format as answer file
    # 5. Write to graph
    
    # Placeholder structure
    answer = {
        "case_id": case_row["case_id"],
        "case": {
            "status": "open",
            "verdict": "uncertain",
            "fraud_probability": 0.5,
            "pattern": "none",
            "pattern_description": "",
            "affected_txn_ids": [],
            "first_suspicious_txn_id": "",
            "connected_card_ids": [],
            "connected_device_profiles": [],
            "exposure_usd": 0.0,
            "evidence": [],
            "similar_prior_cases": [],
            "summary": "",
            "written_to_graph": False,
            "graph_case_id": ""
        },
        "evidence_requests": [],
        "next_best_actions": {
            "initial": [],
            "final": [],
            "what_changed": ""
        },
        "sar": {
            "file": False,
            "reason": "",
            "narrative": "",
            "subjects": [],
            "total_amount_usd": 0.0,
            "activity_dates": []
        },
        "stop_reason": "",
        "tool_calls": 0,
        "tokens": 0,
        "latency_s": time.time() - start_time
    }
    
    return answer

def run_benchmark():
    """Run all 20 benchmark cases"""
    output_dir = Path("evaluation/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cases = load_case_pack()
    print(f"Running {len(cases)} benchmark cases...")
    
    results = []
    
    for idx, case_row in cases.iterrows():
        case_id = case_row["case_id"]
        print(f"\n[{idx+1}/{len(cases)}] Running case {case_id}...")
        
        try:
            answer = run_single_case(case_row.to_dict())
            
            # Write output file
            output_path = output_dir / f"{case_id}.json"
            with open(output_path, 'w') as f:
                json.dump(answer, f, indent=2)
            
            print(f"✓ Case {case_id} completed in {answer['latency_s']:.1f}s")
            results.append({
                "case_id": case_id,
                "status": "success",
                "latency": answer['latency_s']
            })
            
        except Exception as e:
            print(f"✗ Case {case_id} failed: {e}")
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
