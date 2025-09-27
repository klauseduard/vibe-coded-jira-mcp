#!/usr/bin/env python3
"""
Test JIRA MCP server with actual operations
"""
import asyncio
import sys
import json
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def test_jira_operations():
    """Test JIRA operations through MCP"""
    import os
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["simple_jira.py", "--transport", "stdio"],
        env=os.environ.copy()  # Pass current environment to subprocess
    )

    try:
        async with stdio_client(server_params) as streams:
            read, write = streams
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ MCP Server initialized\n")

                # Test 1: Get projects
                print("📋 Testing get_projects_tool...")
                try:
                    result = await session.call_tool(
                        "get_projects_tool",
                        arguments={"max_results": 5}
                    )
                    print(f"   Raw result: {result}")
                    if result.content and result.content[0].text:
                        projects = json.loads(result.content[0].text)
                    else:
                        projects = {"error": "Empty response from server"}

                    if "error" in projects:
                        print(f"❌ Error getting projects: {projects['error']}")
                    elif "projects" in projects:
                        print(f"✅ Found {len(projects['projects'])} projects:")
                        for proj in projects['projects'][:3]:  # Show first 3
                            print(f"   - {proj.get('key', 'N/A')}: {proj.get('name', 'N/A')}")
                    else:
                        print(f"⚠️ Unexpected response: {projects}")
                except Exception as e:
                    print(f"❌ Failed to get projects: {e}")

                print()

                # Test 2: Search for recent issues
                print("🔍 Testing search_issues_tool...")
                try:
                    result = await session.call_tool(
                        "search_issues_tool",
                        arguments={
                            "jql": "created >= -7d ORDER BY created DESC",
                            "max_results": 3
                        }
                    )
                    issues = json.loads(result.content[0].text) if result.content else {}

                    if "error" in issues:
                        print(f"❌ Error searching issues: {issues['error']}")
                    elif "issues" in issues:
                        print(f"✅ Found {issues.get('total', 0)} total issues, showing {len(issues['issues'])}:")
                        for issue in issues['issues']:
                            print(f"   - {issue.get('key', 'N/A')}: {issue.get('fields', {}).get('summary', 'N/A')}")
                    else:
                        print(f"⚠️ Unexpected response: {issues}")
                except Exception as e:
                    print(f"❌ Failed to search issues: {e}")

                print()

                # Test 3: Get a specific issue (hardcoded for testing)
                print("📄 Testing get_issue_tool...")
                # Skip interactive input for now
                issue_key = None  # You can hardcode an issue key here if you know one

                if issue_key:
                    try:
                        result = await session.call_tool(
                            "get_issue_tool",
                            arguments={"issue_key": issue_key}
                        )
                        issue = json.loads(result.content[0].text) if result.content else {}

                        if "error" in issue:
                            print(f"❌ Error getting issue: {issue['error']}")
                        elif "key" in issue:
                            print(f"✅ Retrieved issue {issue['key']}:")
                            fields = issue.get('fields', {})
                            print(f"   Summary: {fields.get('summary', 'N/A')}")
                            print(f"   Status: {fields.get('status', {}).get('name', 'N/A')}")
                            print(f"   Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}")
                        else:
                            print(f"⚠️ Unexpected response: {issue}")
                    except Exception as e:
                        print(f"❌ Failed to get issue: {e}")
                else:
                    print("   Skipped")

                return True

    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing JIRA MCP Server Operations\n")
    print("=" * 50)
    success = asyncio.run(test_jira_operations())
    print("=" * 50)
    print("\n✅ All tests completed!" if success else "\n❌ Tests failed!")
    sys.exit(0 if success else 1)