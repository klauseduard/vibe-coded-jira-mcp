# Simple JIRA MCP Architecture

This document illustrates the architecture and workflows of the Simple JIRA MCP project using Mermaid diagrams. The project is designed to provide a seamless integration between Cursor IDE and JIRA, enabling AI-powered interactions with JIRA data through the Model Context Protocol (MCP).

## System Architecture

The system follows a layered architecture pattern, with clear separation of concerns between different components:

```mermaid
graph TD
    A[CLI Interface] -->|Typer Commands| B[FastMCP Server]
    B -->|MCP Tools| C[Operations Layer]
    C -->|Core| D[JiraClient]
    D -->|API| E[JIRA Server]
    
    subgraph Models
        F[Issue Models]
        G[Comment Models]
        H[Worklog Models]
        I[Config Models]
    end
    
    subgraph Operations
        J[Issue Ops]
        K[Comment Ops]
        L[Worklog Ops]
        M[Project Ops]
    end
    
    C -->|Uses| J
    C -->|Uses| K
    C -->|Uses| L
    C -->|Uses| M
    
    J -->|Uses| F
    K -->|Uses| G
    L -->|Uses| H
    D -->|Uses| I
```

### Component Breakdown

1. **CLI Interface (Typer)**
   - Provides command-line interface for users
   - Handles argument parsing and validation
   - Routes commands to the MCP server

2. **FastMCP Server**
   - Implements the Model Context Protocol
   - Manages tool registration and execution
   - Handles communication between Cursor IDE and JIRA

3. **Operations Layer** (`src/operations/`)
   - Implements MCP tool operations
   - Handles request/response formatting
   - Manages error handling and logging
   - Validates input using Pydantic models

4. **Core Layer** (`src/core/`)
   - `JiraClient`: Encapsulates JIRA API interactions
   - `JiraConfig`: Manages configuration
   - Handles authentication and request formatting
   - Implements error handling and retries

5. **Models Layer** (`src/models/`)
   - Issue-related models (`IssueType`, `IssueArgs`, etc.)
   - Comment models (`CommentArgs`, `GetCommentsArgs`)
   - Worklog models (`LogWorkArgs`)
   - Configuration models (`JiraConfig`)
   - Ensures data validation and type safety

### About Pydantic Models

Our models are organized by domain and provide:

1. **Issue Models** (`models/issue.py`)
   - `IssueType`: Issue type definition
   - `IssueArgs`: Issue creation/update parameters
   - `IssueTransitionArgs`: Status transition parameters
   - `CloneIssueArgs`: Issue cloning parameters

2. **Comment Models** (`models/comment.py`)
   - `CommentArgs`: Comment creation parameters
   - `GetCommentsArgs`: Comment retrieval parameters

3. **Worklog Models** (`models/worklog.py`)
   - `LogWorkArgs`: Work logging parameters
   - Time format validation
   - Issue key validation

4. **Configuration** (`core/config.py`)
   - `JiraConfig`: JIRA connection settings
   - Environment variable management
   - Credential handling

## Issue Lifecycle

The system supports a complete issue lifecycle, from creation through updates and work logging:

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant MCP
    participant JiraClient
    participant JIRA

    User->>CLI: Create Issue
    CLI->>MCP: create_issue
    MCP->>JiraClient: create_issue
    JiraClient->>JIRA: POST /issue
    JIRA-->>JiraClient: Issue Created
    JiraClient-->>MCP: Response
    MCP-->>CLI: Success
    CLI-->>User: Issue Created

    User->>CLI: Update Issue
    CLI->>MCP: update_issue
    MCP->>JiraClient: update_issue
    JiraClient->>JIRA: PUT /issue/{key}
    JIRA-->>JiraClient: Issue Updated
    JiraClient-->>MCP: Response
    MCP-->>CLI: Success
    CLI-->>User: Issue Updated

    User->>CLI: Clone Issue
    CLI->>MCP: clone_issue
    MCP->>JiraClient: clone_issue
    JiraClient->>JIRA: GET /issue/{source_key}
    JIRA-->>JiraClient: Source Issue Data
    JiraClient->>JIRA: POST /issue
    JIRA-->>JiraClient: Clone Created
    JiraClient->>JIRA: POST /issueLink
    JIRA-->>JiraClient: Link Created
    JiraClient-->>MCP: Response
    MCP-->>CLI: Success
    CLI-->>User: Issue Cloned

    User->>CLI: Log Work
    CLI->>MCP: log_work
    MCP->>JiraClient: log_work
    JiraClient->>JIRA: POST /issue/{key}/worklog
    JIRA-->>JiraClient: Work Logged
    JiraClient-->>MCP: Response
    MCP-->>CLI: Success
    CLI-->>User: Work Logged
```

### Lifecycle Stages

1. **Issue Creation**
   - Validates required fields (project key, summary)
   - Supports optional fields (description, type, priority)
   - Returns the newly created issue key

2. **Issue Updates**
   - Allows modification of any editable fields
   - Supports partial updates
   - Maintains issue history

3. **Issue Cloning**
   - Creates a copy of an existing issue
   - Carries over all fields from source, including custom fields
   - Optionally copies attachments
   - Optionally creates a link to source issue
   - Allows field overrides (summary, description, etc.)
   - Helps work around mandatory custom fields in JIRA projects

4. **Work Logging**
   - Tracks time spent on issues
   - Supports work descriptions
   - Maintains worklog history

## Data Validation Flow

Data validation is a critical component ensuring data integrity and API compatibility:

```mermaid
graph LR
    A[Input Data] -->|Validation| B{Pydantic Models}
    B -->|Valid| C[Process Request]
    B -->|Invalid| D[Error Response]
    
    subgraph Validation Rules
        E[Required Fields]
        F[Format Validation]
        G[Custom Validators]
    end
    
    B -->|Uses| E
    B -->|Uses| F
    B -->|Uses| G
```

### Validation Components

1. **Input Data**
   - Command-line arguments
   - Environment variables
   - API request parameters

2. **Validation Rules**
   - Required field checking
   - Data format validation
   - Custom business rules
   - Type checking

3. **Error Handling**
   - Detailed error messages
   - Validation failure responses
   - API error mapping

## Authentication Flow

Secure authentication is handled through environment variables and API tokens:

```mermaid
sequenceDiagram
    participant User
    participant App
    participant JIRA

    User->>App: Start Application
    App->>App: Load Environment Variables
    App->>App: Initialize JiraConfig
    App->>JIRA: Connect with Credentials
    JIRA-->>App: Authentication Success
    App-->>User: Ready for Commands
```

### Security Implementation

1. **Credential Management**
   - Environment variable based configuration
   - Secure API token storage
   - No hardcoded credentials

2. **Connection Process**
   - Validates credentials on startup
   - Maintains authenticated session
   - Handles connection failures

3. **Error Handling**
   - Clear authentication error messages
   - Graceful failure handling
   - Secure error logging

## Design Principles

The architecture follows several key design principles:

1. **Separation of Concerns**
   - Clear boundaries between components
   - Modular design for easy maintenance
   - Independent testing capabilities

2. **Type Safety**
   - Pydantic models for data validation
   - Strong typing throughout the codebase
   - Runtime type checking

3. **Error Handling**
   - Comprehensive error catching
   - Detailed error messages
   - Graceful failure modes

4. **Extensibility**
   - Modular tool registration
   - Easy to add new features
   - Configurable components

## Future Considerations

The architecture is designed to support future enhancements:

1. **Potential Extensions**
   - Additional JIRA API endpoints
   - New MCP tools
   - Enhanced validation rules

2. **Scalability**
   - Connection pooling
   - Rate limiting
   - Caching mechanisms

3. **Monitoring**
   - Performance metrics
   - Usage statistics
   - Error tracking

These diagrams provide a visual representation of:
1. The overall system architecture and component relationships
2. The sequence of operations for issue lifecycle management
3. The data validation flow using Pydantic models
4. The authentication process

The diagrams can help new developers understand:
- How different components interact
- The flow of data through the system
- Where validation occurs
- How authentication is handled
- The sequence of operations for common tasks 