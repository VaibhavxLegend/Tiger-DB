# Demo Video Script 

**Total Runtime:** ~3.5 minutes

## 0:00 - 0:30 | Introduction & Architecture
- **Visual**: Screen sharing the architecture diagram or GitHub Readme.
- **Script**: "Welcome to our TigerGraph Agentic AI Hackathon submission! We built an autonomous fraud investigation system. Instead of LLMs parsing flat transaction records, we use TigerGraph as the reasoning substrate to deterministically spot shared-device fraud rings, then pass those signals to a LangGraph state machine to orchestrate the compliance logic."

## 0:30 - 1:30 | Triggering a Live Case (UI)
- **Visual**: Show the TigerGraph Fraud Investigation Console (the UI we built).
- **Script**: "Here is our analyst console. I'll click 'Trigger New Case' and submit a transaction that fired a high-risk alert. Notice how the agent immediately logs into the `investigate` node via our MCP server, natively querying TigerGraph for N-hop velocity checks."

## 1:30 - 2:30 | Uncertainty Handling & Evidence Loop
- **Visual**: Show the terminal logs or UI logs spinning on the `gather_more_evidence` loop.
- **Script**: "What sets our agent apart is uncertainty handling. If the LLM's confidence drops below our threshold, the LangGraph conditional edge forces it to halt and request external validation—like asking a customer if they made the purchase. It logs exactly why the evidence was insufficient and won't proceed until the request is fulfilled or it maxes out at three iterations."

## 2:30 - 3:00 | Actions, SAR, and Memory Vectorization
- **Visual**: Show the generated JSON final state with recommendations, SAR, and graph updates.
- **Script**: "Once the verdict is locked, the policy engine deterministically assigns approval routes (like L1 or L2 manager approval). If the exposure is high enough, the `explain` node drafts a full Suspicious Activity Report (SAR). Finally, the `update_memory` node embeds the case summary into our vector store and writes a `SIMILAR_TO` edge directly back into TigerGraph."

## 3:00 - 3:30 | The 20 Case Benchmark & Wrap Up
- **Visual**: Open terminal, run `python evaluation/run_benchmark.py`, watch it zip through the 20 test cases.
- **Script**: "We successfully ran all 20 required benchmark cases unattended, producing perfectly formatted JSON bundles for each investigation. We found graph and agent synergies to be incredibly powerful. Thank you."
