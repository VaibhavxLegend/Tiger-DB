"""Pydantic schema for recommend_action LLM output"""
from typing import Literal
from pydantic import BaseModel, Field

class ActionRecommendation(BaseModel):
    """Single action recommendation"""
    action: Literal[
        "ALLOW_TRANSACTION",
        "DECLINE_TRANSACTION",
        "MONITOR_CARD",
        "MONITOR_CONNECTED_CARDS",
        "WARN_CUSTOMER",
        "VERIFY_WITH_CUSTOMER",
        "STEP_UP_AUTH",
        "BLOCK_CARD",
        "BLOCK_ALL_CARDS",
        "GENERATE_REPORT",
        "CREATE_CASE",
        "FILE_REPORT",
        "ESCALATE_TO_ANALYST",
        "CLOSE_NO_FRAUD"
    ] = Field(..., description="Action from policy taxonomy")
    
    reason: str = Field(
        ...,
        description="Policy rule(s) justifying this action (e.g., 'R1', 'R2')"
    )
    
    rationale: str = Field(
        ...,
        description="Explanation citing evidence"
    )

class ActionRecommendationOutput(BaseModel):
    """
    Structured output from recommend_action node
    Must validate before writing to state
    """
    recommended_actions: list[ActionRecommendation] = Field(
        ...,
        description="Ordered list of recommended actions"
    )
    
    what_changed: str = Field(
        default="",
        description="What changed from initial to final recommendation (if anything)"
    )
    
    file_sar: bool = Field(
        ...,
        description="Whether SAR filing is required"
    )
    
    sar_reason: str = Field(
        default="",
        description="Why SAR is/isn't required"
    )
