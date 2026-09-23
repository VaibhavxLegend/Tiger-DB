# Project Structure

## Repository File Structure

```text
tigergraph-fraud-agent/
│
├── README.md                          # setup, run instructions, architecture summary
├── .env.example                       # API keys, TG connection, no secrets committed
├── .gitignore
│
├── docs/                               # planning artifacts (this deliverable)
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── SPEC_PROMPTS.md                 # prompt specs for every LLM-driven node
│
├── data/
│   ├── raw/                           # original CSVs, untouched
│   │   ├── case_pack.csv
│   │   ├── closed_cases_history.csv
│   │   ├── identity.csv
│   │   └── transaction.csv
│   ├── policy/                        # fraud policy doc, typologies, reg refs (for RAG)
│   │   ├── fraud_policy.pdf
│   │   ├── fraud_typologies.md
│   │   └── regulatory_references.md
│   └── processed/                     # cleaned/split versions ready for GSQL LOAD
│       ├── closed_cases_history_exploded.csv
│       └── ...
│
├── graph/
│   ├── schema/
│   │   ├── create_vertices.gsql
│   │   ├── create_edges.gsql
│   │   └── create_graph.gsql
│   ├── loading_jobs/
│   │   ├── load_transactions.gsql
│   │   ├── load_identity.gsql
│   │   ├── load_case_pack.gsql
│   │   └── load_closed_cases.gsql
│   ├── queries/
│   │   ├── get_txn_neighborhood.gsql
│   │   ├── find_shared_devices.gsql
│   │   ├── find_shared_cards.gsql
│   │   ├── velocity_check.gsql
│   │   ├── get_similar_past_cases.gsql
│   │   └── run_community_detection.gsql
│   └── algorithms/
│       └── algo_configs.json
│
├── mcp_server/
│   ├── server.py
│   ├── tool_definitions.py
│   └── config.yaml
│
├── rag/
│   ├── policy_ingest.py
│   ├── case_memory_embed.py
│   ├── vector_store/
│   └── retriever.py
│
├── agent/
│   ├── state.py
│   ├── graph.py
│   ├── nodes/
│   │   ├── trigger.py
│   │   ├── investigate.py
│   │   ├── assess_uncertainty.py
│   │   ├── gather_more_evidence.py
│   │   ├── recommend_action.py
│   │   ├── explain.py
│   │   └── update_memory.py
│   ├── policy_engine.py
│   ├── schemas/                        # pydantic models mirroring SPEC_PROMPTS.md output schemas
│   │   ├── assessment.py
│   │   ├── evidence_request.py
│   │   ├── action_recommendation.py
│   │   └── explanation.py
│   └── prompts/                        # actual prompt template files, spec'd in docs/SPEC_PROMPTS.md
│       ├── assess_prompt.md
│       ├── gather_evidence_prompt.md
│       ├── nba_prompt.md
│       └── explain_prompt.md
│
├── actions/
│   ├── api.py
│   └── mock_responses.py
│
├── ui/
│   └── (Next.js app: pages/components for case timeline,
│       evidence panel, risk gauge, action log, chat)
│
├── evaluation/
│   ├── run_benchmark.py
│   └── output/
│       ├── case_id.json
│       └── ...
│
├── scripts/
│   ├── setup_savanna.sh
│   ├── load_all_data.sh
│   └── seed_case_memory.py
│
└── submission/
    ├── blog_post.md
    ├── demo_video_link.txt
    └── social_post_draft.md

```

## File Naming Conventions

### GSQL Files

- Schema: `create_[entity_type].gsql`
- Loading jobs: `load_[dataset_name].gsql`
- Queries: `[verb]_[noun].gsql` (e.g., `get_txn_neighborhood.gsql`, `find_shared_devices.gsql`)

### Python Modules

- Agent nodes: `[action_name].py` (e.g., `assess_uncertainty.py`, `recommend_action.py`)
- One class/function per file where logical
- Prompts in separate templates directory, not inline in code

### Data Files

- Raw datasets: original filenames preserved in `data/raw/`
- Processed: `[dataset_name]_[transformation].csv` in `data/processed/`
- Output: `case_[case_id].json` in `evaluation/output/`

## Component Boundaries

### Graph Layer (`graph/`)

- **Owns**: TigerGraph schema, GSQL queries, loading jobs, algorithm configs
- **Does not**: Execute agent logic, make LLM calls, handle UI concerns
- **Interface**: GSQL installed queries callable via MCP tools

### MCP Server (`mcp_server/`)

- **Owns**: Tool wrappers with typed input/output schemas, connection to TigerGraph
- **Does not**: Implement graph algorithms, orchestrate investigation flow
- **Interface**: MCP protocol for tool discovery and execution

### RAG Layer (`rag/`)

- **Owns**: Vector store management, policy/typology ingestion, hybrid retrieval
- **Does not**: Execute graph queries directly, make investigation decisions
- **Interface**: Retrieval functions returning structured context

### Agent Layer (`agent/`)

- **Owns**: State machine orchestration, LLM prompts, case state management, policy engine
- **Does not**: Implement GSQL queries, manage vector store, execute real actions
- **Interface**: LangGraph state machine entry points

### Actions Layer (`actions/`)

- **Owns**: Mock action API endpoints with simulated responses
- **Does not**: Make real external calls (card network, banking core, SAR filing)
- **Interface**: FastAPI REST endpoints

### UI Layer (`ui/`)

- **Owns**: Case visualization, live status updates, trigger console
- **Does not**: Contain agent logic, directly query TigerGraph
- **Interface**: REST API + WebSocket for case data

## Key Integration Points

1. **Agent ↔ MCP Server**: Agent calls tools via MCP protocol; MCP server executes GSQL and returns pre-aggregated results
2. **Agent ↔ RAG**: Agent requests context; RAG returns hybrid (graph + vector) retrieval results
3. **Agent ↔ Actions**: Agent calls mock action API; actions return simulated responses
4. **UI ↔ Agent**: UI polls/streams case state; agent pushes state updates
5. **Case Memory ↔ Graph + Vector**: Closed cases written to both graph (edges) and vector store (embeddings)

## Critical Dependencies

- Graph schema must be created before loading jobs run
- GSQL queries must be installed before MCP server starts
- Policy documents must be ingested before agent runs
- Case state object is single source of truth across all nodes
- Case logs are append-only and never mutated in place
