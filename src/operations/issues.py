"""
JIRA issue-related operations.
"""
import json
import logging
from typing import Dict, Any

from ..core import JiraClient, JiraConfig
from ..models.issue import IssueArgs, CloneIssueArgs

logger = logging.getLogger("simple_jira")

async def get_issue(arguments: Dict[str, Any]) -> bytes:
    """
    Get a JIRA issue by key.
    
    Args:
        arguments: A dictionary with:
            - issue_key (str): The JIRA issue key (e.g., "PROJ-123")
    """
    try:
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Get the issue
        result = client.get_issue(arguments["issue_key"])
        
        logger.debug(f"Generated response: {result}")
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in get_issue operation: {str(e)}", exc_info=True)
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
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Search issues
        result = client.search_issues(
            jql=arguments["jql"],
            max_results=arguments.get("max_results", 50),
            start_at=arguments.get("start_at", 0),
            fields=arguments.get("fields")
        )
        
        logger.debug(f"Generated response: {result}")
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in search_issues operation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def create_issue(arguments: Dict[str, Any]) -> bytes:
    """
    Create a new JIRA issue.
    
    Args:
        arguments: A dictionary matching IssueArgs model
    """
    try:
        # Parse and validate arguments
        args = IssueArgs(**arguments)
        logger.debug(f"create_issue called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Create the issue
        result = client.create_issue(
            project_key=args.project_key,
            summary=args.summary,
            description=args.description,
            issue_type=args.issue_type.name if isinstance(args.issue_type, dict) else args.issue_type,
            priority=args.priority,
            assignee=args.assignee,
            labels=args.labels,
            custom_fields=args.custom_fields
        )
        
        logger.debug(f"Generated response: {result}")
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in create_issue operation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def update_issue(arguments: Dict[str, Any]) -> bytes:
    """
    Update an existing JIRA issue.
    
    Args:
        arguments: A dictionary with issue key and fields to update
    """
    try:
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Update the issue
        result = client.update_issue(
            issue_key=arguments["issue_key"],
            summary=arguments.get("summary"),
            description=arguments.get("description"),
            priority=arguments.get("priority"),
            assignee=arguments.get("assignee"),
            labels=arguments.get("labels"),
            comment=arguments.get("comment"),
            custom_fields=arguments.get("custom_fields")
        )
        
        logger.debug(f"Generated response: {result}")
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in update_issue operation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def clone_issue(arguments: Dict[str, Any]) -> bytes:
    """
    Clone an existing JIRA issue.
    
    Args:
        arguments: A dictionary matching CloneIssueArgs model
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
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in clone_issue operation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode() 