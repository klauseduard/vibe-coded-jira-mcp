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
from fastmcp import FastMCP

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

# Set up logging to stderr only (MCP best practice)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("simple_jira")

# Create the FastMCP server with modern pattern
mcp = FastMCP("jira-server")

# Create the Typer app for CLI
app = typer.Typer()

class Transport(str, Enum):
    stdio = "stdio"
    sse = "sse"

# Register tools using modern decorator pattern
@mcp.tool()
def get_issue_tool(issue_key: str) -> dict:
    """Get a JIRA issue by key."""
    return get_issue(issue_key)

@mcp.tool()
def search_issues_tool(
    jql: str = "",
    max_results: int = 50,
    start_at: int = 0,
    fields: str = "key,summary,status,assignee,issuetype,priority,created,updated"
) -> dict:
    """Search for JIRA issues using JQL (JIRA Query Language).

    Args:
        jql: JIRA Query Language string (e.g., "project = PROJ AND assignee = currentUser()")
        max_results: Number of results to return (default: 50, max: 100)
        start_at: Pagination offset (default: 0)
        fields: Comma-separated list of fields to return

    Example JQL queries:
    - "project = PROJ AND status = 'In Progress'"
    - "assignee = currentUser() ORDER BY created DESC"
    - "priority = Major AND created >= startOfDay(-7)"
    """
    return search_issues(jql, max_results, start_at, fields)

@mcp.tool()
def create_issue_tool(
    project_key: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    priority: str = "",
    assignee: str = "",
    labels: list = None,
    custom_fields: dict = None
) -> dict:
    """Create a new JIRA issue.

    Args:
        project_key: The project key (e.g. PROJ)
        summary: Issue summary/title
        description: Issue description
        issue_type: Issue type (default: "Task")
        priority: Issue priority
        assignee: Username of the assignee
        labels: List of labels
        custom_fields: Custom field values
    """
    return create_issue(project_key, summary, description, issue_type, priority, assignee, labels or [], custom_fields or {})

@mcp.tool()
def update_issue_tool(
    issue_key: str,
    summary: str = "",
    description: str = "",
    priority: str = "",
    assignee: str = "",
    labels: list = None,
    comment: str = "",
    custom_fields: dict = None
) -> dict:
    """Update an existing JIRA issue.

    Args:
        issue_key: The JIRA issue key (e.g. PROJ-123)
        summary: New issue summary/title
        description: New issue description
        priority: New issue priority
        assignee: New assignee username
        labels: New list of labels
        comment: Comment to add to the issue
        custom_fields: Custom field values to update
    """
    return update_issue(issue_key, summary, description, priority, assignee, labels or [], comment, custom_fields or {})

@mcp.tool()
def clone_issue_tool(
    source_issue_key: str,
    project_key: str = "",
    summary: str = "",
    description: str = "",
    issue_type: str = "",
    priority: str = "",
    assignee: str = "",
    labels: list = None,
    custom_fields: dict = None,
    copy_attachments: bool = False,
    add_link_to_source: bool = True
) -> dict:
    """Clone an existing JIRA issue.

    Args:
        source_issue_key: The source JIRA issue key to clone from (e.g., PROJ-123)
        project_key: The target project key if different from source
        summary: New summary (defaults to 'Clone of [ORIGINAL-SUMMARY]')
        description: New description (defaults to original description)
        issue_type: Issue type (defaults to original issue type)
        priority: Issue priority (defaults to original priority)
        assignee: Username of the assignee (defaults to original assignee)
        labels: List of labels (defaults to original labels)
        custom_fields: Custom field values to override
        copy_attachments: Whether to copy attachments from the source issue
        add_link_to_source: Whether to add a link to the source issue
    """
    return clone_issue(source_issue_key, project_key, summary, description, issue_type, priority, assignee, labels or [], custom_fields or {}, copy_attachments, add_link_to_source)

@mcp.tool()
def add_comment_tool(issue_key: str, comment: str, visibility: dict = None) -> dict:
    """Add a comment to a JIRA issue.

    Args:
        issue_key: The JIRA issue key (e.g., PROJ-123)
        comment: Comment text to add to the issue
        visibility: Visibility settings for the comment (e.g., {'type': 'role', 'value': 'Administrators'})
    """
    return add_comment(issue_key, comment, visibility or {})

@mcp.tool()
def get_comments_tool(issue_key: str, max_results: int = 50, start_at: int = 0) -> dict:
    """Get comments for a JIRA issue.

    Args:
        issue_key: The JIRA issue key (e.g., PROJ-123)
        max_results: Maximum number of comments to return (default: 50, max: 100)
        start_at: Index of the first comment to return (default: 0)
    """
    return get_comments(issue_key, max_results, start_at)

@mcp.tool()
def log_work_tool(issue_key: str, time_spent: str, comment: str = "", started_at: str = "") -> dict:
    """Log work time on a JIRA issue.

    Args:
        issue_key: The JIRA issue key (e.g., PROJ-123)
        time_spent: Time spent in JIRA format (e.g., '2h 30m', '1d', '30m')
        comment: Comment for the work log
        started_at: When the work was started (defaults to now)
    """
    return log_work(issue_key, time_spent, comment, started_at)

@mcp.tool()
def get_projects_tool(include_archived: bool = False, max_results: int = 50, start_at: int = 0) -> dict:
    """Get list of JIRA projects.

    Args:
        include_archived: Whether to include archived projects (default: False)
        max_results: Maximum number of results to return (default: 50, max: 100)
        start_at: Index of the first result to return (default: 0)
    """
    return get_projects(include_archived, max_results, start_at)

@app.command()
def main(
    transport: Transport = typer.Option(Transport.stdio, help="Transport to use"),
    host: str = typer.Option("127.0.0.1", help="Host to listen on"),
    port: int = typer.Option(8000, help="Port to listen on"),
):
    """Run the MCP server."""
    # Run server
    if transport == Transport.stdio:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host=host, port=port)

if __name__ == "__main__":
    app() 
