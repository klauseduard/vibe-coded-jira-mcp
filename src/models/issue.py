"""
JIRA issue-related models.
"""
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

class IssueType(BaseModel):
    """JIRA issue type model."""
    name: str = Field(description="Name of the issue type (e.g., Bug, Task, Story)")
    id: Optional[str] = Field(default=None, description="ID of the issue type")

    model_config = ConfigDict(arbitrary_types_allowed=True)

class IssueArgs(BaseModel):
    """Arguments for creating or updating a JIRA issue."""
    project_key: str = Field(description="The project key (e.g. PROJ)")
    summary: str = Field(description="Issue summary/title")
    description: Optional[str] = Field(default=None, description="Issue description")
    issue_type: Union[str, IssueType] = Field(default="Task", description="Issue type (e.g. Bug, Task, Story)")
    priority: Optional[str] = Field(default=None, description="Issue priority")
    assignee: Optional[str] = Field(default=None, description="Username of the assignee")
    labels: List[str] = Field(default=[], description="List of labels to add to the issue")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field values")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("project_key")
    def validate_project_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Project key cannot be empty")
        return v.strip().upper()

    @field_validator("summary")
    def validate_summary(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Summary cannot be empty")
        return v.strip()

class IssueTransitionArgs(BaseModel):
    """Arguments for transitioning a JIRA issue."""
    issue_key: str = Field(description="The JIRA issue key (e.g. PROJ-123)")
    transition: str = Field(description="The transition to perform (e.g. 'In Progress', 'Done')")
    comment: Optional[str] = Field(default=None, description="Comment to add with the transition")
    resolution: Optional[str] = Field(default=None, description="Resolution when closing an issue")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("issue_key")
    def validate_issue_key(cls, v: str) -> str:
        if not v or not "-" in v:
            raise ValueError("Issue key must be in format PROJECT-123")
        return v.upper()

class CloneIssueArgs(BaseModel):
    """Arguments for cloning a JIRA issue."""
    source_issue_key: str = Field(description="The source JIRA issue key to clone from (e.g., PROJ-123)")
    project_key: Optional[str] = Field(default=None, description="The target project key if different from source")
    summary: Optional[str] = Field(default=None, description="New summary (defaults to 'Clone of [ORIGINAL-SUMMARY]')")
    description: Optional[str] = Field(default=None, description="New description (defaults to original description)")
    issue_type: Optional[str] = Field(default=None, description="Issue type (defaults to original issue type)")
    priority: Optional[str] = Field(default=None, description="Issue priority (defaults to original priority)")
    assignee: Optional[str] = Field(default=None, description="Username of the assignee (defaults to original assignee)")
    labels: Optional[List[str]] = Field(default=None, description="List of labels (defaults to original labels)")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field values to override")
    copy_attachments: bool = Field(default=False, description="Whether to copy attachments from the source issue")
    add_link_to_source: bool = Field(default=True, description="Whether to add a link to the source issue")

    model_config = ConfigDict(arbitrary_types_allowed=True)

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