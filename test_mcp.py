#!/usr/bin/env python3
"""
Simple test script to verify MCP server functionality
"""
import asyncio
import sys
from mcp.client.stdio import stdio_client

async def test_server():
    """Test the MCP server by listing tools"""
    from mcp.client.stdio import StdioServerParameters

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["simple_jira.py", "--transport", "stdio"]
    )

    try:
        async with stdio_client(server_params) as streams:
            read, write = streams

            # Initialize the client
            from mcp.client.session import ClientSession
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List available tools
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")

                return True

    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)