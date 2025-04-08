"""
Core JIRA client implementation.
"""
import logging
from typing import Dict, Any, Optional, List
from jira import JIRA

logger = logging.getLogger("simple_jira")

class JiraError(Exception):
    """Error raised by JIRA operations."""
    pass

class JiraClient:
    """Simple JIRA client."""
    
    def __init__(self, config):
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
                basic_auth=(self.config.jira_username, self.config.jira_api_token),
                verify=True,
                options={'verify': True}
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