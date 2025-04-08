"""
JIRA worklog-related operations.
"""
import json
import logging
from typing import Dict, Any

from ..core import JiraClient, JiraConfig
from ..models.worklog import LogWorkArgs

logger = logging.getLogger("simple_jira")

async def log_work(arguments: Dict[str, Any]) -> bytes:
    """
    Log work time on a JIRA issue.
    
    Args:
        arguments: A dictionary matching LogWorkArgs model
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
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in log_work operation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode() 