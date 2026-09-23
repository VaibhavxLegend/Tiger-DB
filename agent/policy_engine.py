"""
Deterministic policy engine for action approval routing
Phase 2: GSQL Tools
"""

from typing import Literal

# Action approval routing per Fraud Policy Section 2
ACTION_APPROVAL_ROUTES = {
    # Auto-approved actions
    "ALLOW_TRANSACTION": "auto",
    "MONITOR_CARD": "auto",
    "MONITOR_CONNECTED_CARDS": "auto",
    "WARN_CUSTOMER": "auto",
    "VERIFY_WITH_CUSTOMER": "auto",
    "STEP_UP_AUTH": "auto",
    "GENERATE_REPORT": "auto",
    "CREATE_CASE": "auto",
    "ESCALATE_TO_ANALYST": "auto",
    "CLOSE_NO_FRAUD": "auto",
    
    # L1 (team lead) approval required
    "DECLINE_TRANSACTION": "L1",
    # BLOCK_CARD depends on exposure (see function below)
    
    # L2 (fraud manager) approval required
    "BLOCK_ALL_CARDS": "L2",
    "FILE_REPORT": "L2",
}

def get_approval_route(
    action: str,
    exposure_usd: float = 0.0
) -> Literal["auto", "L1", "L2"]:
    """
    Get approval route for an action
    
    Args:
        action: Action name from policy taxonomy
        exposure_usd: Total exposure (for BLOCK_CARD routing)
        
    Returns:
        Approval route: "auto", "L1", or "L2"
    """
    # Special case: BLOCK_CARD depends on exposure
    if action == "BLOCK_CARD":
        return "L1" if exposure_usd <= 2500 else "L2"
    
    # Default routing
    return ACTION_APPROVAL_ROUTES.get(action, "L2")  # Default to highest approval if unknown

def check_policy_compliance(
    action: str,
    state: dict,
    reason: str
) -> dict:
    """
    Check if action complies with fraud policy rules
    
    Args:
        action: Proposed action
        state: Current case state
        reason: Reason/rule cited (e.g., "R1", "R2")
        
    Returns:
        dict with compliance result and any warnings
    """
    # TODO: Implement policy rule validation
    # - R1: Verify before block on weak signal
    # - R2: Customer denies -> block + case + report
    # - R3: Customer confirms -> close
    # - R4: No reply -> monitor + decline
    # - R5: Card testing -> decline + step-up
    # - R6: Shared origin -> case + report + monitor connected
    # - R7: Disputed but legitimate -> case + verify + warn
    # - R8: Escalate when uncertain + exposed > $500
    # - R9: Undocumented patterns -> case + report + escalate
    # - R10: Never block all cards unless 2+ confirmed fraud
    
    return {
        "compliant": True,
        "warnings": []
    }

def should_file_sar(
    fraud_probability: float,
    exposure_usd: float,
    has_shared_device: bool,
    has_shared_region: bool,
    is_coordinated: bool
) -> bool:
    """
    Determine if SAR filing is required per policy
    
    SAR required when:
    - Fraud confirmed/strongly suspected AND
    - (exposure > $1000 OR shared device/region OR coordinated pattern)
    """
    if fraud_probability < 0.7:
        return False
    
    return (
        exposure_usd > 1000 or
        has_shared_device or
        has_shared_region or
        is_coordinated
    )
