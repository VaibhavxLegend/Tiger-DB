import sys
import os
import glob
import json
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import FileResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.graph import build_investigation_graph
from agent.state import CaseState
from evaluation.run_benchmark import build_answer_from_state

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="TigerGraph HHGOA UI")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/api/cases")
def get_cases():
    cases = []
    cases_dir = os.path.join(os.path.dirname(__file__), '..', 'cases')
    if os.path.exists(cases_dir):
        for filepath in glob.glob(os.path.join(cases_dir, "*.json")):
            if os.path.basename(filepath) == "benchmark_summary.json":
                continue
            with open(filepath, 'r') as f:
                cases.append(json.load(f))
    return cases

class TriggerRequest(BaseModel):
    case_id: str
    flagged_txn_id: str
    card_id: str
    customer_id: str
    risk_score: float
    
@app.post("/api/trigger")
def trigger_case(request: TriggerRequest):
    graph = build_investigation_graph()
    
    state = CaseState(
        case_id=request.case_id,
        flagged_txn_id=request.flagged_txn_id,
        card_id=request.card_id,
        customer_id=request.customer_id,
        trigger_type="manual_trigger",
        trigger_text=f"Manual review requested with risk score {request.risk_score}",
        risk_score=request.risk_score,
        status="open"
    )
    
    try:
        final_state = graph.invoke(state)
        answer = build_answer_from_state(final_state, 0.0)
        
        # Save to cases dir
        cases_dir = os.path.join(os.path.dirname(__file__), '..', 'cases')
        os.makedirs(cases_dir, exist_ok=True)
        with open(os.path.join(cases_dir, f"{request.case_id}.json"), 'w') as f:
            json.dump(answer, f, indent=2)
            
        return answer
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
