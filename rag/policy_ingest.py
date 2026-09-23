"""
Ingest fraud policy, typologies, and regulatory references into vector store
Phase 2: GraphRAG (Mock implementation for hackathon speed)

For hackathon: Using simple dictionary-based retrieval instead of full vector store.
Can be upgraded to ChromaDB post-hackathon.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import re

# Simple in-memory store for hackathon speed
POLICY_STORE = {}

def load_markdown_file(filepath: Path) -> List[Dict[str, Any]]:
    """Load and chunk a markdown file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Split by headers
    sections = re.split(r'\n##+ ', content)
    
    chunks = []
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        # Extract title (first line)
        lines = section.split('\n', 1)
        title = lines[0].strip()
        text = lines[1] if len(lines) > 1 else ""
        
        chunks.append({
            "id": f"{filepath.stem}_chunk_{i}",
            "source": str(filepath),
            "title": title,
            "text": text.strip(),
            "chunk_index": i
        })
    
    return chunks

def ingest_policy_documents():
    """Ingest all policy documents into store"""
    policy_dir = Path("data/policy")
    
    print("Ingesting policy documents...")
    
    # Documents to ingest
    docs = [
        "fraud_policy.md",
        "fraud_typologies.md",
        "regulatory_references.md"
    ]
    
    total_chunks = 0
    
    for doc_name in docs:
        doc_path = policy_dir / doc_name
        
        if not doc_path.exists():
            print(f"  ⚠️  {doc_name} not found")
            continue
        
        print(f"  Processing {doc_name}...")
        
        chunks = load_markdown_file(doc_path)
        
        # Store chunks
        for chunk in chunks:
            POLICY_STORE[chunk["id"]] = chunk
        
        print(f"    ✓ {len(chunks)} chunks extracted")
        total_chunks += len(chunks)
    
    print(f"\n✓ Total: {total_chunks} chunks ingested")
    
    # Create some useful indexes for quick retrieval
    create_indexes()
    
    return total_chunks

def create_indexes():
    """Create indexes for fast retrieval"""
    
    # Index by policy rules
    rules_index = {}
    for chunk_id, chunk in POLICY_STORE.items():
        # Find R1, R2, etc. in text
        rules = re.findall(r'\bR\d+\b', chunk["text"])
        for rule in rules:
            if rule not in rules_index:
                rules_index[rule] = []
            rules_index[rule].append(chunk_id)
    
    POLICY_STORE["_index_rules"] = rules_index
    
    # Index by fraud patterns
    patterns = [
        "card_testing", "card_not_present_fraud", "card_not_present_new_device",
        "out_of_region_use", "account_takeover", "undocumented"
    ]
    
    patterns_index = {}
    for pattern in patterns:
        patterns_index[pattern] = []
        for chunk_id, chunk in POLICY_STORE.items():
            if chunk_id.startswith("_"):
                continue
            if pattern.replace("_", " ") in chunk["text"].lower():
                patterns_index[pattern].append(chunk_id)
    
    POLICY_STORE["_index_patterns"] = patterns_index
    
    # Index by actions
    actions = [
        "ALLOW_TRANSACTION", "DECLINE_TRANSACTION", "BLOCK_CARD", "BLOCK_ALL_CARDS",
        "MONITOR_CARD", "VERIFY_WITH_CUSTOMER", "FILE_REPORT", "CREATE_CASE",
        "ESCALATE_TO_ANALYST"
    ]
    
    actions_index = {}
    for action in actions:
        actions_index[action] = []
        for chunk_id, chunk in POLICY_STORE.items():
            if chunk_id.startswith("_"):
                continue
            if action in chunk["text"]:
                actions_index[action].append(chunk_id)
    
    POLICY_STORE["_index_actions"] = actions_index

def retrieve_policy_context(
    pattern: str = None,
    rule: str = None,
    action: str = None,
    query: str = None,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant policy chunks
    
    Args:
        pattern: Fraud pattern name
        rule: Policy rule (e.g., "R1", "R5")
        action: Action name
        query: Free text query
        top_k: Number of chunks to return
        
    Returns:
        List of relevant policy chunks
    """
    
    if not POLICY_STORE:
        ingest_policy_documents()
    
    relevant_chunk_ids = set()
    
    # Index-based retrieval
    if rule and "_index_rules" in POLICY_STORE:
        chunk_ids = POLICY_STORE["_index_rules"].get(rule, [])
        relevant_chunk_ids.update(chunk_ids[:top_k])
    
    if pattern and "_index_patterns" in POLICY_STORE:
        chunk_ids = POLICY_STORE["_index_patterns"].get(pattern, [])
        relevant_chunk_ids.update(chunk_ids[:top_k])
    
    if action and "_index_actions" in POLICY_STORE:
        chunk_ids = POLICY_STORE["_index_actions"].get(action, [])
        relevant_chunk_ids.update(chunk_ids[:top_k])
    
    # Simple keyword search if query provided
    if query:
        query_lower = query.lower()
        for chunk_id, chunk in POLICY_STORE.items():
            if chunk_id.startswith("_"):
                continue
            if query_lower in chunk["text"].lower():
                relevant_chunk_ids.add(chunk_id)
                if len(relevant_chunk_ids) >= top_k:
                    break
    
    # Retrieve chunks
    results = []
    for chunk_id in list(relevant_chunk_ids)[:top_k]:
        if chunk_id in POLICY_STORE:
            results.append(POLICY_STORE[chunk_id])
    
    return results

def get_policy_rule_text(rule: str) -> str:
    """Get the full text of a policy rule"""
    chunks = retrieve_policy_context(rule=rule, top_k=1)
    if chunks:
        return chunks[0]["text"]
    return f"Policy rule {rule} not found"

def get_pattern_description(pattern: str) -> str:
    """Get the description of a fraud pattern"""
    chunks = retrieve_policy_context(pattern=pattern, top_k=1)
    if chunks:
        return chunks[0]["text"]
    return f"Pattern {pattern} not found"

# Auto-ingest on module import for convenience
if __name__ == "__main__":
    print("=" * 60)
    print("Policy Document Ingestion")
    print("=" * 60)
    
    ingest_policy_documents()
    
    # Test retrieval
    print("\n" + "=" * 60)
    print("Testing Retrieval")
    print("=" * 60)
    
    print("\n1. Retrieving R5 (card testing rule):")
    chunks = retrieve_policy_context(rule="R5")
    for chunk in chunks:
        print(f"  - {chunk['title']}")
        print(f"    {chunk['text'][:100]}...")
    
    print("\n2. Retrieving card_testing pattern:")
    chunks = retrieve_policy_context(pattern="card_testing")
    for chunk in chunks:
        print(f"  - {chunk['title']}")
    
    print("\n3. Retrieving FILE_REPORT action:")
    chunks = retrieve_policy_context(action="FILE_REPORT")
    for chunk in chunks:
        print(f"  - {chunk['title']}")
    
    print("\n" + "=" * 60)
    print(f"✓ Policy store ready with {len([k for k in POLICY_STORE.keys() if not k.startswith('_')])} chunks")
    print("=" * 60)
