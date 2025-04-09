"""
JIRA comment-related models.
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class CommentArgs(BaseModel):
    """Arguments for the add_comment tool."""
    issue_key: str = Field(description="The JIRA issue key (e.g., PROJ-123)")
    comment: str = Field(description="Comment text to add to the issue")
    visibility: Optional[Dict[str, str]] = Field(
        default=None, 
        description="Visibility settings for the comment (e.g., {'type': 'role', 'value': 'Administrators'})"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("issue_key")
    def validate_issue_key(cls, v: str) -> str:
        if not v or not "-" in v:
            raise ValueError("Issue key must be in format PROJECT-123")
        return v.upper()

    @field_validator("comment")
    def validate_comment(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Comment cannot be empty")
        return v.strip()

class GetCommentsArgs(BaseModel):
    """Arguments for the get_comments tool."""
    issue_key: str = Field(description="The JIRA issue key (e.g., PROJ-123)")
    max_results: int = Field(default=50, description="Maximum number of comments to return", ge=1, le=100)
    start_at: int = Field(default=0, description="Index of the first comment to return", ge=0)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("issue_key")
    def validate_issue_key(cls, v: str) -> str:
        if not v or not "-" in v:
            raise ValueError("Issue key must be in format PROJECT-123")
        return v.upper() 