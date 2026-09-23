"""
Mock response generators for evidence requests
Phase 3: Agent State Machine
"""

def simulate_customer_validation(case_context: dict) -> str:
    """
    Simulate customer response to validation request
    
    Returns realistic responses based on case context:
    - For high fraud probability patterns: customer denies
    - For legitimate patterns: customer confirms
    - For uncertain cases: mixed responses
    """
    # TODO: Implement realistic simulation based on:
    # - Pattern type
    # - Fraud probability
    # - Evidence strength
    
    fraud_prob = case_context.get("fraud_probability", 0.5)
    
    if fraud_prob > 0.7:
        return "Customer states they did not make this purchase and still have the card in possession"
    elif fraud_prob < 0.3:
        return "Customer confirms this was their purchase"
    else:
        return "Customer is unsure, will check and call back"

def simulate_step_up_auth(case_context: dict) -> str:
    """Simulate step-up authentication response"""
    # TODO: Implement realistic simulation
    return "Step-up authentication successful"

def simulate_analyst_info(case_context: dict) -> str:
    """Simulate analyst providing additional context"""
    # TODO: Implement realistic simulation
    return "Analyst confirms pattern matches known fraud ring from previous cases"
