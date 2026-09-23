# Building an Agentic Fraud Investigation System with TigerGraph

*[Draft - To be completed in Phase 6]*

## Overview

[Introduction: what we built, why graph + agent is powerful for fraud investigation]

## Architecture

### Why TigerGraph as the Reasoning Substrate

[How TigerGraph performs deterministic pattern detection, not the LLM]

### The Investigation Workflow

[Walk through the LangGraph state machine: trigger → investigate → assess → (evidence loop) → action → explain → memory]

### Graph Schema Design

[Entities, relationships, why they matter for fraud detection]

### Hybrid Retrieval: GraphRAG + Case Memory

[How we combine graph traversal with vector similarity]

## Key Technical Decisions

### Graph-Native Pattern Detection

[GSQL queries + graph algorithms for ring detection, velocity checks]

### Uncertainty Handling

[How we explicitly model "insufficient evidence" and request more]

### Policy Compliance

[Deterministic policy engine, approval routing, two log points]

### Explainability

[Evidence citation, immutable audit logs, SAR generation]

## Implementation Highlights

### Phase 1: Graph Foundation

[Data preprocessing, schema creation, loading 590k transactions]

### Phase 2: GSQL Tools + MCP

[Building typed tools wrapping GSQL queries]

### Phase 3: Agent State Machine

[LangGraph implementation, prompt engineering, case memory]

### Phase 4: Benchmark Results

[Running 20 cases, patterns identified, actions recommended]

## What We Learned

### Graph + LLM Synergy

[Where graph excels (relationships, patterns), where LLM excels (synthesis, uncertainty)]

### Real-World Challenges

[No ground truth labels, simulating evidence responses, bounded iteration loops]

### Production Considerations

[What would change for real deployment: real action APIs, streaming ingestion, scale]

## What We'd Improve With More Time

- [List improvements]
- [Additional features]
- [Performance optimizations]

## Demo

[Link to demo video]

## Code

[Link to GitHub repository]

---

**Tags**: #TigerGraph #GraphRAG #FraudDetection #LangGraph #AgenticAI
