"""
Core JIRA client package.
"""
from .client import JiraClient, JiraError
from .config import JiraConfig

__all__ = ['JiraClient', 'JiraConfig', 'JiraError'] 