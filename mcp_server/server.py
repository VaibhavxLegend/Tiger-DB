"""
MCP Server for TigerGraph fraud investigation tools
Phase 2: Mock implementation for hackathon speed

This implementation uses mock graph data for rapid prototyping.
Can be swapped for real GSQL queries post-hackathon.
"""

import json
import sys
from typing import Any, Dict
from mcp_server.tool_definitions import (
    TOOL_DEFINITIONS,
    TxnNeighborhoodInput,
    SharedDevicesInput,
    SharedCardsInput,
    VelocityCheckInput,
    SimilarCasesInput
)
from mcp_server.mock_graph_data import (
    generate_transaction_neighborhood,
    generate_shared_devices,
    generate_velocity_check,
    generate_similar_past_cases,
    generate_linked_cards
)

class MockMCPServer:
    """
    Mock MCP server for TigerGraph fraud investigation tools
    
    Returns realistic graph data without requiring full data load.
    Architecture is identical to real MCP server.
    """
    
    def __init__(self):
        self.tools = TOOL_DEFINITIONS
        self.call_count = 0
    
    def list_tools(self) -> list:
        """List all available tools"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"].schema(),
            }
            for tool in self.tools.values()
        ]
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given arguments
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments as dict
            
        Returns:
            Tool execution result
        """
        self.call_count += 1
        
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        tool_def = self.tools[tool_name]
        
        # Validate inputs
        try:
            input_schema = tool_def["input_schema"]
            validated_input = input_schema(**arguments)
        except Exception as e:
            return {"error": f"Invalid input: {str(e)}"}
        
        # Route to appropriate handler
        try:
            if tool_name == "get_txn_neighborhood":
                result = self._handle_txn_neighborhood(validated_input)
            elif tool_name == "find_shared_devices":
                result = self._handle_shared_devices(validated_input)
            elif tool_name == "find_shared_cards":
                result = self._handle_shared_cards(validated_input)
            elif tool_name == "velocity_check":
                result = self._handle_velocity_check(validated_input)
            elif tool_name == "get_similar_past_cases":
                result = self._handle_similar_cases(validated_input)
            else:
                return {"error": f"Tool not implemented: {tool_name}"}
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def _handle_txn_neighborhood(self, input_data: TxnNeighborhoodInput) -> Dict[str, Any]:
        """Handle transaction neighborhood query"""
        
        # Determine scenario based on transaction/card ID patterns
        # For demo, use simple heuristics
        scenario = self._infer_scenario(input_data.card_id)  # consistent with device/velocity
        
        result = generate_transaction_neighborhood(
            txn_id=input_data.transaction_id,
            card_id=input_data.card_id,
            customer_id=input_data.customer_id,
            scenario=scenario
        )
        
        return result
    
    def _handle_shared_devices(self, input_data: SharedDevicesInput) -> Dict[str, Any]:
        """Handle shared device query"""
        scenario = self._infer_scenario(input_data.card_id)
        
        result = generate_shared_devices(
            card_id=input_data.card_id,
            scenario="fraud_ring" if scenario == "suspicious" else "normal"
        )
        
        return result
    
    def _handle_shared_cards(self, input_data: SharedCardsInput) -> Dict[str, Any]:
        """Handle linked cards query"""
        scenario = self._infer_scenario(input_data.card_id)
        
        result = generate_linked_cards(
            card_id=input_data.card_id,
            scenario="fraud_ring" if scenario == "suspicious" else "normal"
        )
        
        return result
    
    def _handle_velocity_check(self, input_data: VelocityCheckInput) -> Dict[str, Any]:
        """Handle velocity check query"""
        scenario = self._infer_scenario(input_data.card_id)
        
        result = generate_velocity_check(
            card_id=input_data.card_id,
            scenario="testing" if scenario == "suspicious" else "normal"
        )
        
        return result
    
    def _handle_similar_cases(self, input_data: SimilarCasesInput) -> Dict[str, Any]:
        """Handle similar cases query"""
        
        result = generate_similar_past_cases(
            pattern=input_data.pattern,
            device_id=input_data.device_id,
            card_id=input_data.card_id
        )
        
        return {
            "cases": result,
            "query_metadata": {
                "total_cases_examined": 5565,
                "cases_returned": len(result),
                "execution_time_ms": 85
            }
        }
    
    def _infer_scenario(self, identifier: str) -> str:
        """Deterministic scenario from identifier hash — gives varied, reproducible results."""
        digits = ''.join(c for c in identifier if c.isdigit())
        seed = int(digits) % 97 if digits else hash(identifier) & 0xFF
        if seed % 5 == 0:          # 20% legitimate
            return "legitimate"
        elif seed % 5 <= 1:        # 20% uncertain
            return "uncertain"
        else:                      # 60% suspicious
            return "suspicious"

# Singleton instance
_server_instance = None

def get_server() -> MockMCPServer:
    """Get or create server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = MockMCPServer()
    return _server_instance

# For testing
if __name__ == "__main__":
    print("MCP Server for TigerGraph Fraud Investigation")
    print("=" * 60)
    
    server = get_server()
    
    # List tools
    print("\nAvailable Tools:")
    for tool in server.list_tools():
        print(f"  - {tool['name']}: {tool['description'][:80]}...")
    
    # Test a tool call
    print("\n" + "=" * 60)
    print("Testing get_txn_neighborhood tool...")
    print("=" * 60)
    
    result = server.call_tool("get_txn_neighborhood", {
        "transaction_id": "3478782",
        "card_id": "C11891-K1",
        "customer_id": "C11891",
        "hops": 2
    })
    
    if result.get("success"):
        print("\n✓ Tool executed successfully")
        print("\nSample result:")
        print(json.dumps(result["result"]["transaction"], indent=2))
        print(f"\nRisk signals: {result['result']['risk_signals']}")
        print(f"Recent transactions: {len(result['result']['recent_transactions'])}")
    else:
        print(f"\n✗ Tool failed: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("MCP Server ready for agent integration")
    print("=" * 60)
