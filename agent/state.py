"""
LangGraph state definition for fraud investigation
Phase 3: Agent State Machine
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    """Single piece of evidence"""
    claim: str
    source: Literal["graph", "document", "customer", "external"]
    ref: str  # query:name, document:section, evidence_request:N
    entity_ids: List[str]

class Action(BaseModel):
    """Recommended action with approval routing"""
    action: str
    route: Literal["auto", "L1", "L2"]
    reason: str

class EvidenceRequest(BaseModel):
    """Request for additional evidence"""
    type: Literal["customer_validation", "step_up_auth", "analyst_info"]
    asked_after_step: int
    assumed_response: str

class CaseState(BaseModel):
    """
    State object for fraud investigation
    Single source of truth across all LangGraph nodes
    """
    # Case metadata
    case_id: str
    flagged_txn_id: str
    card_id: str
    customer_id: str
    trigger_type: str
    trigger_text: str
    risk_score: Optional[float]
    
    # Investigation state
    status: Literal["open", "investigating", "gathering_evidence", "closed"]
    verdict: Optional[Literal["fraud", "legitimate", "uncertain"]] = None
    fraud_probability: float = 0.0
    confidence: float = 0.0
    
    # Pattern matching
    pattern: Optional[str] = None
    pattern_description: str = ""
    
    # Evidence
    graph_evidence: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Evidence] = Field(default_factory=list)
    evidence_requests: List[EvidenceRequest] = Field(default_factory=list)
    similar_prior_cases: List[str] = Field(default_factory=list)
    
    # Actions
    initial_actions: List[Action] = Field(default_factory=list)
    final_actions: List[Action] = Field(default_factory=list)
    
    # Findings
    explanation_summary: str = ""
    sar_narrative: str = ""
    sar_subjects: List[str] = Field(default_factory=list)
    evidence_explanation: str = ""
    uncertainty_explanation: str = ""
    action_justification: str = ""
    affected_txn_ids: List[str] = Field(default_factory=list)
    first_suspicious_txn_id: str = ""
    connected_card_ids: List[str] = Field(default_factory=list)
    connected_device_profiles: List[str] = Field(default_factory=list)
    exposure_usd: float = 0.0
    
    # Control flow
    iteration_count: int = 0
    sufficient_evidence: bool = False
    stop_reason: str = ""
    
    # Metadata
    tool_calls: int = 0
    tokens: int = 0
    
    # Audit log (append-only)
    state_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    def log_transition(self, node: str, data: Dict[str, Any]):
        """Append state transition to immutable log"""
        self.state_log.append({
            "node": node,
            "iteration": self.iteration_count,
            "data": data
        })
