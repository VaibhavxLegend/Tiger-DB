"""
Pre-process closed_cases_history.csv: explode list columns
Phase 1: Graph Foundation

CRITICAL: closed_cases_history.csv has pipe-separated list columns that must be
split into individual rows before GSQL loading:
- txn_ids: pipe-separated transaction IDs
- connected_card_ids: pipe-separated card IDs
"""

import pandas as pd
from pathlib import Path
import numpy as np

def explode_closed_cases():
    """
    Split pipe-separated list columns into exploded rows
    Output: data/processed/closed_cases_history_exploded.csv
    """
    input_path = Path("data/raw/closed_cases_history.csv")
    output_path = Path("data/processed/closed_cases_history_exploded.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Reading {input_path}...")
    df = pd.read_csv(input_path)
    
    print(f"Original shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst few rows of txn_ids:")
    print(df['txn_ids'].head(3))
    
    # Split txn_ids on '|' character
    print("\nSplitting txn_ids column...")
    df['txn_ids_list'] = df['txn_ids'].fillna('').str.split('|')
    
    # Split connected_card_ids on '|' character
    print("Splitting connected_card_ids column...")
    df['connected_card_ids_list'] = df['connected_card_ids'].fillna('').str.split('|')
    
    # Explode txn_ids into multiple rows
    print("Exploding txn_ids...")
    df_exploded = df.explode('txn_ids_list').reset_index(drop=True)
    
    # Rename exploded column
    df_exploded['txn_id'] = df_exploded['txn_ids_list']
    
    # For connected_card_ids, we'll keep as list for now and handle in loading job
    # Or explode separately if needed
    df_exploded['connected_card_ids_str'] = df_exploded['connected_card_ids_list'].apply(
        lambda x: '|'.join(x) if isinstance(x, list) else ''
    )
    
    # Clean up: remove rows with empty txn_id
    df_exploded = df_exploded[df_exploded['txn_id'].str.len() > 0]
    
    # Select relevant columns for loading
    output_cols = [
        'case_id', 'customer_id', 'card_id', 'opened_at', 'closed_at',
        'outcome', 'pattern', 'first_fraud_txn_id', 'txn_id',
        'n_txns', 'exposure_usd', 'connected_card_ids_str',
        'actions_taken', 'report_filed', 'analyst_notes'
    ]
    
    df_output = df_exploded[output_cols].copy()
    
    print(f"\nWriting to {output_path}...")
    df_output.to_csv(output_path, index=False)
    
    print("\n✓ Preprocessing complete")
    print(f"  Input:  {len(df)} cases")
    print(f"  Output: {len(df_output)} rows (exploded by transaction)")
    print(f"\nSample output:")
    print(df_output.head())
    print(f"\nOutput columns: {df_output.columns.tolist()}")

if __name__ == "__main__":
    explode_closed_cases()
