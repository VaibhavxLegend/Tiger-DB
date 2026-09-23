#!/bin/bash
# Load all data into TigerGraph
# Phase 1: Graph Foundation

set -e  # Exit on error

echo "=== TigerGraph Data Loading Script ==="
echo

# TODO: Add TigerGraph connection check
echo "Checking TigerGraph connection..."
# gsql "ls" || { echo "Error: Cannot connect to TigerGraph"; exit 1; }

echo
echo "Step 1: Creating schema..."
# gsql graph/schema/create_vertices.gsql
# gsql graph/schema/create_edges.gsql
# gsql graph/schema/create_graph.gsql

echo
echo "Step 2: Running loading jobs..."
# gsql graph/loading_jobs/load_transactions.gsql
# gsql graph/loading_jobs/load_identity.gsql
# gsql graph/loading_jobs/load_case_pack.gsql
# gsql graph/loading_jobs/load_closed_cases.gsql

echo
echo "Step 3: Installing queries..."
# gsql graph/queries/get_txn_neighborhood.gsql
# gsql graph/queries/find_shared_devices.gsql
# gsql graph/queries/find_shared_cards.gsql
# gsql graph/queries/velocity_check.gsql
# gsql graph/queries/get_similar_past_cases.gsql

echo
echo "Step 4: Verifying data load..."
# TODO: Run sanity check queries
# - Count vertices by type
# - Count edges by type
# - Verify a known closed case resolves as connected cluster

echo
echo "✓ Data loading complete!"
