"""
Hybrid retrieval: graph traversal + vector similarity
Phase 2: GraphRAG (Mock implementation for hackathon speed)
"""

from typing import List, Dict, Any
from rag.policy_ingest import retrieve_policy_context, POLICY_STORE, ingest_policy_documents

# Initialize policy store
if not POLICY_STORE:
    ingest_policy_documents()

def retrieve_similar_cases(
    entities: List[str],
    pattern: str,
    narrative_query: str = None,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval of similar past cases
    
    Combines:
    1. Graph traversal (via MCP tools - get_similar_past_cases)
    2. Vector similarity (for semantic matching - simplified for hackathon)
    
    Args:
        entities: Entity IDs (card, customer, device) to match
        pattern: Fraud pattern to match
        narrative_query: Text query for semantic search
        top_k: Number of results to return
        
    Returns:
        List of similar cases with metadata
    """
    
    # For hackathon: This would call the MCP tool
    # In real implementation, combines graph + vector results
    
    # Import here to avoid circular dependency
    from mcp_server.server import get_server
    
    server = get_server()
    
    # Extract device_id and card_id from entities if present
    device_id = None
    card_id = None
    for entity in entities:
        if entity.startswith('D'):
            device_id = entity
        elif entity.startswith('C'):
            card_id = entity
    
    # Call MCP tool for graph-based retrieval
    result = server.call_tool("get_similar_past_cases", {
        "pattern": pattern,
        "device_id": device_id,
        "card_id": card_id,
        "limit": top_k
    })
    
    if result.get("success"):
        cases = result["result"]["cases"]
        
        # Add retrieval metadata
        for case in cases:
            case["retrieval_method"] = "hybrid_graph_vector"
            case["retrieved_at"] = "2016-11-14T10:00:00Z"
        
        return cases
    else:
        return []

def retrieve_policy_context_for_case(
    pattern: str,
    entities: List[str],
    risk_signals: List[str],
    fraud_probability: float = None
) -> Dict[str, Any]:
    """
    Retrieve relevant policy and typology context for a case
    
    Args:
        pattern: Identified fraud pattern
        entities: Entities involved
        risk_signals: Risk signals detected
        fraud_probability: Assessed fraud probability
        
    Returns:
        Dict with policy excerpts, typology descriptions, rules
    """
    
    # Retrieve pattern description
    pattern_context = retrieve_policy_context(pattern=pattern, top_k=2)
    
    # Retrieve relevant policy rules based on situation
    rules_to_retrieve = []
    
    # R1: Verify before block (if uncertain)
    if fraud_probability and fraud_probability < 0.70:
        rules_to_retrieve.append("R1")
    
    # R5: Card testing
    if pattern == "card_testing":
        rules_to_retrieve.append("R5")
    
    # R6: Shared origin
    if any("shared" in signal for signal in risk_signals):
        rules_to_retrieve.append("R6")
    
    # R8: Escalate when uncertain
    if fraud_probability and 0.3 < fraud_probability < 0.7:
        rules_to_retrieve.append("R8")
    
    # R9: Undocumented patterns
    if pattern == "undocumented":
        rules_to_retrieve.append("R9")
    
    # Retrieve rule context
    rules_context = []
    for rule in rules_to_retrieve:
        chunks = retrieve_policy_context(rule=rule, top_k=1)
        rules_context.extend(chunks)
    
    # Retrieve action context (approval routing)
    actions_context = retrieve_policy_context(action="BLOCK_CARD", top_k=1)
    approval_context = retrieve_policy_context(query="approval routing", top_k=1)
    
    # Retrieve SAR filing requirements
    sar_context = retrieve_policy_context(action="FILE_REPORT", top_k=1)
    
    return {
        "pattern_description": pattern_context,
        "relevant_rules": rules_context,
        "action_policy": actions_context,
        "approval_routing": approval_context,
        "sar_requirements": sar_context,
        "retrieval_metadata": {
            "pattern": pattern,
            "rules_retrieved": rules_to_retrieve,
            "total_chunks": (
                len(pattern_context) +
                len(rules_context) +
                len(actions_context) +
                len(approval_context) +
                len(sar_context)
            )
        }
    }

def build_graphrag_context(
    transaction_data: Dict[str, Any],
    shared_devices_data: Dict[str, Any],
    velocity_data: Dict[str, Any],
    similar_cases: List[Dict[str, Any]],
    pattern: str,
    fraud_probability: float
) -> str:
    """
    Build formatted GraphRAG context for LLM prompts
    
    Combines:
    - Graph evidence (structured data from MCP tools)
    - Policy context (relevant rules and typologies)
    - Prior cases (similar investigations)
    
    Returns formatted markdown context string
    """
    
    # Extract key info
    txn = transaction_data.get("transaction", {})
    risk_signals = transaction_data.get("risk_signals", [])
    
    # Get policy context
    policy_context = retrieve_policy_context_for_case(
        pattern=pattern,
        entities=[txn.get("transaction_id", "")],
        risk_signals=risk_signals,
        fraud_probability=fraud_probability
    )
    
    # Build formatted context
    context_parts = []
    
    # 1. Graph Evidence Summary
    context_parts.append("## Graph Evidence\n")
    context_parts.append(f"**Transaction**: ${txn.get('amount', 0):.2f} via {txn.get('channel', 'unknown')}")
    context_parts.append(f"**Risk Score**: {txn.get('risk_score', 0):.2f}")
    context_parts.append(f"**Risk Signals**: {', '.join(risk_signals)}\n")
    
    if shared_devices_data and shared_devices_data.get("risk_level") == "high":
        context_parts.append(f"**Shared Device**: {shared_devices_data['pattern']}")
        context_parts.append(f"  - Cards involved: {len(shared_devices_data['shared_cards'])}")
        context_parts.append(f"  - Linked cases: {', '.join(shared_devices_data.get('linked_closed_cases', []))}\n")
    
    if velocity_data and velocity_data.get("pattern_detected") != "normal":
        context_parts.append(f"**Velocity**: {velocity_data['pattern_detected']}")
        context_parts.append(f"  - Transactions: {velocity_data['transaction_count']} in {velocity_data.get('time_window_minutes', 60)} min")
        context_parts.append(f"  - Velocity ratio: {velocity_data.get('velocity_ratio', 1):.1f}x normal\n")
    
    # 2. Pattern Description
    if policy_context["pattern_description"]:
        context_parts.append("\n## Fraud Pattern Context\n")
        for chunk in policy_context["pattern_description"][:1]:
            context_parts.append(f"**{chunk['title']}**")
            context_parts.append(chunk['text'][:300] + "...\n")
    
    # 3. Relevant Policy Rules
    if policy_context["relevant_rules"]:
        context_parts.append("\n## Relevant Policy Rules\n")
        for chunk in policy_context["relevant_rules"]:
            context_parts.append(f"**{chunk['title']}**")
            context_parts.append(chunk['text'][:200] + "...\n")
    
    # 4. Similar Past Cases
    if similar_cases:
        context_parts.append("\n## Similar Past Cases\n")
        for case in similar_cases[:2]:
            context_parts.append(f"**{case['case_id']}** ({case['outcome']})")
            context_parts.append(f"  - Pattern: {case['pattern']}")
            context_parts.append(f"  - Exposure: ${case['exposure_usd']:.2f}")
            context_parts.append(f"  - Actions: {case['actions_taken']}")
            context_parts.append(f"  - Notes: {case['analyst_notes'][:150]}...\n")
    
    return "\n".join(context_parts)

# For testing
if __name__ == "__main__":
    print("=" * 60)
    print("GraphRAG Context Builder Test")
    print("=" * 60)
    
    # Test policy retrieval
    print("\n1. Testing policy context retrieval...")
    context = retrieve_policy_context_for_case(
        pattern="card_testing",
        entities=["C12345-K1", "D000731"],
        risk_signals=["new_device", "multiple_small_transactions"],
        fraud_probability=0.85
    )
    
    print(f"  ✓ Retrieved {context['retrieval_metadata']['total_chunks']} chunks")
    print(f"  - Pattern chunks: {len(context['pattern_description'])}")
    print(f"  - Rules: {context['retrieval_metadata']['rules_retrieved']}")
    
    # Test similar cases retrieval
    print("\n2. Testing similar cases retrieval...")
    cases = retrieve_similar_cases(
        entities=["C12345-K1", "D000731"],
        pattern="card_testing",
        top_k=3
    )
    print(f"  ✓ Retrieved {len(cases)} similar cases")
    for case in cases:
        print(f"    - {case['case_id']}: {case['outcome']} ({case['pattern']})")
    
    print("\n" + "=" * 60)
    print("✓ Hybrid retrieval ready")
    print("=" * 60)
