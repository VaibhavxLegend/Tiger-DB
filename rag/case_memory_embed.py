"""
Embed closed case narratives and store in vector store
Phase 3: Agent State Machine
"""

import json
import uuid
from typing import Dict, Any, List

# In a real app we'd use ChromaDB or Neo4j Vector
VECTOR_STORE_MOCK = {}

def embed_case(case_id: str, narrative: str, entities: Dict[str, Any]) -> str:
    """Embed a closed case and link it in the graph"""
    print(f"  [MEMORY] Embedding case {case_id} narrative for future search")
    # Generate mock embedding and save
    embedding_id = f"emb_{uuid.uuid4().hex[:8]}"
    VECTOR_STORE_MOCK[case_id] = {
        "id": embedding_id,
        "narrative": narrative,
        "entities": entities
    }
    return embedding_id

def update_case_graph_links(case_id: str, entities: Dict[str, Any], pattern: str):
    """Create graph edges linking case to entities and patterns"""
    print(f"  [MEMORY] Updating graph for case {case_id}")
    print(f"    - Creating Case vertex {case_id}")
    
    # Mocking graph writes
    if entities.get("cards"):
        for card in entities["cards"]:
            print(f"    - Edge: (Case:{case_id}) -[INVOLVES_CARD]-> (Card:{card})")
            
    if entities.get("devices"):
        for device in entities["devices"]:
            print(f"    - Edge: (Case:{case_id}) -[INVOLVES_DEVICE]-> (Device:{device})")
            
    if pattern and pattern != "none":
        print(f"    - Edge: (Case:{case_id}) -[MATCHED_PATTERN]-> (FraudPattern:{pattern})")
