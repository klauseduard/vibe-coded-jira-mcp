#!/usr/bin/env python3
"""
A small self-contained JIRA MCP server.
"""
import sys
import logging
import os
from enum import Enum
import typer
from dotenv import load_dotenv
from mcp.server import FastMCP

from src.operations import (
    get_issue,
    search_issues,
    create_issue,
    update_issue,
    clone_issue,
    add_comment,
    get_comments,
    log_work,
    get_projects,
)

# Load environment variables
load_dotenv()

# Set up logging to both stderr and file
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "jira_mcp.log")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("simple_jira")
logger.info(f"Logging initialized, writing to {log_file}")

# Create the Typer app for CLI
app = typer.Typer()

class Transport(str, Enum):
    stdio = "stdio"
    sse = "sse"

@app.command()
def main(
    transport: Transport = typer.Option(Transport.stdio, help="Transport to use"),
    host: str = typer.Option("127.0.0.1", help="Host to listen on"),
    port: int = typer.Option(8000, help="Port to listen on"),
):
    """Run the MCP server."""
    mcp = FastMCP()

    # Add tools
    mcp.add_tool(
        get_issue,
        name="get_issue",
        description="Get a JIRA issue by key"
    )
    mcp.add_tool(
        search_issues,
        name="search_issues",
        description="""Search for JIRA issues using JQL (JIRA Query Language).
        
Required parameters:
- jql: JIRA Query Language string (e.g., "project = EHEALTHDEV AND assignee = currentUser()")

Optional parameters:
- max_results: Number of results to return (default: 50, max: 100)
- start_at: Pagination offset (default: 0)
- fields: List of fields to return (default: ["key", "summary", "status", "assignee", "issuetype", "priority", "created", "updated"])

Example JQL queries:
- "project = EHEALTHDEV AND status = 'In Progress'"
- "assignee = currentUser() ORDER BY created DESC"
- "priority = Major AND created >= startOfDay(-7)"
"""
    )
    mcp.add_tool(
        add_comment,
        name="add_comment",
        description="""Add a comment to a JIRA issue.

Required parameters:
- issue_key: The JIRA issue key (e.g., PROJ-123)
- comment: Comment text to add to the issue

Optional parameters:
- visibility: Visibility settings for the comment (e.g., {'type': 'role', 'value': 'Administrators'})

Example:
{
    "issue_key": "PROJ-123",
    "comment": "This is a comment added via the MCP server",
    "visibility": {
        "type": "group",
        "value": "jira-developers"
    }
}
"""
    )
    mcp.add_tool(
        create_issue,
        name="create_issue",
        description="""Create a new JIRA issue.

Required parameters:
- project_key: The project key (e.g. PROJ)
- summary: Issue summary/title

Optional parameters:
- description: Issue description
- issue_type: Issue type (default: "Task")
- priority: Issue priority
- assignee: Username of the assignee
- labels: List of labels
- custom_fields: Custom field values

Example:
{
    "project_key": "PROJ",
    "summary": "Implement new feature",
    "description": "Add the ability to create issues",
    "issue_type": "Task",
    "priority": "High",
    "assignee": "john.doe",
    "labels": ["feature", "v0.4"]
}
"""
    )
    mcp.add_tool(
        update_issue,
        name="update_issue",
        description="""Update an existing JIRA issue.

Required parameters:
- issue_key: The JIRA issue key (e.g. PROJ-123)

Optional parameters:
- summary: New issue summary/title
- description: New issue description
- priority: New issue priority
- assignee: New assignee username
- labels: New list of labels
- comment: Comment to add to the issue
- custom_fields: Custom field values to update

Example:
{
    "issue_key": "PROJ-123",
    "summary": "Updated feature implementation",
    "description": "Adding more capabilities to issue creation",
    "priority": "High",
    "assignee": "jane.doe",
    "labels": ["feature", "v0.4", "in-progress"],
    "comment": "Updated the implementation plan"
}
"""
    )
    mcp.add_tool(
        get_projects,
        name="get_projects",
        description="""Get list of JIRA projects.

Optional parameters:
- include_archived: Whether to include archived projects (default: False)
- max_results: Maximum number of results to return (default: 50, max: 100)
- start_at: Index of the first result to return (default: 0)

Returns project information including:
- id: Project ID
- key: Project key
- name: Project name
- description: Project description
- lead: Project lead's display name
- url: Project URL
- style: Project style
- archived: Whether the project is archived
- category: Project category name
- simplified: Whether the project is simplified
- project_type_key: Project type key
"""
    )
    mcp.add_tool(
        clone_issue,
        name="clone_issue",
        description="""Clone an existing JIRA issue.

Required parameters:
- source_issue_key: The source JIRA issue key to clone from (e.g., PROJ-123)

Optional parameters:
- project_key: The target project key if different from source
- summary: New summary (defaults to 'Clone of [ORIGINAL-SUMMARY]')
- description: New description (defaults to original description)
- issue_type: Issue type (defaults to original issue type)
- priority: Issue priority (defaults to original priority)
- assignee: Username of the assignee (defaults to original assignee)
- labels: List of labels (defaults to original labels)
- custom_fields: Custom field values to override
- copy_attachments: Whether to copy attachments from the source issue (default: false)
- add_link_to_source: Whether to add a link to the source issue (default: true)

Example:
{
    "source_issue_key": "PROJ-123",
    "project_key": "NEWPROJ",
    "summary": "Cloned issue with modifications",
    "assignee": "jane.doe",
    "copy_attachments": true,
    "custom_fields": {
        "customfield_10001": "High",
        "customfield_10002": "Backend"
    }
}
"""
    )
    mcp.add_tool(
        log_work,
        name="log_work",
        description="""Log work time on a JIRA issue.

Required parameters:
- issue_key: The JIRA issue key (e.g., PROJ-123)
- time_spent: Time spent in JIRA format (e.g., '2h 30m', '1d', '30m')

Optional parameters:
- comment: Comment for the work log
- started_at: When the work was started (defaults to now)

Example:
{
    "issue_key": "EHEALTHDEV-123",
    "time_spent": "2h 30m",
    "comment": "Implemented feature X",
    "started_at": "2024-03-08T10:00:00"
}
"""
    )
    mcp.add_tool(
        get_comments,
        name="get_comments",
        description="""Get comments for a JIRA issue.

Required parameters:
- issue_key: The JIRA issue key (e.g., PROJ-123)

Optional parameters:
- max_results: Maximum number of comments to return (default: 50, max: 100)
- start_at: Index of the first comment to return (default: 0)

Example:
{
    "issue_key": "PROJ-123",
    "max_results": 20,
    "start_at": 0
}

Returns:
- issue_key: The issue key
- total: Total number of comments for the issue
- start_at: Index of the first comment returned
- max_results: Maximum number of comments returned
- comments: Array of comment objects with:
  - id: Comment ID
  - author: Display name of the comment author
  - body: Text content of the comment
  - created: Creation timestamp
  - updated: Last update timestamp (if available)
  - visibility: Visibility restrictions (if any)
"""
    )

    # Run server
    if transport == Transport.stdio:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host=host, port=port)

if __name__ == "__main__":
    app() 
