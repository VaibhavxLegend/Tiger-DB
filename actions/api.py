"""
Mock action API endpoints for fraud actions
Phase 3: Agent State Machine
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
from typing import Literal

app = FastAPI(title="Fraud Action API (Mock)")

class ActionRequest(BaseModel):
    case_id: str
    action: str
    card_id: str
    customer_id: str
    reason: str

class ActionResponse(BaseModel):
    success: bool
    action: str
    message: str
    latency_ms: int

# Simulated latency for each action type (milliseconds)
ACTION_LATENCY = {
    "ALLOW_TRANSACTION": 50,
    "DECLINE_TRANSACTION": 100,
    "MONITOR_CARD": 80,
    "MONITOR_CONNECTED_CARDS": 150,
    "WARN_CUSTOMER": 200,
    "VERIFY_WITH_CUSTOMER": 300,
    "STEP_UP_AUTH": 250,
    "BLOCK_CARD": 400,
    "BLOCK_ALL_CARDS": 500,
    "GENERATE_REPORT": 100,
    "CREATE_CASE": 150,
    "FILE_REPORT": 600,
    "ESCALATE_TO_ANALYST": 100,
    "CLOSE_NO_FRAUD": 50,
}

@app.post("/action/execute", response_model=ActionResponse)
async def execute_action(request: ActionRequest):
    """
    Execute a fraud action (mock implementation)
    Returns simulated response after simulated latency
    """
    latency = ACTION_LATENCY.get(request.action, 100)
    time.sleep(latency / 1000)  # Simulate latency
    
    # TODO: Add realistic response variations
    return ActionResponse(
        success=True,
        action=request.action,
        message=f"Action {request.action} executed for case {request.case_id}",
        latency_ms=latency
    )

@app.post("/customer/validate")
async def validate_with_customer(request: ActionRequest):
    """Mock customer validation response"""
    # TODO: Return simulated customer response based on case context
    time.sleep(0.3)
    return {
        "response": "simulated_customer_response",
        "confirmed": False  # Varies by case
    }

@app.post("/auth/step-up")
async def step_up_auth(request: ActionRequest):
    """Mock step-up authentication response"""
    time.sleep(0.25)
    return {
        "response": "simulated_auth_response",
        "success": True  # Varies by case
    }

@app.post("/analyst/request-info")
async def request_analyst_info(request: ActionRequest):
    """Mock analyst information request"""
    time.sleep(0.1)
    return {
        "response": "simulated_analyst_response",
        "info": "Additional context from analyst"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
