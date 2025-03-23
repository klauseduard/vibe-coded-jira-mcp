#!/usr/bin/env python3
"""
A small self-contained JIRA MCP server.
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

class UpdateIssueArgs(BaseModel):
    """Arguments for the update_issue tool."""
    issue_key: str = Field(description="The JIRA issue key (e.g. PROJ-123)")
    summary: Optional[str] = Field(default=None, description="New issue summary/title")
    description: Optional[str] = Field(default=None, description="New issue description")
    priority: Optional[str] = Field(default=None, description="New issue priority")
    assignee: Optional[str] = Field(default=None, description="New assignee username")
    labels: Optional[List[str]] = Field(default=None, description="New list of labels")
    comment: Optional[str] = Field(default=None, description="Comment to add to the issue")
    custom_fields: Dict[str, Any] = Field(default={}, description="Custom field values to update")

    @field_validator('issue_key')
    def validate_issue_key(cls, v):
        if not v or not v.strip():
            raise ValueError("Issue key cannot be empty")
        return v.strip().upper()

    @field_validator('summary')
    def validate_summary(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Summary cannot be empty if provided")
            return v.strip()
        return v

    @field_validator('comment')
    def validate_comment(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Comment cannot be empty if provided")
            return v.strip()
        return v

class GetProjectsArgs(BaseModel):
    """Arguments for the get_projects tool."""
    include_archived: bool = Field(default=False, description="Whether to include archived projects")
    max_results: int = Field(default=50, description="Maximum number of results to return", ge=1, le=100)
    start_at: int = Field(default=0, description="Index of the first result to return", ge=0)

class LogWorkArgs(BaseModel):
    """Arguments for the log_work tool."""
    issue_key: str = Field(description="The JIRA issue key (e.g., PROJ-123)")
    time_spent: str = Field(description="Time spent in JIRA format (e.g., '2h 30m', '1d', '30m')")
    comment: Optional[str] = Field(default=None, description="Optional comment for the work log")
    started_at: Optional[str] = Field(default=None, description="When the work was started (defaults to now)")

    @field_validator("issue_key")
    def validate_issue_key(cls, v: str) -> str:
        if not v or not "-" in v:
            raise ValueError("Issue key must be in format PROJECT-123")
        return v.upper()

    @field_validator("time_spent")
    def validate_time_spent(cls, v: str) -> str:
        # Basic validation for time format
        valid_units = ["w", "d", "h", "m"]
        v = v.lower().strip()
        parts = v.split()
        
        for part in parts:
            if not any(part.endswith(unit) for unit in valid_units):
                raise ValueError("Time must be specified in weeks (w), days (d), hours (h), or minutes (m)")
            if not part[:-1].isdigit():
                raise ValueError("Time value must be a number followed by unit (e.g., '2h', '30m')")
        return v

class CloneIssueArgs(BaseModel):
    """Arguments for the clone_issue tool."""
    source_issue_key: str = Field(description="The source JIRA issue key to clone from (e.g., PROJ-123)")
    project_key: Optional[str] = Field(default=None, description="The target project key (e.g. PROJ) if different from source")
    summary: Optional[str] = Field(default=None, description="New summary (defaults to 'Clone of [ORIGINAL-SUMMARY]')")
    description: Optional[str] = Field(default=None, description="New description (defaults to original description)")
    issue_type: Optional[str] = Field(default=None, description="Issue type (defaults to original issue type)")
    priority: Optional[str] = Field(default=None, description="Issue priority (defaults to original priority)")
    assignee: Optional[str] = Field(default=None, description="Username of the assignee (defaults to original assignee)")
    labels: Optional[List[str]] = Field(default=None, description="List of labels (defaults to original labels)")
    custom_fields: Dict[str, Any] = Field(default={}, description="Custom field values to override")
    copy_attachments: bool = Field(default=False, description="Whether to copy attachments from the source issue")
    add_link_to_source: bool = Field(default=True, description="Whether to add a link to the source issue")

    @field_validator("source_issue_key")
    def validate_source_issue_key(cls, v: str) -> str:
        if not v or not "-" in v:
            raise ValueError("Source issue key must be in format PROJECT-123")
        return v.upper()

    @field_validator("project_key")
    def validate_project_key(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Project key cannot be empty if provided")
            return v.strip().upper()
        return v

    @field_validator("summary")
    def validate_summary(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Summary cannot be empty if provided")
            return v.strip()
        return v

class JiraError(Exception):
    """Error raised by JIRA operations."""
    pass

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

    def update_issue(self,
                    issue_key: str,
                    summary: Optional[str] = None,
                    description: Optional[str] = None,
                    priority: Optional[str] = None,
                    assignee: Optional[str] = None,
                    labels: Optional[List[str]] = None,
                    comment: Optional[str] = None,
                    custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update a JIRA issue."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}

            # Get the issue first
            issue = self.client.issue(issue_key)
            
            # Prepare update fields
            update_dict = {}
            
            # Handle standard fields
            if summary is not None:
                update_dict['summary'] = summary
            if description is not None:
                update_dict['description'] = description
            if priority is not None:
                update_dict['priority'] = {'name': priority}
            if assignee is not None:
                update_dict['assignee'] = {'name': assignee}
            
            # Update the issue fields
            if update_dict:
                issue.update(fields=update_dict)
            
            # Handle labels separately as they need special treatment
            if labels is not None:
                issue.update(fields={'labels': labels})
            
            # Add comment if provided
            if comment:
                issue.add_comment(comment)
            
            # Handle custom fields
            if custom_fields:
                issue.update(fields=custom_fields)

            # Return the updated issue details
            updated_issue = self.client.issue(issue_key)
            return {
                "key": updated_issue.key,
                "summary": updated_issue.fields.summary,
                "description": updated_issue.fields.description,
                "status": updated_issue.fields.status.name,
                "assignee": updated_issue.fields.assignee.displayName if updated_issue.fields.assignee else None,
                "reporter": updated_issue.fields.reporter.displayName if updated_issue.fields.reporter else None,
                "created": updated_issue.fields.created,
                "updated": updated_issue.fields.updated,
                "issue_type": updated_issue.fields.issuetype.name,
                "priority": updated_issue.fields.priority.name if updated_issue.fields.priority else None,
                "labels": updated_issue.fields.labels,
                "comment_added": bool(comment)
            }

        except Exception as e:
            logger.error(f"Error updating issue {issue_key}: {str(e)}")
            return {"error": f"Error updating issue: {str(e)}"}

    def get_projects(self, include_archived: bool = False, max_results: int = 50, start_at: int = 0) -> Dict[str, Any]:
        """Get list of JIRA projects."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}

            # Get all projects
            logger.debug("Fetching projects from JIRA...")
            projects = self.client.projects()
            logger.debug(f"Got projects response type: {type(projects)}")
            if projects:
                logger.debug(f"First project type: {type(projects[0])}")
                logger.debug(f"First project dir: {dir(projects[0])}")
            
            # Apply pagination
            total = len(projects)
            projects = projects[start_at:start_at + max_results]
            
            # Format results
            results = []
            for project in projects:
                # Get the basic project info that's always available
                try:
                    project_dict = {
                        "key": project.key,
                        "name": project.name,
                        "id": str(project.id)
                    }
                    results.append(project_dict)
                except Exception as e:
                    logger.error(f"Error processing project: {str(e)}")
                    logger.error(f"Project object: {project}")
                    continue

            return {
                "total": total,
                "start_at": start_at,
                "max_results": max_results,
                "projects": results
            }

        except Exception as e:
            logger.error(f"Error getting projects: {str(e)}")
            return {"error": f"Error getting projects: {str(e)}"}

    def log_work(self, args: LogWorkArgs) -> Dict[str, Any]:
        """Log work on a JIRA issue."""
        logger.info(f"Logging work on issue {args.issue_key}: {args.time_spent}")
        
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}
            
            # Create worklog entry
            worklog = self.client.add_worklog(
                issue=args.issue_key,
                timeSpent=args.time_spent,
                comment=args.comment if args.comment else None,
                started=args.started_at if args.started_at else None
            )
            
            logger.info(f"Successfully logged work: {worklog.id}")
            return {
                "id": worklog.id,
                "issue_key": args.issue_key,
                "time_spent": args.time_spent,
                "author": worklog.author.displayName,
                "created": str(worklog.created)
            }
            
        except Exception as e:
            logger.error(f"Error logging work: {str(e)}")
            return {"error": f"Error logging work: {str(e)}"}

    def clone_issue(self, args: CloneIssueArgs) -> Dict[str, Any]:
        """Clone a JIRA issue."""
        logger.info(f"Cloning issue {args.source_issue_key}")
        
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}
            
            # Get the source issue
            source_issue = self.client.issue(args.source_issue_key)
            
            # Extract data from source issue
            source_project = source_issue.fields.project.key
            target_project = args.project_key or source_project
            
            # Prepare issue fields
            issue_dict = {
                'project': target_project,
                'summary': args.summary or f"Clone of {source_issue.fields.summary}",
                'issuetype': {'name': args.issue_type or source_issue.fields.issuetype.name}
            }

            # Add description
            if args.description is not None:
                issue_dict['description'] = args.description
            else:
                issue_dict['description'] = source_issue.fields.description

            # Add priority if available
            if args.priority is not None:
                issue_dict['priority'] = {'name': args.priority}
            elif hasattr(source_issue.fields, 'priority') and source_issue.fields.priority:
                issue_dict['priority'] = {'name': source_issue.fields.priority.name}

            # Add assignee if available
            if args.assignee is not None:
                issue_dict['assignee'] = {'name': args.assignee}
            elif hasattr(source_issue.fields, 'assignee') and source_issue.fields.assignee:
                # Handle different ways JIRA might represent users
                if hasattr(source_issue.fields.assignee, 'accountId'):
                    issue_dict['assignee'] = {'accountId': source_issue.fields.assignee.accountId}
                elif hasattr(source_issue.fields.assignee, 'key'):
                    issue_dict['assignee'] = {'key': source_issue.fields.assignee.key}
                elif hasattr(source_issue.fields.assignee, 'name'):
                    issue_dict['assignee'] = {'name': source_issue.fields.assignee.name}

            # Add labels if available
            if args.labels is not None:
                issue_dict['labels'] = args.labels
            elif hasattr(source_issue.fields, 'labels') and source_issue.fields.labels:
                issue_dict['labels'] = source_issue.fields.labels

            # Handle custom fields - copy over from source issue
            custom_field_prefixes = ['customfield_']
            source_custom_fields = {}
            
            # Extract custom fields from source issue
            for field_name in dir(source_issue.fields):
                if any(field_name.startswith(prefix) for prefix in custom_field_prefixes):
                    field_value = getattr(source_issue.fields, field_name)
                    if field_value is not None:
                        # Handle complex field values that might be objects
                        if hasattr(field_value, 'id'):
                            source_custom_fields[field_name] = {'id': field_value.id}
                        elif hasattr(field_value, 'value'):
                            source_custom_fields[field_name] = {'value': field_value.value}
                        elif hasattr(field_value, 'name'):
                            source_custom_fields[field_name] = {'name': field_value.name}
                        else:
                            source_custom_fields[field_name] = field_value
            
            # Use custom fields from source issue, overridden by any explicitly set fields
            issue_dict.update(source_custom_fields)
            
            # Override with user-specified custom fields
            if args.custom_fields:
                issue_dict.update(args.custom_fields)
            
            # Collect information about source issue for reference
            source_info = {
                "key": source_issue.key,
                "summary": source_issue.fields.summary,
                "project": source_project,
                "issue_type": source_issue.fields.issuetype.name,
                "status": source_issue.fields.status.name,
                "priority": source_issue.fields.priority.name if hasattr(source_issue.fields, 'priority') and source_issue.fields.priority else None,
                "assignee": source_issue.fields.assignee.displayName if hasattr(source_issue.fields, 'assignee') and source_issue.fields.assignee else None,
                "reporter": source_issue.fields.reporter.displayName if hasattr(source_issue.fields, 'reporter') and source_issue.fields.reporter else None,
                "created": source_issue.fields.created,
                "updated": source_issue.fields.updated,
                "custom_fields": source_custom_fields
            }

            # Create the new issue
            new_issue = self.client.create_issue(fields=issue_dict)
            
            # Add link to source issue if requested
            if args.add_link_to_source:
                try:
                    self.client.create_issue_link(
                        type="Cloned",
                        inwardIssue=new_issue.key,
                        outwardIssue=source_issue.key,
                        comment={
                            "body": f"This issue was cloned from {source_issue.key}."
                        }
                    )
                    logger.info(f"Added link from {new_issue.key} to source issue {source_issue.key}")
                except Exception as e:
                    logger.warning(f"Failed to create issue link: {str(e)}")
            
            # Copy attachments if requested
            if args.copy_attachments:
                try:
                    attachments = source_issue.fields.attachment
                    if attachments:
                        for attachment in attachments:
                            # Download the attachment
                            attachment_data = self.client.attachment(attachment.id)
                            
                            # Upload to the new issue
                            self.client.add_attachment(
                                issue=new_issue.key,
                                attachment=attachment_data.get()
                            )
                        logger.info(f"Copied {len(attachments)} attachments to {new_issue.key}")
                except Exception as e:
                    logger.warning(f"Failed to copy attachments: {str(e)}")
            
            # Return the created issue details along with source info
            return {
                "key": new_issue.key,
                "summary": new_issue.fields.summary,
                "description": new_issue.fields.description,
                "status": new_issue.fields.status.name,
                "assignee": new_issue.fields.assignee.displayName if hasattr(new_issue.fields, 'assignee') and new_issue.fields.assignee else None,
                "reporter": new_issue.fields.reporter.displayName if hasattr(new_issue.fields, 'reporter') and new_issue.fields.reporter else None,
                "created": new_issue.fields.created,
                "updated": new_issue.fields.updated,
                "issue_type": new_issue.fields.issuetype.name,
                "priority": new_issue.fields.priority.name if hasattr(new_issue.fields, 'priority') and new_issue.fields.priority else None,
                "labels": new_issue.fields.labels if hasattr(new_issue.fields, 'labels') else [],
                "source_issue": source_info,
                "attachments_copied": args.copy_attachments,
                "link_added": args.add_link_to_source
            }
            
        except Exception as e:
            logger.error(f"Error cloning issue: {str(e)}")
            return {"error": f"Error cloning issue: {str(e)}"}

# Define tool functions
async def hello(arguments: Dict[str, Any]) -> bytes:
    """Say hello to a name with optional enthusiasm."""
    try:
        name = arguments.get("name", "World")
        enthusiastic = arguments.get("enthusiastic", False)
        greeting = f"Hello, {name}{'!' if enthusiastic else '.'}"
        return json.dumps({"greeting": greeting}).encode()
    except Exception as e:
        logger.error(f"Error in hello tool: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

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

async def update_issue(arguments: Dict[str, Any]) -> bytes:
    """
    Update an existing JIRA issue.
    
    Args:
        arguments: A dictionary with:
            - issue_key (str): The JIRA issue key (e.g. PROJ-123)
            - summary (str, optional): New issue summary/title
            - description (str, optional): New issue description
            - priority (str, optional): New issue priority
            - assignee (str, optional): New assignee username
            - labels (List[str], optional): New list of labels
            - comment (str, optional): Comment to add to the issue
            - custom_fields (Dict[str, Any], optional): Custom field values to update
    """
    try:
        # Parse and validate arguments
        args = UpdateIssueArgs(**arguments)
        logger.debug(f"update_issue called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Update the issue
        result = client.update_issue(
            issue_key=args.issue_key,
            summary=args.summary,
            description=args.description,
            priority=args.priority,
            assignee=args.assignee,
            labels=args.labels,
            comment=args.comment,
            custom_fields=args.custom_fields
        )
        
        logger.debug(f"Generated response: {result}")
        
        # Return the response as a JSON string
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in update_issue tool: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def get_projects(arguments: Dict[str, Any]) -> bytes:
    """
    Get list of JIRA projects.
    
    Args:
        arguments: A dictionary with:
            - include_archived (bool, optional): Whether to include archived projects (default: False)
            - max_results (int, optional): Maximum number of results to return (default: 50)
            - start_at (int, optional): Index of the first result to return (default: 0)
    """
    try:
        # Parse and validate arguments
        args = GetProjectsArgs(**arguments) if arguments else GetProjectsArgs()
        logger.debug(f"get_projects called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Get the projects
        result = client.get_projects(
            include_archived=args.include_archived,
            max_results=args.max_results,
            start_at=args.start_at
        )
        
        logger.debug(f"Generated response: {result}")
        
        # Return the response as a JSON string
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in get_projects tool: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def clone_issue(arguments: Dict[str, Any]) -> bytes:
    """
    Clone an existing JIRA issue.
    
    Args:
        arguments: A dictionary with:
            - source_issue_key: The source JIRA issue key to clone from (e.g., PROJ-123)
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
    """
    try:
        # Parse and validate arguments
        args = CloneIssueArgs(**arguments)
        logger.debug(f"clone_issue called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Clone the issue
        result = client.clone_issue(args)
        
        logger.debug(f"Generated response: {result}")
        
        # Return the response as a JSON string
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in clone_issue tool: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def log_work(arguments: Dict[str, Any]) -> bytes:
    """
    Log work time on a JIRA issue.
    
    Args:
        arguments: A dictionary with:
            - issue_key (str): The JIRA issue key (e.g., PROJ-123)
            - time_spent (str): Time spent in JIRA format (e.g., '2h 30m', '1d', '30m')
            - comment (str, optional): Comment for the work log
            - started_at (str, optional): When the work was started (defaults to now)
    """
    try:
        # Parse and validate arguments
        args = LogWorkArgs(**arguments)
        logger.debug(f"log_work called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Log the work
        result = client.log_work(args)
        
        logger.debug(f"Generated response: {result}")
        
        # Return the response as a JSON string
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in log_work tool: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

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
        hello,
        name="hello",
        description="Say hello to a name with optional enthusiasm"
    )
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

    # Run server
    if transport == Transport.stdio:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host=host, port=port)

if __name__ == "__main__":
    app() 
