"""Pydantic schema for explain LLM output"""
from pydantic import BaseModel, Field

class ExplanationOutput(BaseModel):
    """
    Structured output from explain node
    Must validate before writing to state
    """
    summary: str = Field(
        ...,
        description="2-6 sentence summary for analysts",
        min_length=50,
        max_length=1000
    )
    
    sar_narrative: str = Field(
        default="",
        description="Full SAR narrative (who, what, when, where, how, why suspicious)"
    )
    
    sar_subjects: list[str] = Field(
        default_factory=list,
        description="IDs of customers, cards, merchants, devices in SAR"
    )
    
    evidence_explanation: str = Field(
        ...,
        description="What evidence was used and why"
    )
    
    uncertainty_explanation: str = Field(
        default="",
        description="Why additional evidence was requested (if any)"
    )
    
    action_justification: str = Field(
        ...,
        description="Why recommended actions follow from evidence and policy"
    )
