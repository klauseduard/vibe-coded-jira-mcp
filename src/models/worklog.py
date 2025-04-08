"""
JIRA worklog-related models.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class LogWorkArgs(BaseModel):
    """Arguments for logging work on a JIRA issue."""
    issue_key: str = Field(description="The JIRA issue key (e.g., PROJ-123)")
    time_spent: str = Field(description="Time spent in JIRA format (e.g., '2h 30m', '1d', '30m')")
    comment: Optional[str] = Field(default=None, description="Optional comment for the work log")
    started_at: Optional[str] = Field(default=None, description="When the work was started (defaults to now)")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("issue_key")
    def validate_issue_key(cls, v: str) -> str:
        if not v or not "-" in v:
            raise ValueError("Issue key must be in format PROJECT-123")
        return v.upper()

    @field_validator("time_spent")
    def validate_time_spent(cls, v: str) -> str:
        # Basic validation for time format
        valid_units = ["w", "d", "h", "m"]
        v = v.lower().strip()
        parts = v.split()
        
        for part in parts:
            if not any(part.endswith(unit) for unit in valid_units):
                raise ValueError("Time must be specified in weeks (w), days (d), hours (h), or minutes (m)")
            if not part[:-1].isdigit():
                raise ValueError("Time value must be a number followed by unit (e.g., '2h', '30m')")
        return v 