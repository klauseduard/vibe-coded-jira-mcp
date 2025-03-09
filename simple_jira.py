#!/usr/bin/env python3
"""
A minimal, self-contained JIRA MCP server that just returns TODO responses.
"""
import sys
import logging
import json
from typing import Dict, Any, Optional, List
from enum import Enum
import os
import typer
from jira import JIRA
from mcp.server import FastMCP
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging to stderr
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("simple_jira")

# Create the Typer app for CLI
app = typer.Typer()

class Transport(str, Enum):
    stdio = "stdio"
    sse = "sse"

class JiraConfig(BaseModel):
    """JIRA configuration settings."""
    jira_url: str = Field(default=os.getenv("JIRA_URL", ""))
    jira_username: str = Field(default=os.getenv("JIRA_USERNAME", ""))
    jira_api_token: str = Field(default=os.getenv("JIRA_API_TOKEN", ""))

class GetIssueArgs(BaseModel):
    """Arguments for the get_issue tool."""
    issue_key: str = Field(default="PROJ-123", description="The JIRA issue key (e.g. PROJ-123)")

class SearchIssuesArgs(BaseModel):
    """Arguments for the search_issues tool."""
    jql: str = Field(description="JQL query to search for issues")
    max_results: int = Field(default=50, description="Maximum number of results to return", ge=1, le=100)
    start_at: int = Field(default=0, description="Index of the first result to return", ge=0)
    fields: List[str] = Field(
        default=["key", "summary", "status", "assignee", "issuetype", "priority", "created", "updated"],
        description="List of fields to return"
    )

    @field_validator('jql')
    def validate_jql(cls, v):
        if not v or not v.strip():
            raise ValueError("JQL query cannot be empty")
        return v.strip()

class CreateIssueArgs(BaseModel):
    """Arguments for the create_issue tool."""
    project_key: str = Field(description="The project key (e.g. PROJ)")
    summary: str = Field(description="Issue summary/title")
    description: Optional[str] = Field(default=None, description="Issue description")
    issue_type: str = Field(default="Task", description="Issue type (e.g. Bug, Task, Story)")
    priority: Optional[str] = Field(default=None, description="Issue priority")
    assignee: Optional[str] = Field(default=None, description="Username of the assignee")
    labels: List[str] = Field(default=[], description="List of labels to add to the issue")
    custom_fields: Dict[str, Any] = Field(default={}, description="Custom field values")

    @field_validator('project_key')
    def validate_project_key(cls, v):
        if not v or not v.strip():
            raise ValueError("Project key cannot be empty")
        return v.strip().upper()

    @field_validator('summary')
    def validate_summary(cls, v):
        if not v or not v.strip():
            raise ValueError("Summary cannot be empty")
        return v.strip()

    @field_validator('issue_type')
    def validate_issue_type(cls, v):
        if not v or not v.strip():
            raise ValueError("Issue type cannot be empty")
        return v.strip()

class JiraClient:
    """Simple JIRA client."""
    
    def __init__(self, config: JiraConfig):
        """Initialize the JIRA client with configuration."""
        self.config = config
        self._client = None
        self._verify_config()
    
    def _verify_config(self):
        """Verify the configuration is valid."""
        if not self.config.jira_url or not self.config.jira_username or not self.config.jira_api_token:
            logger.error("JIRA configuration is incomplete")
            raise ValueError("JIRA configuration is incomplete")
    
    def connect(self) -> bool:
        """Connect to the JIRA instance."""
        try:
            self._client = JIRA(
                server=self.config.jira_url,
                basic_auth=(self.config.jira_username, self.config.jira_api_token)
            )
            # Test connection by getting server info
            self._client.server_info()
            logger.info(f"Connected to JIRA at {self.config.jira_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to JIRA: {str(e)}")
            return False
    
    @property
    def client(self) -> Optional[JIRA]:
        """Get the JIRA client, connecting if necessary."""
        if self._client is None:
            self.connect()
        return self._client
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get a JIRA issue by key."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}
            
            issue = self.client.issue(issue_key)
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "issue_type": issue.fields.issuetype.name,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
            }
        except Exception as e:
            logger.error(f"Error getting issue {issue_key}: {str(e)}")
            return {"error": f"Error getting issue: {str(e)}"}

    def search_issues(self, jql: str, max_results: int = 50, start_at: int = 0, fields: List[str] = None) -> Dict[str, Any]:
        """Search for issues using JQL."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}

            # Default fields if none specified
            if not fields:
                fields = ["key", "summary", "status", "assignee", "issuetype", "priority"]

            # Execute search
            issues = self.client.search_issues(
                jql_str=jql,
                maxResults=max_results,
                startAt=start_at,
                fields=",".join(fields)
            )

            # Format results
            results = []
            for issue in issues:
                issue_dict = {"key": issue.key}
                for field in fields:
                    if field == "key":
                        continue
                    try:
                        value = getattr(issue.fields, field)
                        if field == "assignee":
                            issue_dict[field] = value.displayName if value else None
                        elif field == "status":
                            issue_dict[field] = value.name if value else None
                        elif field == "issuetype":
                            issue_dict[field] = value.name if value else None
                        elif field == "priority":
                            issue_dict[field] = value.name if value else None
                        else:
                            issue_dict[field] = value
                    except AttributeError:
                        issue_dict[field] = None

                results.append(issue_dict)

            return {
                "total": issues.total,
                "start_at": start_at,
                "max_results": max_results,
                "issues": results
            }

        except Exception as e:
            logger.error(f"Error searching issues with JQL '{jql}': {str(e)}")
            return {"error": f"Error searching issues: {str(e)}"}

    def create_issue(self,
                    project_key: str,
                    summary: str,
                    description: Optional[str] = None,
                    issue_type: str = "Task",
                    priority: Optional[str] = None,
                    assignee: Optional[str] = None,
                    labels: List[str] = None,
                    custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new JIRA issue."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}

            # Prepare issue fields
            issue_dict = {
                'project': project_key,
                'summary': summary,
                'issuetype': {'name': issue_type}
            }

            # Add optional fields
            if description:
                issue_dict['description'] = description
            if priority:
                issue_dict['priority'] = {'name': priority}
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            if labels:
                issue_dict['labels'] = labels
            if custom_fields:
                issue_dict.update(custom_fields)

            # Create the issue
            issue = self.client.create_issue(fields=issue_dict)

            # Return the created issue details
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "issue_type": issue.fields.issuetype.name,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
                "labels": issue.fields.labels
            }

        except Exception as e:
            logger.error(f"Error creating issue: {str(e)}")
            return {"error": f"Error creating issue: {str(e)}"}

# Define tool functions
async def get_issue(arguments: Dict[str, Any]) -> bytes:
    """
    Get a JIRA issue by key.
    
    Args:
        arguments: A dictionary with:
            - issue_key (str, optional): The JIRA issue key (default: "PROJ-123")
    """
    try:
        # Parse and validate arguments
        args = GetIssueArgs(**arguments) if arguments else GetIssueArgs()
        logger.debug(f"get_issue called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Get the issue
        result = client.get_issue(args.issue_key)
        
        logger.debug(f"Generated response: {result}")
        
        # Return the response as a JSON string
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in get_issue tool: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def search_issues(arguments: Dict[str, Any]) -> bytes:
    """
    Search for JIRA issues using JQL.
    
    Args:
        arguments: A dictionary with:
            - jql (str): JQL query to search for issues
            - max_results (int, optional): Maximum number of results to return (default: 50)
            - start_at (int, optional): Index of the first result to return (default: 0)
            - fields (List[str], optional): List of fields to return
    """
    try:
        # Parse and validate arguments
        args = SearchIssuesArgs(**arguments)
        logger.debug(f"search_issues called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Search issues
        result = client.search_issues(
            jql=args.jql,
            max_results=args.max_results,
            start_at=args.start_at,
            fields=args.fields
        )
        
        logger.debug(f"Generated response: {result}")
        
        # Return the response as a JSON string
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in search_issues tool: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def create_issue(arguments: Dict[str, Any]) -> bytes:
    """
    Create a new JIRA issue.
    
    Args:
        arguments: A dictionary with:
            - project_key (str): The project key (e.g. PROJ)
            - summary (str): Issue summary/title
            - description (str, optional): Issue description
            - issue_type (str, optional): Issue type (default: "Task")
            - priority (str, optional): Issue priority
            - assignee (str, optional): Username of the assignee
            - labels (List[str], optional): List of labels
            - custom_fields (Dict[str, Any], optional): Custom field values
    """
    try:
        # Parse and validate arguments
        args = CreateIssueArgs(**arguments)
        logger.debug(f"create_issue called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Create the issue
        result = client.create_issue(
            project_key=args.project_key,
            summary=args.summary,
            description=args.description,
            issue_type=args.issue_type,
            priority=args.priority,
            assignee=args.assignee,
            labels=args.labels,
            custom_fields=args.custom_fields
        )
        
        logger.debug(f"Generated response: {result}")
        
        # Return the response as a JSON string
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in create_issue tool: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

# Create the MCP server
def create_server():
    # Create the server
    mcp_server = FastMCP("SimpleJira", log_level="DEBUG")
    
    # Add the tools
    logger.info("Adding JIRA tools to MCP server...")
    mcp_server.add_tool(
        get_issue,    # Function reference
        name="get_issue",  # Tool name
        description="Get a JIRA issue by key"  # Description
    )
    mcp_server.add_tool(
        search_issues,    # Function reference
        name="search_issues",  # Tool name
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
"""  # Description
    )
    mcp_server.add_tool(
        create_issue,    # Function reference
        name="create_issue",  # Tool name
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
"""  # Description
    )
    logger.info("Tools added successfully")
    
    return mcp_server

@app.command()
def run(transport: Transport = Transport.stdio):
    """Run the MCP server."""
    logger.info(f"Starting Simple JIRA MCP server with {transport.value} transport...")
    
    # Test JIRA connection
    try:
        config = JiraConfig()
        client = JiraClient(config)
        if client.connect():
            logger.info("Successfully connected to JIRA")
        else:
            logger.warning("Failed to connect to JIRA - check your credentials")
    except Exception as e:
        logger.error(f"Error connecting to JIRA: {str(e)}")
        logger.warning("Server will start but JIRA operations may fail")
    
    # Create and run the server
    mcp_server = create_server()
    mcp_server.run(transport.value)

if __name__ == "__main__":
    app() 