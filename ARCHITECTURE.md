# System Architecture Diagram

```mermaid
graph TD

    %% =========================================================
    %% USER INTERFACE
    %% =========================================================
    subgraph UI["🖥️ USER INTERFACE"]
        direction TB
        UI_Dashboard["📊 Dashboard<br/><small>localhost:8080</small>"]
        UI_Case_Browser["🔎 Case Browser<br/>& Trigger"]
    end


    %% =========================================================
    %% AGENT ORCHESTRATION
    %% =========================================================
    subgraph Agent["🤖 AGENT ORCHESTRATION · LANGGRAPH"]
        direction LR

        Trigger(["⚡ trigger_node"])
        Investigate(["🔍 investigate_node"])
        Assess{"❓ assess_uncertainty_node"}
        Gather(["📚 gather_more_evidence_node"])
        Recommend(["🎯 recommend_action_node"])
        Explain(["💡 explain_node"])
        Update(["🧠 update_memory_node"])
        End(["✓ END"])

        Trigger --> Investigate
        Investigate --> Assess

        Assess -->|"Uncertain<br/>& iter < 3"| Gather
        Gather --> Assess

        Assess -->|"Sufficient"| Recommend
        Recommend --> Explain
        Explain --> Update
        Update --> End
    end


    %% =========================================================
    %% MEMORY & RAG
    %% =========================================================
    subgraph Memory["🧠 CASE MEMORY & RAG"]
        direction TB

        RAG["🔗 RAG Retriever<br/><small>rag/retriever.py</small>"]
        Similar["🔎 Similar Case<br/>Retrieval"]
        Policy["📜 Policy Context<br/>Retrieval"]
        Embed["🧬 Case Memory<br/>Embeddings"]
    end


    %% =========================================================
    %% GRAPH / MCP
    %% =========================================================
    subgraph Graph["🕸️ GRAPH INTELLIGENCE · MCP SERVER"]
        direction TB

        MCP["🔌 MCP Server<br/><small>mcp_server/server.py</small>"]

        TxN["🧩 Transaction<br/>Neighborhood"]
        Dev["🔗 Shared Device<br/>Detection"]
        Vel["⚡ Velocity<br/>Check"]
        Sim["🔎 Similar Past<br/>Cases"]

        MCP --> TxN
        MCP --> Dev
        MCP --> Vel
        MCP --> Sim
    end


    %% =========================================================
    %% ACTION LAYER
    %% =========================================================
    subgraph Actions["⚙️ ACTION & DECISION LAYER"]
        direction TB

        Policy_Engine["🛡️ Policy Engine<br/><small>agent/policy_engine.py</small>"]
        Executor["🚀 Action Executor<br/><small>actions/executor.py</small>"]
        Mock["🧪 Mock Responses<br/><small>actions/mock_responses.py</small>"]

        Policy_Engine --> Executor
        Executor --> Mock
    end


    %% =========================================================
    %% DATA STORES
    %% =========================================================
    TigerGraph[("🗄️ TigerGraph<br/>Database")]
    VectorDB[("🔮 Vector Store")]
    Case_Storage[("📁 Case Storage<br/>JSON Outputs")]


    %% =========================================================
    %% UI → AGENT
    %% =========================================================
    UI_Dashboard -->|"HTTP"| Trigger
    UI_Case_Browser -->|"HTTP"| Trigger


    %% =========================================================
    %% AGENT → GRAPH
    %% =========================================================
    Investigate -->|"Tool Calls"| MCP

    TxN --> TigerGraph
    Dev --> TigerGraph
    Vel --> TigerGraph
    Sim --> TigerGraph


    %% =========================================================
    %% GRAPH → MEMORY
    %% =========================================================
    Sim --> Similar
    Similar --> VectorDB
    Policy --> VectorDB
    Embed --> VectorDB


    %% =========================================================
    %% AGENT → RAG
    %% =========================================================
    Assess -->|"Entities + Pattern"| RAG
    RAG --> Similar
    RAG --> Policy


    %% =========================================================
    %% DECISION → ACTION
    %% =========================================================
    Recommend --> Policy_Engine


    %% =========================================================
    %% EXPLANATION / MEMORY
    %% =========================================================
    Explain --> Case_Storage
    Update -->|"Persist Case Knowledge"| TigerGraph


    %% =========================================================
    %% STYLING
    %% =========================================================

    %% UI
    classDef ui fill:#E8F1FF,stroke:#2563EB,color:#172554,stroke-width:2px;

    %% Agent
    classDef agent fill:#EAF8F0,stroke:#16A34A,color:#14532D,stroke-width:2px;

    %% Decision
    classDef decision fill:#FFF7D6,stroke:#D97706,color:#78350F,stroke-width:2px;

    %% Memory
    classDef memory fill:#F3E8FF,stroke:#9333EA,color:#581C87,stroke-width:2px;

    %% Graph
    classDef Graph fill:#E6FFFB,stroke:#0891B2,color:#164E63,stroke-width:2px;

    %% Actions
    classDef action fill:#FFF0F0,stroke:#DC2626,color:#7F1D1D,stroke-width:2px;

    %% Database
    classDef database fill:#EEF2F7,stroke:#475569,color:#0F172A,stroke-width:2px;

    %% End
    classDef endA fill:#DCFCE7,stroke:#15803D,color:#14532D,stroke-width:2px;

    %% Apply classes
    class UI_Dashboard,UI_Case_Browser ui;

    class Trigger,Investigate,Gather,Recommend,Explain,Update agent;
    class Assess decision;
    class End endA;

    class RAG,Similar,Policy,Embed memory;

    class MCP,TxN,Dev,Vel,Sim Graph;

    class Policy_Engine,Executor,Mock action;

    class TigerGraph,VectorDB,Case_Storage database;


    %% =========================================================
    %% SUBGRAPH STYLING
    %% =========================================================

    style UI fill:#F8FBFF,stroke:#2563EB,stroke-width:2px
    style Agent fill:#F7FCF8,stroke:#16A34A,stroke-width:2px
    style Memory fill:#FCF8FF,stroke:#9333EA,stroke-width:2px
    style Graph fill:#F4FEFF,stroke:#0891B2,stroke-width:2px
    style Actions fill:#FFF8F8,stroke:#DC2626,stroke-width:2px
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
