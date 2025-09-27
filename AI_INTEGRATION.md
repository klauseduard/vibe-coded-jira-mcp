# AI Coding Assistant Integration Guide

This guide shows how to integrate the JIRA MCP server with various AI coding assistants for seamless JIRA operations within your development workflow.

## 🎯 Available JIRA Tools

All integrations provide access to these JIRA operations:

### 📋 Project Management
- **`get_projects_tool`** - List JIRA projects with pagination
- **`search_issues_tool`** - Search issues using JQL with advanced filtering

### 🎫 Issue Operations
- **`get_issue_tool`** - Retrieve detailed issue information
- **`create_issue_tool`** - Create new issues with custom fields
- **`update_issue_tool`** - Update existing issues
- **`clone_issue_tool`** - Clone issues (helpful for templates)

### 💬 Comments & Tracking
- **`add_comment_tool`** - Add comments to issues
- **`get_comments_tool`** - Retrieve issue comments
- **`log_work_tool`** - Track time spent on issues

## 🔧 Prerequisites

### Environment Setup
Create a `.env` file with your JIRA credentials:
```bash
JIRA_URL=https://your-jira-instance.com
JIRA_USERNAME=your-username
JIRA_API_TOKEN=your-api-token
```

### Server Requirements
- **Python**: 3.12+
- **Framework**: FastMCP 2.0
- **Transport**: STDIO (MCP protocol)
- **Authentication**: JIRA API token

---

## 🤖 Claude Code Integration

### Setup

**Option 1: Project Configuration** (Recommended - for team collaboration):

1. **Find the absolute path** to this JIRA MCP server:
   ```bash
   # Navigate to the JIRA MCP server directory and get full path
   cd /path/to/vibe-coded-jira-mcp
   pwd
   # Example output: /home/username/tools/vibe-coded-jira-mcp
   ```

2. **In your project directory**, create the project-scoped configuration:
   ```bash
   # Navigate to YOUR project (not the MCP server directory)
   cd /path/to/your-project

   # Create .mcp.json in project root
   cat > .mcp.json << 'EOF'
   {
     "mcpServers": {
       "jira": {
         "command": "/home/username/tools/vibe-coded-jira-mcp/venv/bin/python3",
         "args": [
           "/home/username/tools/vibe-coded-jira-mcp/simple_jira.py",
           "--transport",
           "stdio"
         ],
         "cwd": "/home/username/tools/vibe-coded-jira-mcp",
         "env": {}
       }
     }
   }
   EOF
   ```
   **⚠️ Replace `/home/username/tools/vibe-coded-jira-mcp` with your actual path from step 1**

3. **Verify Claude Code recognizes it**:
   - Open Claude Code in your project directory
   - Claude Code will ask for approval to use the project-scoped server
   - Run `/mcp` command to see if the JIRA server appears
   - If not found, run `/doctor` for troubleshooting

**Option 2: Use Claude Code's built-in MCP commands**:

```bash
# Navigate to your project directory
cd /path/to/your-project

# Add project-scoped MCP server
claude mcp add jira --scope project "/home/username/tools/vibe-coded-jira-mcp/venv/bin/python3" "/home/username/tools/vibe-coded-jira-mcp/simple_jira.py" "--transport" "stdio"
```
**⚠️ Replace `/home/username/tools/vibe-coded-jira-mcp` with your actual path**

This creates a `.mcp.json` file in your project root automatically.

**Option 3: Helper Script** (Easiest):

Use the included helper script to automatically configure Claude Code:

```bash
# Navigate to the JIRA MCP server directory
cd /path/to/vibe-coded-jira-mcp

# Add to specific project (recommended)
./add-to-claude.sh /path/to/your-project

# Add to current directory
./add-to-claude.sh $(pwd)

# Add globally (not recommended)
./add-to-claude.sh --global

# Show help
./add-to-claude.sh --help
```

The script automatically detects the MCP server location and creates the correct configuration.

**Option 4: Global Configuration** (not recommended):

1. **Find the absolute path** to this JIRA MCP server:
   ```bash
   cd /path/to/vibe-coded-jira-mcp && pwd
   ```

2. **Create global config using ~/.claude.json**:
   ```bash
   # Replace with your actual path
   MCP_PATH="/home/username/tools/vibe-coded-jira-mcp"

   cat > ~/.claude.json << EOF
   {
     "mcp_servers": {
       "jira": {
         "command": "$MCP_PATH/venv/bin/python3",
         "args": ["$MCP_PATH/simple_jira.py", "--transport", "stdio"],
         "cwd": "$MCP_PATH"
       }
     }
   }
   EOF
   ```

### Verification Steps

1. **Check MCP server status**:
   ```bash
   # In Claude Code, run:
   /mcp
   ```
   You should see "jira" listed as an available server.

2. **Test a simple operation**:
   ```bash
   # In Claude Code, try:
   /mcp call jira get_projects_tool
   ```

3. **If server not found**:
   ```bash
   # Run diagnostics:
   /doctor
   ```

### Usage Examples
```
"Search for all high priority bugs in the EHEALTHDEV project"
"Create a new task for implementing user authentication"
"Add a comment to issue PROJ-123 explaining the current status"
"Show me all issues assigned to me that were created in the last week"
```

### Version Control Considerations

**Should you commit `.mcp.json` to version control?**

✅ **Commit if:**
- Your team uses the same JIRA MCP server installation
- You want consistent tooling across team members
- Paths are standardized (e.g., using environment variables)

❌ **Don't commit if:**
- Each developer has different MCP server locations
- This is personal tooling setup
- Paths contain sensitive information

**Alternative for teams with different setups:**
```json
{
  "mcpServers": {
    "jira": {
      "command": "${JIRA_MCP_PATH}/venv/bin/python3",
      "args": ["${JIRA_MCP_PATH}/simple_jira.py", "--transport", "stdio"],
      "cwd": "${JIRA_MCP_PATH}",
      "env": {}
    }
  }
}
```
Each developer sets `JIRA_MCP_PATH` environment variable to their installation path.

### Troubleshooting

- **"No MCP servers configured"**: Ensure `.mcp.json` is in your project root or global config exists
- **Server fails to start**: Check that the command path in `.mcp.json` is correct and executable
- **JIRA connection issues**: Verify your `.env` file has correct JIRA credentials
- **Permission denied**: Make sure the MCP server has appropriate file permissions

---

## 🎯 Cursor IDE Integration

**Status**: ✅ **Originally designed for Cursor** - This MCP server was specifically built for Cursor IDE integration.

### Setup Options

1. **Project Configuration** (Recommended):
   ```json
   // mcp.json (legacy format - already exists in project)
   {
     "mcpServers": {
       "jira": {
         "command": "python3",
         "args": [
           "/home/klaus/workspace/vibe-coded-jira-mcp/simple_jira.py",
           "--transport",
           "stdio"
         ],
         "cwd": "/home/klaus/workspace/vibe-coded-jira-mcp",
         "env": {
           "PYTHONPATH": "/home/klaus/workspace/vibe-coded-jira-mcp",
           "PATH": "/home/klaus/workspace/vibe-coded-jira-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin"
         }
       }
     }
   }
   ```

2. **Modern Project Configuration**:
   ```json
   // .cursor/mcp.json or cursor-mcp.json
   {
     "servers": {
       "jira": {
         "command": "./venv/bin/python3",
         "args": ["simple_jira.py", "--transport", "stdio"],
         "cwd": ".",
         "env": {
           "PYTHONPATH": "."
         }
       }
     }
   }
   ```

3. **Global Cursor Settings**:
   ```json
   // Cursor settings.json
   {
     "mcp.servers": {
       "jira": {
         "command": "/absolute/path/to/venv/bin/python3",
         "args": ["/absolute/path/to/simple_jira.py", "--transport", "stdio"]
       }
     }
   }
   ```

### Historical Context
- **Original Purpose**: This server was "vibe-coded" specifically for Cursor IDE
- **Proven Integration**: Successfully replaces a previous JIRA MCP server that "failed to init in Cursor"
- **Architecture Designed**: Built with Cursor's AI features and MCP protocol in mind

### Usage Examples
- **AI Chat Integration**: Use Cursor's AI chat to interact with JIRA tools
- **Context Awareness**: Leverage Cursor's code context for intelligent issue references
- **Workflow Integration**: Seamlessly integrate JIRA operations into code review workflows
- **Real-time JIRA Data**: Access live JIRA data through Cursor's AI features

---

## 🧠 Codex CLI Integration

Codex CLI 0.5+ ships with experimental MCP client support. Register this server once and every Codex session can call the JIRA tools.

### Setup
1. **Prepare the server**
   ```bash
   cd /path/to/vibe-coded-jira-mcp
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   Ensure your `.env` contains valid `JIRA_URL`, `JIRA_USERNAME`, and `JIRA_API_TOKEN` values.

2. **Add the MCP server to Codex** (writes to the Codex config directory):
   ```bash
   codex mcp add jira ./venv/bin/python3 simple_jira.py --transport stdio
   ```
   - Use `./venv/bin/python3` on macOS/Linux or `venv\Scripts\python.exe` on Windows.
   - Add repeated `--env KEY=VALUE` flags if you want Codex to inject environment variables directly instead of using `.env`.
   - Run `codex mcp list` to confirm the server is registered. `codex mcp get jira --json` prints the stored configuration.

### Verification
```bash
codex mcp list             # Should show "jira"
codex mcp get jira --json  # Inspect the command Codex will run
```
Start a Codex session inside your project (`codex --cd /path/to/project`). Ask Codex to "call the jira MCP server" or request specific tools, e.g., "Use jira.search_issues_tool to find open bugs". The session transcript will show MCP tool calls once the server is reachable.

### Maintenance
- Update the entry after virtualenv moves: `codex mcp add jira ...` (the command overwrites the existing record).
- Remove the integration at any time: `codex mcp remove jira`.
- Tail logs during debugging with `codex --log-level debug ...` and watch this repository's `logs/` directory when using `run-jira-mcp.sh`.

---

## 🛠 Testing & Troubleshooting

### Verify Server Works
```bash
# Test the server directly
./venv/bin/python3 simple_jira.py --help

# Test with MCP client
source venv/bin/activate
python3 test_jira_operations.py
```

### Common Issues

#### "JIRA configuration incomplete"
- Check `.env` file exists and has all required variables
- Verify environment variables are loaded correctly

#### "Command not found"
- Verify Python virtual environment path in configuration
- Ensure `simple_jira.py` is executable

#### "Connection refused"
- Test JIRA URL accessibility: `curl -I $JIRA_URL`
- Verify API token permissions in JIRA
- Check network connectivity to JIRA instance

#### MCP Protocol Issues
- Ensure FastMCP dependencies are installed: `pip install -r requirements.txt`
- Check server logs for detailed error messages
- Verify MCP client compatibility

### Debug Commands
```bash
# Check environment
env | grep JIRA

# Test JIRA connection
python3 -c "from src.core.config import JiraConfig; print(JiraConfig())"

# Validate server startup
timeout 5s ./venv/bin/python3 simple_jira.py --transport stdio
```

---

## 📚 Additional Resources

- **Technical Architecture**: See `ARCHITECTURE.md` for system design
- **Development Guide**: See `CLAUDE.md` for contributing
- **Feature Roadmap**: See `IMPLEMENTATION_PLAN.md` for upcoming features
- **Project Overview**: See `README.md` for general information

---

## 🚀 Getting Started

1. **Clone and setup** this repository
2. **Configure** your preferred AI assistant using the sections above
3. **Test** the integration with simple operations
4. **Explore** advanced features like issue cloning and time tracking

🤖 **Ready to enhance your JIRA workflow with AI assistance!**
