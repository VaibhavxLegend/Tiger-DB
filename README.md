# TigerGraph Agentic Fraud Investigation

An autonomous fraud investigation system that uses TigerGraph as the primary reasoning substrate to investigate flagged transactions, assess risk and uncertainty, and recommend next-best-actions within policy constraints.

*Submitted for the TigerGraph Agentic AI Hackathon 2026*

## Overview

This system implements an agentic fraud investigation workflow that:
- Investigates flagged transactions using graph traversal and MCP tools.
- Explicitly handles uncertainty by conditionally requesting additional evidence (Analyst, Customer) when needed.
- Recommends policy-compliant actions with approval routing.
- Maintains case memory for future investigations (embedded and wired natively back to the Graph).
- Generates regulatory filings (SAR narratives).

## Architecture

- **Graph Layer**: TigerGraph (Savanna) with GSQL queries exposing relationships.
- **Agent Orchestration**: LangGraph state machine with 7 explicit investigation nodes.
- **LLM**: Google Gemini for synthesis, uncertainty assessment, and contextual explanations.
- **RAG**: Hybrid graph+vector retrieval for policy requirements and case memory.
- **Action Layer**: Mock FastAPI endpoints for fraud actions execution.
- **UI**: FastAPI + Vanilla JS asynchronous triggers and case browser.

## Setup

### Prerequisites

- Python 3.9+
- TigerGraph Savanna account (free tier)
- Google Gemini API key (`GOOGLE_API_KEY`)

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
# Edit .env with your TigerGraph and Google Gemini credentials
```

## Usage

### Run Benchmark Cases

```bash
python evaluation/run_benchmark.py
```

This will process all 20 cases in an unattended programmatic loop from `data/raw/case_pack.csv` and output strictly formatted results to the `cases/` directory, exactly matching the benchmark specifications.

### Start UI Dashboard & Run a Single Case

```bash
python ui/main.py
```

Visit `http://localhost:8080/` to view the Case Investigation Console, browse the benchmark results, and manually trigger new LangGraph investigations live.

## Project Structure

```text
├── data/              # Raw data
├── cases/             # Benchmark JSON outputs (20 files)
├── docs/              # Planning documents and architectures
├── graph/             # TigerGraph schema, queries, loading jobs
├── mcp_server/        # MCP tool layer wrapping Graph traversals
├── rag/               # Vector store and hybrid GraphRAG retrievals
├── agent/             # LangGraph state machine & schemas
├── actions/           # Mock action endpoints
├── ui/                # FastAPI triggers console
├── evaluation/        # Benchmark runner
├── submission/        # Assets: demo scripts, blog post, social post
└── scripts/           # Setup and utility scripts
```

## Key Features

### Graph-Native Reasoning
All pattern detection and relationship analysis happens natively querying connected components via MCP endpoints. The LLM synthesizes and structures ambiguous text.

### Uncertainty Handling
The LangGraph conditional edge explicitly represents "insufficient evidence" as a valid state loop. When LLM confidence is below threshold, it routes backwards to simulate requesting additional evidence up to 3 times before taking high-impact action.

### Policy Compliance
A deterministic policy engine intercepts LLM recommendations to flag approval requirements before generating the final timeline.

### Case Memory
Closed cases are modeled and stored in the graph for traversal retrieval (`SIMILAR_TO` edges), and as vectors for contextual RAG matching.
