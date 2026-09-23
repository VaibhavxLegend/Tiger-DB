"""Pydantic schema for assess_uncertainty LLM output"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

class AssessmentOutput(BaseModel):
    """
    Structured output from assess_uncertainty node
    Must validate before writing to state
    """
    pattern: Literal[
        "card_testing",
        "card_not_present_fraud",
        "card_not_present_new_device",
        "out_of_region_use",
        "account_takeover",
        "undocumented",
        "none"
    ] = Field(..., description="Identified fraud pattern")
    
    pattern_description: str = Field(
        default="",
        description="Required when pattern=undocumented: describe the pattern"
    )
    
    fraud_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability this is fraud (0-1)"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the assessment (0-1)"
    )
    
    sufficient_evidence: bool = Field(
        ...,
        description="Whether we have enough evidence to act"
    )
    
    rationale: str = Field(
        ...,
        description="Explanation citing specific evidence items"
    )
    
    affected_txn_ids: list[str] = Field(
        default_factory=list,
        description="Transaction IDs identified as part of fraud episode"
    )
    
    first_suspicious_txn_id: Optional[str] = Field(
        default=None,
        description="Where the fraud started"
    )
    
    connected_card_ids: list[str] = Field(
        default_factory=list,
        description="Other cards involved in the pattern"
    )
    
    connected_device_profiles: list[str] = Field(
        default_factory=list,
        description="Device profiles linking this case to others"
    )
    
    exposure_usd: float = Field(
        default=0.0,
        description="Total exposure in USD"
    )
