"""
JIRA comment-related operations.
"""
import json
import logging
from typing import Dict, Any

from ..core import JiraClient, JiraConfig
from ..models.comment import CommentArgs, GetCommentsArgs

logger = logging.getLogger("simple_jira")

async def add_comment(arguments: Dict[str, Any]) -> bytes:
    """
    Add a comment to a JIRA issue.
    
    Args:
        arguments: A dictionary matching CommentArgs model
    """
    try:
        # Parse and validate arguments
        args = CommentArgs(**arguments)
        logger.debug(f"add_comment called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Add the comment
        result = client.add_comment(args)
        
        logger.debug(f"Generated response: {result}")
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in add_comment operation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode()

async def get_comments(arguments: Dict[str, Any]) -> bytes:
    """
    Get comments for a JIRA issue.
    
    Args:
        arguments: A dictionary matching GetCommentsArgs model
    """
    try:
        # Parse and validate arguments
        args = GetCommentsArgs(**arguments)
        logger.debug(f"get_comments called with arguments: {args}")
        
        # Get JIRA configuration
        config = JiraConfig()
        client = JiraClient(config)
        
        # Get the comments
        result = client.get_comments(args)
        
        logger.debug(f"Generated response: {result}")
        return json.dumps(result).encode()
    except Exception as e:
        logger.error(f"Error in get_comments operation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}).encode() 