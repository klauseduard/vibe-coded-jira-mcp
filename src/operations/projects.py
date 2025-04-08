"""
JIRA project-related operations.
"""
import json
import logging
from typing import Dict, Any

from ..core import JiraClient, JiraConfig

logger = logging.getLogger("simple_jira")

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
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Get the projects
        result = client.get_projects(
            include_archived=arguments.get("include_archived", False),
            max_results=arguments.get("max_results", 50),
            start_at=arguments.get("start_at", 0)
        )
        
        logger.debug(f"Generated response: {result}")
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in get_projects operation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode() 