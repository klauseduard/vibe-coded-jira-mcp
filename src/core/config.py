"""
JIRA configuration settings.
"""
import os
from pydantic import BaseModel, Field

class JiraConfig(BaseModel):
    """JIRA configuration settings."""
    jira_url: str = Field(default="", description="JIRA server URL")
    jira_username: str = Field(default="", description="JIRA username or email")
    jira_api_token: str = Field(default="", description="JIRA API token")

    def __init__(self, **data):
        # Load environment variables explicitly
        import os
        import logging
        from dotenv import load_dotenv

        load_dotenv()  # Make sure .env is loaded

        logger = logging.getLogger("simple_jira")

        # Override with environment variables if not provided
        if 'jira_url' not in data:
            data['jira_url'] = os.getenv("JIRA_URL", "")
        if 'jira_username' not in data:
            data['jira_username'] = os.getenv("JIRA_USERNAME", "")
        if 'jira_api_token' not in data:
            data['jira_api_token'] = os.getenv("JIRA_API_TOKEN", "")

        logger.debug(f"Config loaded: URL={data['jira_url']}, USER={data['jira_username']}, TOKEN={'SET' if data['jira_api_token'] else 'NOT SET'}")

        super().__init__(**data)

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        frozen = True  # Makes the config immutable after creation 