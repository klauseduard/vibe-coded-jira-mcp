"""
JIRA configuration settings.
"""
import os
from pydantic import BaseModel, Field

class JiraConfig(BaseModel):
    """JIRA configuration settings."""
    jira_url: str = Field(default=os.getenv("JIRA_URL", ""), description="JIRA server URL")
    jira_username: str = Field(default=os.getenv("JIRA_USERNAME", ""), description="JIRA username or email")
    jira_api_token: str = Field(default=os.getenv("JIRA_API_TOKEN", ""), description="JIRA API token")

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        frozen = True  # Makes the config immutable after creation 