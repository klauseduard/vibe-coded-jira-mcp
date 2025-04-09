"""
Core JIRA client implementation.
"""
from .client import JiraClient, JiraError
from .config import JiraConfig

__all__ = ['JiraClient', 'JiraConfig', 'JiraError'] 