#!/bin/bash
# Helper script to add JIRA MCP configuration to Claude Code

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [project-directory] [--global]"
    echo "This will add JIRA MCP configuration to Claude Code"
    echo ""
    echo "Options:"
    echo "  project-directory  Add to .mcp.json in specified project (recommended)"
    echo "  --global          Add to ~/.claude/mcp_servers.json"
    echo ""
    echo "Examples:"
    echo "  $0 ~/my-project      # Add to ~/my-project/.mcp.json"
    echo "  $0 \$(pwd)            # Add to current directory"
    echo "  $0 --global          # Add to ~/.claude/mcp_servers.json"
    exit 0
fi

MCP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$1" = "--global" ]; then
    # Use ~/.claude/mcp_servers.json (global)
    mkdir -p "$HOME/.claude"
    CONFIG_FILE="$HOME/.claude/mcp_servers.json"

    cat > "$CONFIG_FILE" << EOL
{
  "jira": {
    "command": "$MCP_DIR/venv/bin/python3",
    "args": [
      "$MCP_DIR/simple_jira.py",
      "--transport",
      "stdio"
    ],
    "cwd": "$MCP_DIR"
  }
}
EOL

    echo "✅ JIRA MCP configuration added to $CONFIG_FILE (global)"
    echo ""
    echo "Next steps:"
    echo "1. Open Claude Code in any project directory"
    echo "2. Run '/mcp' to verify the JIRA server is available"
else
    # Project-scoped configuration (recommended)
    if [ -z "$1" ]; then
        echo "❌ Error: Please specify a project directory"
        echo "Usage: $0 /path/to/your-project"
        echo "Example: $0 \$(pwd)"
        exit 1
    fi

    PROJECT_DIR="$1"

    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "❌ Error: Directory '$PROJECT_DIR' does not exist"
        exit 1
    fi

    CONFIG_FILE="$PROJECT_DIR/.mcp.json"

    cat > "$CONFIG_FILE" << EOL
{
  "mcpServers": {
    "jira": {
      "command": "$MCP_DIR/venv/bin/python3",
      "args": [
        "$MCP_DIR/simple_jira.py",
        "--transport",
        "stdio"
      ],
      "cwd": "$MCP_DIR",
      "env": {}
    }
  }
}
EOL

    echo "✅ JIRA MCP configuration added to $CONFIG_FILE"
    echo ""
    echo "Next steps:"
    echo "1. cd $PROJECT_DIR"
    echo "2. Open Claude Code in that directory"
    echo "3. Approve the project-scoped server when prompted"
    echo ""
    echo "Optional (for team collaboration):"
    echo "- Add to version control: git add .mcp.json && git commit -m 'Add JIRA MCP configuration'"
    echo "- Or keep it local if this is personal use only"
fi

echo "5. Run '/mcp' to verify the JIRA server is available"
echo "6. Try: 'List all JIRA projects' or 'Search for recent issues'"