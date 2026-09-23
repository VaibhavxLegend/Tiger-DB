# Product Overview

## What We're Building

An agentic fraud investigation system that autonomously investigates flagged transactions using TigerGraph as the primary reasoning substrate. The agent gathers evidence from graph relationships, assesses risk and confidence, requests additional evidence when uncertain, and recommends actions within defined policy constraints.

## Core Capabilities

- **Autonomous Investigation**: Agent-driven evidence gathering using graph traversal and algorithms
- **Uncertainty Handling**: Explicitly represents "insufficient evidence" as a state, not a forced guess
- **Next-Best-Action**: Recommends/executes actions (block, monitor, escalate) within policy constraints
- **Case Memory**: Hybrid graph+vector storage of closed cases for retrieval in future investigations
- **Explainability**: Every decision cites the graph evidence and policy used

## Target Users

- **Fraud Analysts**: Pre-investigated cases with clear evidence and recommended actions
- **Fraud Ops Leads**: Aggregate patterns, case throughput, and approval/autonomous action routing
- **Hackathon Judges**: Full trigger→investigation→action→explanation loop on 20 benchmark cases

## Key Principles

- **Graph-native reasoning**: TigerGraph performs relationship and pattern detection via GSQL + algorithms, not the LLM
- **LLM for synthesis only**: Used for uncertainty judgment, action selection, and natural-language explanation
- **Explainability over accuracy**: Every decision must cite the graph/RAG evidence used
- **Auditability**: Case logs are append-only and immutable

## Success Criteria

- Correct pattern identification with well-cited evidence (25%)
- Policy-compliant next-best-actions that handle uncertainty properly (25%)
- Clear, evidence-grounded case narratives (10%)
- Clean agentic design with real tool use and memory (15%)
- Innovation in hybrid graph+vector case memory and GraphRAG (15%)
- Quality end-to-end demo (10%)
