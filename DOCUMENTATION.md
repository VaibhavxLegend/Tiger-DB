# TigerGraph Agentic Fraud Investigation System

## Overview

An autonomous fraud investigation system that uses TigerGraph as the primary reasoning substrate to investigate flagged transactions, assess risk and uncertainty, and recommend next-best-actions within policy constraints.

## Architecture

### Core Components

1. **Agent Orchestration** (`agent/`)
   - LangGraph state machine with 7 explicit investigation nodes
   - CaseState as single source of truth
   - Nodes: trigger, investigate, assess_uncertainty, gather_more_evidence, recommend_action, explain, update_memory

2. **Graph Layer** (`mcp_server/`)
   - MCP (Model Context Protocol) server wrapping TigerGraph traversals
   - Mock data generators for demonstration (swapable for real GSQL)
   - Tools: get_txn_neighborhood, find_shared_devices, velocity_check, get_similar_past_cases

3. **RAG System** (`rag/`)
   - Hybrid graph+vector retrieval for policy requirements and case memory
   - Policy context retrieval
   - Similar case retrieval

4. **Action Layer** (`actions/`)
   - Mock action endpoints for fraud actions execution
   - Policy engine for approval routing

5. **UI Dashboard** (`ui/`)
   - FastAPI + Vanilla JS asynchronous triggers and case browser
   - Real-time case investigation console

6. **Evaluation** (`evaluation/`)
   - Benchmark runner for 20 test cases
   - Outputs strictly formatted results matching benchmark specifications

### Data Flow

1. **Trigger** - UI or API opens a case from `case_pack.csv`
2. **Investigate** - MCP tools gather evidence via graph traversals:
   - Transaction neighborhood (risk signals, amount, channel)
   - Shared devices (fraud rings, device sharing)
   - Velocity check (transaction patterns like card testing)
   - Similar past cases (case memory)
3. **Assess Uncertainty** - Rule-based assessment of:
   - Fraud probability (risk_score + signal boosts)
   - Confidence (corroborating signals)
   - Pattern detection (card_testing, device_sharing, etc.)
   - Sufficient evidence threshold
4. **Gather More Evidence** (if uncertain) - Request:
   - Customer validation
   - Step-up authentication
   - Analyst review
5. **Recommend Actions** - Policy-compliant actions:
   - BLOCK_CARD, CREATE_CASE, FILE_SAR, VERIFY_WITH_CUSTOMER, etc.
   - Routing: auto (low risk), L1 (medium), L2 (high)
6. **Explain** - Generate human-readable narrative:
   - Summary for analysts
   - SAR narrative (if required)
   - Evidence explanation
   - Uncertainty explanation
   - Action justification
7. **Update Memory** - Archive case to graph for future similarity search

## Key Features

### Graph-Native Reasoning
All pattern detection and relationship analysis happens via MCP tool calls to TigerGraph. The LLM (when available) synthesizes and structures ambiguous text.

### Uncertainty Handling
LangGraph conditional edge represents "insufficient evidence" as a valid state loop. When confidence < 0.6, system requests additional evidence up to 3 times before taking high-impact action.

### Policy Compliance
Deterministic policy engine intercepts recommendations to flag approval requirements before generating final timeline.

### Case Memory
Closed cases modeled and stored in graph for traversal retrieval (SIMILAR_TO edges) and as vectors for contextual RAG matching.

### Regulatory Filings
Generates SAR narratives for confirmed fraud cases meeting exposure thresholds.

## State Machine

The LangGraph consists of 7 nodes in this sequence:
```
trigger → investigate → assess_uncertainty → 
[gather_more_evidence] ← (if uncertain & iteration < 3) →
recommend_action → explain → update_memory → end
```

## Configuration

### Environment Variables
- `GOOGLE_API_KEY`: For Gemini LLM calls (not required for deterministic mode)
- TigerGraph connection details in `.env`

### Dependencies
- Python 3.9+
- TigerGraph Savanna account
- Required packages: fastapi, uvicorn, pydantic, python-dotenv, langchain-google-genai

## Usage

### Run Benchmark Cases
```bash
python evaluation/run_benchmark.py
```
Processes all 20 cases from `data/raw/case_pack.csv` and outputs to `cases/` directory.

### Start UI Dashboard
```bash
python ui/main.py
```
Visit `http://localhost:8080/` to view Case Investigation Console.

## Deterministic Mode (No LLM)

When Google API Key is unavailable, the system uses rule-based logic in:
- `assess_uncertainty_node`: Calculates fraud probability from risk signals
- `gather_more_evidence_node`: Selects evidence type based on pattern and iteration
- `explain_node`: Generates template-based explanations from state fields

## File Formats

### Input: `data/raw/case_pack.csv`
Columns: case_id, opened_at, trigger_type, trigger_text, flagged_txn_id, card_id, customer_id, risk_score

### Output: `cases/{case_id}.json`
Structured JSON matching benchmark specification with fields:
- case_id, status, verdict, fraud_probability, pattern, etc.
- evidence array with claims, sources, refs
- explanation summary, SAR narrative, recommended actions

## Extending the System

1. **Replace Mock Data**: Implement real GSQL queries in `mcp_server/server.py`
2. **Add New Patterns**: Extend pattern detection in `assess_uncertainty_node`
3. **Modify Policy**: Update policy documents and retrieval in `rag/`
4. **Add Actions**: Implement new action types in `actions/` and policy engine
5. **Enhance UI**: Add new visualization components in `ui/`

## Benchmark Results

After fixes, the system produces varied verdicts:
- Multiple fraud cases (clear patterns)
- Multiple uncertain cases (borderline signals)
- All deterministic, no LLM calls required