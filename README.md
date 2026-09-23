# TigerGraph Agentic Fraud Investigation

An autonomous fraud investigation system that uses TigerGraph as the primary reasoning substrate to investigate flagged transactions, assess risk and uncertainty, and recommend next-best-actions within policy constraints.

## Overview

This system implements an agentic fraud investigation workflow that:
- Investigates flagged transactions using graph traversal and algorithms
- Explicitly handles uncertainty by requesting additional evidence when needed
- Recommends policy-compliant actions with approval routing
- Maintains case memory for future investigations
- Generates regulatory filings (SARs) when required

## Architecture

- **Graph Layer**: TigerGraph (Savanna) with GSQL queries and graph algorithms
- **Agent Orchestration**: LangGraph state machine
- **LLM**: Anthropic Claude for synthesis, uncertainty assessment, and explanation
- **RAG**: Hybrid graph+vector retrieval for policy and case memory
- **Action Layer**: Mock FastAPI endpoints for fraud actions
- **UI**: Next.js dashboard for case visualization

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- TigerGraph Savanna account (free tier)
- Anthropic API key

### Installation

1. Clone the repository
```bash
git clone <repo-url>
cd tigergraph-fraud-agent
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your TigerGraph and Anthropic credentials
```

5. Load data into TigerGraph
```bash
# Pre-process closed cases history
python scripts/preprocess_closed_cases.py

# Run GSQL schema and loading jobs
bash scripts/load_all_data.sh
```

6. Ingest policy documents into vector store
```bash
python rag/policy_ingest.py
```

7. Install UI dependencies
```bash
cd ui
npm install
cd ..
```

## Usage

### Run Benchmark Cases

```bash
python evaluation/run_benchmark.py
```

This will process all 20 cases from `data/raw/case_pack.csv` and output results to `evaluation/output/`.

### Start UI Dashboard

```bash
cd ui
npm run dev
```

Visit http://localhost:3000 to view the dashboard.

### Start Mock Action API

```bash
uvicorn actions.api:app --reload
```

### Start MCP Server

```bash
python mcp_server/server.py
```

## Project Structure

```
├── data/              # Raw and processed datasets
├── docs/              # Planning documents (PRD, Architecture, Implementation Plan)
├── graph/             # TigerGraph schema, queries, loading jobs
├── mcp_server/        # MCP tool layer wrapping GSQL
├── rag/               # Vector store and retrieval
├── agent/             # LangGraph state machine
├── actions/           # Mock action API endpoints
├── ui/                # Next.js dashboard
├── evaluation/        # Benchmark runner and outputs
└── scripts/           # Setup and utility scripts
```

## Key Features

### Graph-Native Reasoning

All pattern detection and relationship analysis happens in TigerGraph via GSQL queries and graph algorithms (WCC, Louvain, PageRank). The LLM is used only for synthesis, uncertainty judgment, and natural language explanation.

### Uncertainty Handling

The system explicitly represents "insufficient evidence" as a valid state. When confidence is below threshold, it requests additional evidence (customer validation, step-up auth, analyst input) before making high-impact decisions.

### Policy Compliance

A deterministic policy engine (not LLM-based) checks approval requirements for every action. Approval routing is logged both before and after evidence gathering.

### Case Memory

Closed cases are stored in both:
- **Graph**: Linked via edges to entities and patterns for traversal-based retrieval
- **Vector store**: Embedded narratives for semantic similarity search

Hybrid retrieval combines both for comprehensive prior case matching.

### Explainability

Every decision cites the specific graph evidence, policy clauses, and prior cases used. All state transitions are logged in an immutable case audit trail.

## Development

### Phase 0: Verify Inputs ✅
- Confirmed CSV schemas match dataset
- Identified benchmark answer format
- Scaffolded repository structure

### Phase 1: Graph Foundation (In Progress)
- TigerGraph schema creation
- Data preprocessing and loading
- GSQL query development

### Phase 2: GSQL Tools + GraphRAG
- MCP server implementation
- Policy/typology ingestion
- Graph algorithm configuration

### Phase 3: Agent State Machine
- LangGraph workflow
- LLM prompt engineering
- Policy engine
- Case memory

### Phase 4: Benchmark Execution
- Run 20 test cases
- Validate outputs

### Phase 5: UI
- Case dashboard
- Live investigation viewer

### Phase 6: Submission Assets
- Demo video
- Technical blog post
- Final cleanup

## License

[Add license information]

## Acknowledgments

- IEEE-CIS Fraud Detection dataset via Vesta Corporation
- TigerGraph Hacker House Goa 2026
