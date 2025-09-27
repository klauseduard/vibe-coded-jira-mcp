# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the MCP Server
```bash
./run-jira-mcp.sh  # Main entry point - installs dependencies and runs server
python3 simple_jira.py  # Direct execution
```

### Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### Environment Setup
Copy `.env.example` to `.env` and configure:
- `JIRA_URL`: Your JIRA instance URL
- `JIRA_USERNAME`: Your JIRA username
- `JIRA_API_TOKEN`: Your JIRA API token

## Architecture Overview

This is a Model Context Protocol (MCP) server for JIRA integration, implementing a modular architecture:

### Core Structure
- **Entry Point**: `simple_jira.py` - FastMCP server with Typer CLI
- **Modular Design**: Code is organized into `src/` with clear separation:
  - `src/core/` - Base JIRA client and configuration
  - `src/models/` - Pydantic data models for validation
  - `src/operations/` - MCP tool implementations

### Key Components

**Core Layer** (`src/core/`):
- `client.py` - `JiraClient` class handling JIRA API interactions
- `config.py` - `JiraConfig` for environment-based configuration

**Models Layer** (`src/models/`):
- `issue.py` - Issue creation, update, transition, and cloning models
- `comment.py` - Comment creation and retrieval models
- `worklog.py` - Work logging models with validation
- All models use Pydantic for type safety and validation

**Operations Layer** (`src/operations/`):
- `issues.py` - Issue CRUD operations (get, search, create, update, clone)
- `comments.py` - Comment management (add, get)
- `worklog.py` - Time tracking operations
- `projects.py` - Project listing and metadata

### Architecture Principles
- **Type Safety**: Pydantic models throughout for runtime validation
- **Modular Design**: Clear separation between API client, data models, and MCP operations
- **Error Handling**: Comprehensive error catching with detailed logging
- **Security**: Environment-based credential management, no hardcoded secrets

## MCP Tools Available
- `get_issue` - Fetch JIRA issue by key
- `search_issues` - JQL-based issue search with pagination
- `create_issue` - Create new issues with validation
- `update_issue` - Update existing issues
- `clone_issue` - Clone issues with custom field preservation
- `add_comment` - Add comments to issues
- `get_comments` - Retrieve issue comments
- `log_work` - Track time spent on issues
- `get_projects` - List available projects

## Implementation Status (v0.4)

**Completed Features**:
- ✅ Basic JIRA integration with authentication
- ✅ Issue CRUD operations with field validation
- ✅ JQL search with pagination and field selection
- ✅ Comment management
- ✅ Work logging
- ✅ Issue cloning (helps with mandatory custom fields)
- ✅ Project listing
- ✅ Modular architecture (core refactoring)

**Development Notes**:
- Uses stdio transport for MCP communication
- Logging goes to both stderr and `jira_mcp.log`
- Custom field support for heavily customized JIRA projects
- Clone functionality as workaround for mandatory fields

## Key Files to Understand
- `simple_jira.py:13-23` - MCP tool registration and imports
- `src/core/client.py` - Main JIRA API client implementation
- `src/operations/issues.py` - Core issue management operations
- `ARCHITECTURE.md` - Detailed system architecture with diagrams
- `IMPLEMENTATION_PLAN.md` - Development roadmap and progress tracking

## Development Patterns
- All operations use Pydantic models for input validation
- Error handling follows consistent patterns with logging
- MCP tools are registered in `simple_jira.py` and implemented in `src/operations/`
- Configuration is environment-based using `src/core/config.py`
- Follow the modular structure when adding new features