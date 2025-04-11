# Rate Limiting Implementation

## Overview

This document describes the rate limiting implementation for the JIRA MCP server. The implementation uses a token bucket algorithm to provide smooth and efficient rate limiting for all JIRA API calls.

## Architecture

```mermaid
graph TD
    A[JIRA API Call] -->|Passes through| B[Rate Limiter]
    B -->|Has tokens| C[Execute Call]
    B -->|No tokens| D[Wait]
    D -->|Token available| C
    
    subgraph Rate Limiter
        E[Token Bucket] -->|Refills| F[Available Tokens]
        F -->|Consumed by| B
    end
```

## Components

### 1. Rate Limiter Class

The `RateLimiter` class implements the token bucket algorithm:

```mermaid
classDiagram
    class RateLimiter {
        +int calls
        +int period
        +float tokens
        +datetime last_check
        +__init__(calls: int, period: int)
        +_add_tokens()
        +acquire() float
    }
```

### 2. Configuration

Rate limiting configuration in `JiraConfig`:

```mermaid
classDiagram
    class JiraConfig {
        +str jira_url
        +str jira_username
        +str jira_api_token
        +int rate_limit_calls
        +int rate_limit_period
    }
```

### 3. Integration Flow

```mermaid
sequenceDiagram
    participant Client as JIRA Client
    participant Limiter as Rate Limiter
    participant API as JIRA API

    Client->>Limiter: Request Token
    alt Has Available Tokens
        Limiter->>Client: Token Granted
        Client->>API: Make API Call
    else No Tokens Available
        Limiter->>Client: Wait Time
        Client->>Client: Wait
        Client->>Limiter: Retry Request
        Limiter->>Client: Token Granted
        Client->>API: Make API Call
    end
```

## Usage

The rate limiting is automatically applied to all JIRA API methods through a decorator:

```python
@rate_limited(calls=30, period=60)
def api_method():
    # Method implementation
```

## Configuration

Default configuration:
- 30 calls per 60-second period
- Configurable through environment variables or direct configuration

## Monitoring

The rate limiter includes logging for monitoring:
- Logs when rate limit is reached
- Includes wait times in logs
- Can be used for usage analysis

## Benefits

1. **Smooth Rate Limiting**
   - Token bucket algorithm provides smooth rate limiting
   - Allows bursts within limits
   - Prevents API quota exhaustion

2. **Flexibility**
   - Configurable limits
   - Per-instance rate limiting
   - Can be adjusted based on needs

3. **Monitoring**
   - Built-in logging
   - Wait time tracking
   - Usage patterns visible

## Example Usage Pattern

```mermaid
graph LR
    A[Normal Usage] -->|Under Limit| B[Immediate Execution]
    C[Burst Usage] -->|Over Limit| D[Gradual Processing]
    
    subgraph "Rate Limiting Behavior"
        B -->|Continues| E[Stable Operation]
        D -->|Smooths to| E
    end
```

## Implementation Details

The rate limiting is implemented in three main files:

1. `src/utils/rate_limit.py`
   - Core rate limiting implementation
   - Token bucket algorithm
   - Decorator implementation

2. `src/core/config.py`
   - Rate limiting configuration
   - Default values
   - Environment variable support

3. `src/core/client.py`
   - Integration with JIRA client
   - Automatic application to API methods
   - Runtime configuration 