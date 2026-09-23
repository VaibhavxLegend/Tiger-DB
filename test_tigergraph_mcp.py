"""
Simple test script for TigerGraph-MCP integration
This demonstrates basic tool usage without requiring a full agent setup
"""

import asyncio
from pathlib import Path
from dotenv import dotenv_values
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables
env_dict = dotenv_values(dotenv_path=Path(".env").expanduser().resolve())

# Configure MCP client
client = MultiServerMCPClient(
    {
        "tigergraph-mcp-server": {
            "transport": "stdio",
            "command": "tigergraph-mcp",
            "args": ["-vv"],  # verbose logging
            "env": env_dict,
        },
    }
)


async def test_connection():
    """Test basic TigerGraph-MCP connection and list available graphs"""
    print("=" * 60)
    print("Testing TigerGraph-MCP Connection")
    print("=" * 60)
    
    # Use a session to reuse the connection across multiple tool calls
    async with client.session("tigergraph-mcp-server") as session:
        try:
            # Test 1: List available graphs
            print("\n1. Listing available graphs...")
            result = await session.call_tool("tigergraph__list_graphs", {})
            print(f"   Result: {result}")
            
            # Test 2: List all available tools
            print("\n2. Discovering available tools...")
            tools_response = await session.list_tools()
            print(f"   Found {len(tools_response.tools)} tools")
            
            # Show first 10 tools as examples
            print("\n   Sample tools (first 10):")
            for i, tool in enumerate(tools_response.tools[:10], 1):
                print(f"   {i}. {tool.name}")
            
            # Test 3: List connection profiles
            print("\n3. Checking connection profiles...")
            result = await session.call_tool("tigergraph__list_connections", {})
            print(f"   Connections: {result}")
            
            print("\n" + "=" * 60)
            print("✓ Connection test successful!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ Error during test: {str(e)}")
            print("\nPlease check your .env file configuration:")
            print("  - TG_HOST: TigerGraph server URL")
            print("  - TG_USERNAME and TG_PASSWORD: Credentials")
            print("  - TG_GRAPHNAME: Graph name (optional)")
            raise


async def show_available_tools():
    """Show all available TigerGraph-MCP tools organized by category"""
    print("\n" + "=" * 60)
    print("Available TigerGraph-MCP Tools")
    print("=" * 60)
    
    async with client.session("tigergraph-mcp-server") as session:
        tools_response = await session.list_tools()
        
        # Organize tools by prefix/category
        categories = {}
        for tool in tools_response.tools:
            # Extract category from tool name
            parts = tool.name.split("__")
            if len(parts) > 1:
                category = parts[1].split("_")[0]  # First word after prefix
            else:
                category = "other"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(tool.name)
        
        # Print organized tools
        for category, tools in sorted(categories.items()):
            print(f"\n{category.upper()} ({len(tools)} tools):")
            for tool in sorted(tools):
                print(f"  • {tool}")
        
        print(f"\n{'=' * 60}")
        print(f"Total: {len(tools_response.tools)} tools available")
        print(f"{'=' * 60}\n")


async def main():
    """Run all tests"""
    try:
        # First, show all available tools
        await show_available_tools()
        
        # Then test the connection
        await test_connection()
        
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Update .env with your actual TigerGraph credentials")
        print("2. Create a graph schema using tigergraph__create_graph")
        print("3. Load data using tigergraph__insert_vertices and tigergraph__insert_edges")
        print("4. Query data using tigergraph__run_query or tigergraph__gsql")
        print("5. Integrate with LangGraph agent for agentic workflows")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        print("Please ensure TigerGraph is running and .env is configured correctly.")


if __name__ == "__main__":
    asyncio.run(main())
