"""
JIRA configuration models and settings.
"""
import os
from pydantic import BaseModel, Field

class JiraConfig(BaseModel):
    """JIRA configuration settings."""
    jira_url: str = Field(default=os.getenv("JIRA_URL", ""))
    jira_username: str = Field(default=os.getenv("JIRA_USERNAME", ""))
    jira_api_token: str = Field(default=os.getenv("JIRA_API_TOKEN", "")) 