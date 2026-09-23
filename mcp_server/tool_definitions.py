"""
MCP tool definitions with typed input/output schemas
Phase 2: GSQL Tools (Mock implementation for hackathon speed)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# ============================================================================
# Tool Input Schemas
# ============================================================================

class TxnNeighborhoodInput(BaseModel):
    """Input schema for get_txn_neighborhood tool"""
    transaction_id: str = Field(..., description="Transaction ID to investigate")
    card_id: str = Field(..., description="Card ID associated with transaction")
    customer_id: str = Field(..., description="Customer ID associated with card")
    hops: int = Field(default=2, description="Number of hops for neighborhood (1-3)")

class SharedDevicesInput(BaseModel):
    """Input schema for find_shared_devices tool"""
    card_id: str = Field(..., description="Card ID to analyze")
    time_window_hours: int = Field(default=168, description="Time window in hours (default 7 days)")

class SharedCardsInput(BaseModel):
    """Input schema for find_shared_cards tool"""
    card_id: str = Field(..., description="Card ID to analyze")
    link_types: List[str] = Field(
        default=["shared_device", "shared_address", "shared_email"],
        description="Types of links to search for"
    )

class VelocityCheckInput(BaseModel):
    """Input schema for velocity_check tool"""
    card_id: str = Field(..., description="Card ID to check")
    time_window_minutes: int = Field(default=60, description="Time window for velocity check")

class SimilarCasesInput(BaseModel):
    """Input schema for get_similar_past_cases tool"""
    pattern: Optional[str] = Field(None, description="Fraud pattern to match")
    device_id: Optional[str] = Field(None, description="Device ID to match")
    card_id: Optional[str] = Field(None, description="Card ID to match")
    customer_id: Optional[str] = Field(None, description="Customer ID to match")
    limit: int = Field(default=5, description="Maximum number of cases to return")

# ============================================================================
# Tool Output Schemas
# ============================================================================

class TransactionDetail(BaseModel):
    """Transaction information"""
    transaction_id: str
    amount: float
    timestamp: str
    channel: str  # "online" or "in_person"
    product_cd: str
    risk_score: float
    addr1: float
    addr2: float
    p_email_domain: Optional[str] = None

class CardDetail(BaseModel):
    """Card information"""
    card_id: str
    customer_id: str
    network: str
    type: str
    issued_date: Optional[str] = None

class CustomerDetail(BaseModel):
    """Customer information"""
    customer_id: str
    account_age_days: int
    total_transactions: int
    avg_transaction_amount: float
    fraud_history_count: int

class DeviceDetail(BaseModel):
    """Device information"""
    id: str
    type: str  # "mobile" or "desktop"
    info: str
    os: Optional[str] = None
    browser: Optional[str] = None
    screen: Optional[str] = None
    new_found: Optional[str] = None  # "New" or "Found"
    proxy_type: Optional[str] = None
    times_seen_on_card: Optional[int] = None
    first_seen_date: Optional[str] = None

class RecentTransaction(BaseModel):
    """Recent transaction summary"""
    transaction_id: str
    amount: float
    timestamp: str
    channel: str
    minutes_before_flagged: Optional[int] = None
    days_before_flagged: Optional[int] = None

class TxnNeighborhoodOutput(BaseModel):
    """Output schema for get_txn_neighborhood tool"""
    transaction: TransactionDetail
    card: CardDetail
    customer: CustomerDetail
    device: Optional[DeviceDetail]
    recent_transactions: List[RecentTransaction]
    risk_signals: List[str]
    query_metadata: Dict[str, Any]

class SharedDevicesOutput(BaseModel):
    """Output schema for find_shared_devices tool"""
    device: DeviceDetail
    shared_cards: List[Dict[str, Any]]
    time_window_hours: int
    pattern: str
    linked_closed_cases: List[str]
    risk_level: str

class VelocityCheckOutput(BaseModel):
    """Output schema for velocity_check tool"""
    card_id: str
    time_window_minutes: Optional[int] = None
    time_window_hours: Optional[int] = None
    transaction_count: int
    transactions: List[Dict[str, Any]]
    pattern_detected: str
    typical_velocity_for_card: float
    current_velocity: float
    velocity_ratio: float
    risk_level: str

class ClosedCaseDetail(BaseModel):
    """Closed case information"""
    case_id: str
    outcome: str
    pattern: str
    opened_at: str
    closed_at: str
    exposure_usd: float
    n_txns: int
    actions_taken: str
    report_filed: bool
    analyst_notes: str
    match_reason: str
    similarity_score: float

class SimilarCasesOutput(BaseModel):
    """Output schema for get_similar_past_cases tool"""
    cases: List[ClosedCaseDetail]
    query_metadata: Dict[str, Any]

class LinkedCardsOutput(BaseModel):
    """Output schema for find_shared_cards tool"""
    card_id: str
    linked_cards: List[Dict[str, Any]]
    cluster_id: Optional[str]
    cluster_size: int
    risk_level: str

# ============================================================================
# Tool Definitions
# ============================================================================

TOOL_DEFINITIONS = {
    "get_txn_neighborhood": {
        "name": "get_txn_neighborhood",
        "description": """
Get k-hop neighborhood of a transaction including:
- Transaction details (amount, timestamp, channel, risk score)
- Card information (network, type, issuer)
- Customer history (account age, transaction patterns)
- Device details (if online transaction)
- Recent transactions on same card
- Risk signals identified

Returns pre-aggregated summary, not raw rows.
""".strip(),
        "input_schema": TxnNeighborhoodInput,
        "output_schema": TxnNeighborhoodOutput
    },
    
    "find_shared_devices": {
        "name": "find_shared_devices",
        "description": """
Find cards sharing the same device profile within a time window.
Identifies potential fraud rings where multiple cards use the same device.

Returns:
- Device details
- All cards using this device
- Time window analysis
- Pattern classification
- Links to closed cases with same device
- Risk level assessment
""".strip(),
        "input_schema": SharedDevicesInput,
        "output_schema": SharedDevicesOutput
    },
    
    "find_shared_cards": {
        "name": "find_shared_cards",
        "description": """
Find cards linked through shared attributes:
- shared_device: Same device profile
- shared_address: Same billing address/region
- shared_email: Same email domain

Returns linked card clusters and risk assessment.
""".strip(),
        "input_schema": SharedCardsInput,
        "output_schema": LinkedCardsOutput
    },
    
    "velocity_check": {
        "name": "velocity_check",
        "description": """
Check transaction velocity and detect patterns:
- Card testing: Multiple small transactions followed by large
- Burst activity: Unusual frequency for this card
- Compare current velocity to card's typical pattern

Returns velocity metrics and pattern classification.
""".strip(),
        "input_schema": VelocityCheckInput,
        "output_schema": VelocityCheckOutput
    },
    
    "get_similar_past_cases": {
        "name": "get_similar_past_cases",
        "description": """
Retrieve similar closed cases from history based on:
- Fraud pattern match
- Device/card/customer overlap
- Semantic similarity of case narratives

Returns closed cases with outcomes, actions taken, and similarity scores.
This is case memory retrieval for learning from past investigations.
""".strip(),
        "input_schema": SimilarCasesInput,
        "output_schema": SimilarCasesOutput
    }
}

