"""Pydantic schema for gather_more_evidence LLM output"""
from typing import Literal
from pydantic import BaseModel, Field

class EvidenceRequestOutput(BaseModel):
    """
    Structured output from gather_more_evidence node
    Must validate before writing to state
    """
    evidence_type: Literal[
        "customer_validation",
        "step_up_auth",
        "analyst_info"
    ] = Field(..., description="Type of evidence to request")
    
    justification: str = Field(
        ...,
        description="Why this evidence is needed, citing policy rule"
    )
    
    simulated_response: str = Field(
        ...,
        description="Assumed response for this request"
    )
    
    expected_impact: str = Field(
        ...,
        description="How this evidence will affect the assessment"
    )
