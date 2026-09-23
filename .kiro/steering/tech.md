# Technical Stack

## Core Technologies

### Graph & Data Layer

- **TigerGraph (Savanna)**: Primary reasoning substrate for relationship and pattern detection
- **GSQL**: Graph query language for deterministic evidence gathering
- **Built-in Graph Algorithms**: WCC (weakly-connected-components), Louvain, PageRank, shortest-path

### Agent & Orchestration

- **LangGraph**: State machine orchestration for investigation workflow
- **Anthropic Claude**: LLM for synthesis, uncertainty assessment, action selection, and explanation

### Backend

- **Python**: Primary development language
- **FastAPI**: Mock action APIs (allow/block transaction, escalate, etc.)
- **MCP (Model Context Protocol)**: Tool layer wrapping GSQL queries as typed agent tools

### RAG & Memory

- **Chroma**: Local vector store for policy documents, typology descriptions, and case embeddings
- **GraphRAG**: Hybrid retrieval combining graph traversal + vector similarity

### Frontend

- **Next.js**: UI dashboard for case visualization
- **WebSocket**: Live case status streaming during investigation

## Project Architecture

### Directory Structure

``` text
graph/              # TigerGraph schema, GSQL queries, loading jobs
mcp_server/         # MCP tool layer wrapping GSQL as typed tools
rag/                # Vector store, retrieval, policy/typology ingestion
agent/              # LangGraph state machine, case state, prompts
actions/            # Mock action API endpoints
ui/                 # Next.js dashboard
evaluation/         # Benchmark runner and output files
data/               # Raw and processed CSV datasets
```

## Key Design Patterns

### Graph-Native Reasoning

- GSQL queries and graph algorithms perform deterministic pattern detection
- MCP tools return **pre-aggregated summaries**, not raw rows
- LLM receives structured, low-noise GraphRAG context

### State Machine Flow

``` text
trigger → investigate → assess_uncertainty
              ↑              ↓
              └─────┐    sufficient?
                    │    ↓ No
          gather_more_evidence
                    │
                    ↓ Yes
        recommend_action → explain → update_memory
```

### Policy Engine

- Deterministic module (not LLM) that checks approval requirements
- Logs approval routing before and after evidence gathering
- Sourced from parsed fraud policy document

## Common Commands

### TigerGraph

```bash
# Schema creation
gsql graph/schema/create_vertices.gsql
gsql graph/schema/create_edges.gsql
gsql graph/schema/create_graph.gsql

# Data loading
gsql graph/loading_jobs/load_transactions.gsql
gsql graph/loading_jobs/load_identity.gsql
gsql graph/loading_jobs/load_case_pack.gsql

# Query installation
gsql graph/queries/get_txn_neighborhood.gsql
gsql graph/queries/find_shared_devices.gsql
```

### Python/Backend

```bash
# Install dependencies
pip install langchain langgraph anthropic fastapi uvicorn chromadb

# Run mock action API
uvicorn actions.api:app --reload

# Run MCP server
python mcp_server/server.py

# Run benchmark
python evaluation/run_benchmark.py
```

### Frontend Run

```bash
# Install and run UI
cd ui
npm install
npm run dev
```

## Data Constraints

- **No ground-truth fraud labels** in live data — decisions use risk scores + graph evidence
- **Savanna free tier**: Auto-stop/auto-start enabled to control resource usage
- **Bounded evidence loop**: Max 3 iterations to guarantee termination
- **Temperature kept low**: For reproducible assessment/action decisions

## Performance Targets

- Single case investigation: < 2 minutes end-to-end
- Benchmark run: 20 cases unattended with consistent outputs
- Reasonable latency through bounded tool calls and evidence loop iterations
