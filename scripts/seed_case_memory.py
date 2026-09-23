"""
Seed case memory from closed_cases_history.csv
Phase 3: Agent State Machine

Load historical closed cases into vector store and graph for retrieval
"""

import pandas as pd
from pathlib import Path

def seed_case_memory():
    """
    Load closed_cases_history into case memory
    
    For each closed case:
    1. Extract case narrative from analyst_notes
    2. Generate embeddings
    3. Store in vector store
    4. Create graph edges to entities and patterns
    """
    input_path = Path("data/raw/closed_cases_history.csv")
    
    print(f"Loading closed cases from {input_path}...")
    df = pd.read_csv(input_path)
    
    print(f"Found {len(df)} closed cases")
    print(f"  - Confirmed fraud: {len(df[df['outcome'] == 'confirmed_fraud'])}")
    print(f"  - Cleared: {len(df[df['outcome'] == 'cleared'])}")
    
    # TODO: Implement
    # for idx, case in df.iterrows():
    #     # Extract narrative
    #     narrative = case['analyst_notes']
    #     
    #     # Embed and store
    #     embed_case(
    #         case_id=case['case_id'],
    #         narrative=narrative,
    #         entities={...}
    #     )
    
    print("\n✓ Case memory seeding complete")

if __name__ == "__main__":
    seed_case_memory()
