#!/usr/bin/env bash
# setup_tigergraph.sh — install GSQL schema + queries into TigerGraph Cloud
# Usage: ./scripts/setup_tigergraph.sh
# Requires: GSQL CLI or pyTigerGraph; TG_HOST, TG_API_TOKEN in .env

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env
if [ -f "$ROOT/.env" ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' "$ROOT/.env" | xargs)
fi

: "${TG_HOST:?Set TG_HOST in .env}"
: "${TG_GRAPH_NAME:=FraudInvestigation}"

echo "==> Connecting to: $TG_HOST / graph: $TG_GRAPH_NAME"

python3 - <<PYEOF
import os
from pyTigerGraph import TigerGraphConnection

host      = os.environ["TG_HOST"]
graphname = os.environ.get("TG_GRAPH_NAME", "FraudInvestigation")
token     = os.environ.get("TG_API_TOKEN", "")
is_cloud  = os.environ.get("TG_TGCLOUD", "").lower() == "true"

conn = TigerGraphConnection(host=host, graphname=graphname,
                            apiToken=token, tgCloud=is_cloud)
print("Echo:", conn.echo())

root = "$ROOT"

def run_gsql(path):
    with open(path) as f:
        gsql = f.read()
    result = conn.gsql(gsql)
    print(f"  {path}: {str(result)[:120]}")

print("--- Installing schema ---")
run_gsql(f"{root}/graph/schema/create_vertices.gsql")
run_gsql(f"{root}/graph/schema/create_edges.gsql")
run_gsql(f"{root}/graph/schema/create_graph.gsql")

print("--- Installing queries ---")
for q in ["get_txn_neighborhood", "find_shared_devices",
          "find_shared_cards", "velocity_check", "get_similar_past_cases"]:
    run_gsql(f"{root}/graph/queries/{q}.gsql")

print("--- Installing loading jobs ---")
run_gsql(f"{root}/graph/loading_jobs/load_transactions.gsql")
run_gsql(f"{root}/graph/loading_jobs/load_case_pack.gsql")

print("Done. Run 'python scripts/load_data.py' to load CSV data.")
PYEOF
