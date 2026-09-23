# System Architecture Diagram

```mermaid
graph TD
    %% Core Components
    subgraph UI["User Interface"]
        UI_Dashboard[Dashboard: http://localhost:8080]
        UI_Case_Browser[Case Browser & Trigger]
    end

    subgraph Agent["Agent Orchestration (LangGraph)"]
        Trigger[trigger_node] --> Investigate[investigate_node]
        Investigate --> Assess[assess_uncertainty_node]
        Assess -->|uncertain & iter<3| Gather[gather_more_evidence_node]
        Gather --> Assess
        Assess -->|sufficient| Recommend[recommend_action_node]
        Recommend --> Explain[explain_node]
        Explain --> Update[update_memory_node]
        Update --> End[end]
    end

    subgraph Memory["Case Memory & RAG"]
        RAG[rag/retriever.py]
        Similar[Similar Case Retrieval]
        Policy[Policy Context Retrieval]
        Embed[case_memory_embed.py]
    end

    subgraph Graph["Graph Layer (MCP Server)"]
        MCP[mcp_server/server.py]
        TxN[get_txn_neighborhood]
        Dev[find_shared_devices]
        Vel[velocity_check]
        Sim[get_similar_past_cases]
    end

    subgraph Actions["Action Layer"]
        Policy_Engine[agent/policy_engine.py]
        Executor[actions/executor.py]
        Mock[actions/mock_responses.py]
    end

    %% Data Stores
    TigerGraph[TigerGraph Database]
    VectorDB[Vector Store]
    Case_Storage[(cases/ JSON outputs)]

    %% Connections
    UI_Dashboard -->|HTTP| Trigger
    UI_Case_Browser -->|HTTP| Trigger

    Trigger -->|Case ID| Investigate
    Investigate -->|Tool Calls| MCP

    MCP --> TxN
    MCP --> Dev
    MCP --> Vel
    MCP --> Sim

    TxN --> TigerGraph
    Dev --> TigerGraph
    Vel --> TigerGraph
    Sim --> TigerGraph

    Sim --> Similar
    Similar --> VectorDB
    Policy --> VectorDB

    Assess -->|Entities, Pattern| RAG
    RAG --> Similar
    RAG --> Policy

    Recommend --> Policy_Engine
    Policy_Engine --> Executor
    Executor --> Mock

    Explain --> Case_Storage
    Update --> TigerGraph

    %% Styling
    classDef component fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef database fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
    classDef ui fill:#fff3e0,stroke:#ef6c00,stroke-width:1px;
    classDef agent fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;
    classDef memory fill:#f3e5f5,stroke:#6a1b9a,stroke-width:1px;
    classDef graphA fill:#e0f7fa,stroke:#006064,stroke-width:1px;
    classDef actions fill:#ffebee,stroke:#c62828,stroke-width:1px;

    class UI_Dashboard,UI_Case_Browser ui;
    class Trigger,Investigate,Assess,Gather,Recommend,Explain,Update component;
    class RAG,Similar,Policy,Embed memory;
    class MCP,TxN,Dev,Vel,Sim graphA;
    class Policy_Engine,Executor,Mock actions;
    class TigerGraph,VectorDB database;
```

## Component Descriptions

### User Interface

- **Dashboard**: Main investigation console showing case status, evidence, and recommendations
- **Case Browser**: Browse historical cases and trigger new investigations

### Agent Orchestration (LangGraph)

- **trigger_node**: Opens case from case_pack.csv or UI
- **investigate_node**: Calls MCP tools to gather evidence
- **assess_uncertainty_node**: Rule-based fraud assessment (pattern, probability, confidence)
- **gather_more_evidence_node**: Requests additional evidence when uncertain
- **recommend_action_node**: Recommends policy-compliant actions
- **explain_node**: Generates human-readable explanations and SAR narratives
- **update_memory_node**: Archives case to graph for future similarity

### Case Memory & RAG

- **Similar Case Retrieval**: Finds historically similar cases for context
- **Policy Context Retrieval**: Retrieves relevant fraud policies
- **Vector Store**: Stores case embeddings for similarity search

### Graph Layer (MCP Server)

- **get_txn_neighborhood**: Transaction details, risk signals, channel info
- **find_shared_devices**: Device clustering and fraud ring detection
- **velocity_check**: Transaction velocity and pattern analysis
- **get_similar_past_cases**: Case memory retrieval

### Action Layer

- **Policy Engine**: Routes actions based on risk level (auto/L1/L2 approval)
- **Executor**: Mock execution of fraud actions (block card, create case, etc.)

### Data Stores

- **TigerGraph**: Primary graph database for relationships and traversals
- **Vector Store**: Embedding store for case similarity search
- **Case Storage**: JSON output files for benchmark results

## Data Flow

1. **Trigger**: Case initiated via UI or benchmark script
2. **Investigate**:
   - MCP tools query TigerGraph for evidence
   - Evidence stored in CaseState
3. **Assess**:
   - Rule-based analysis of evidence
   - Pattern detection and probability calculation
   - If uncertain and iterations < 3 → gather more evidence
4. **Recommend**: Policy-compliant action recommendation
5. **Explain**: Generate narratives and justifications
6. **Update**: Archive case to TigerGraph for future reference

## Key Interfaces

### MCP Server Interface

```python
# Available tools via mcp_server/server.py
- get_txn_neighborhood(txn_id, card_id, customer_id)
- find_shared_devices(card_id, time_window_hours)
- velocity_check(card_id, time_window_minutes)
- get_similar_past_cases(pattern, device_id, card_id)
```

### State Interface

```python
# agent/state.py CaseState contains:
- case_metadata (case_id, card_id, customer_id, etc.)
- investigation_state (status, verdict, probabilities)
- evidence (List[Evidence])
- actions (List[Action])
- explanations (summary, SAR, etc.)
- control_flow (iteration_count, sufficient_evidence)
```

### Action Interface

```python
# actions/executor.py executes:
- BLOCK_CARD
- CREATE_CASE
- FILE_SAR
- VERIFY_WITH_CUSTOMER
- STEP_UP_AUTH
- ESCALATE_TO_ANALYST
- MONITOR_CARD
- CLOSE_NO_FRAUD
```
