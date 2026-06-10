# Code Review Buddy MCP Server

An internal Model Context Protocol (MCP) server that grants AI agents (e.g. Claude Desktop, Cursor) the ability to inspect git repositories locally. Built using Python and the `FastMCP` framework.

## Project Structure
The project follows the API-First and modular folder structure:
```
packages/python/code-review-buddy/
├── build/
│   ├── Dockerfile                  # Production container definitions
│   └── .gitkeep
├── contracts/
│   └── mcp/
│       ├── tools.json              # Contract defining tool signatures
│       └── changelog.md            # Changelog for contracts
├── src/
│   ├── api/
│   │   └── mcp/
│   │       ├── server.py           # Launch and transport initialization
│   │       ├── router.py           # Exposes Resources (project://readme)
│   │       └── tools.py            # Maps and registers tools (list_files, read_file, get_git_diff, etc.)
│   ├── features/
│   │   ├── fs/
│   │   │   └── service.py          # File listing and line-guarded reading logic
│   │   ├── git/
│   │   │   └── service.py          # Subprocess-based git diff and logs retrieval
│   │   └── scanner/
│   │       └── service.py          # TODO/FIXME scanner & large function heuristics
│   └── shared/
│       └── config.py               # Shared repo-root configurations
└── tests/
    └── unit/                       # Unit tests for features and services
```

## Features (MCP Tools & Resources)

### Tools
1. **`list_files`**: List all files in a directory relative to the repository root, optionally filtered by file extension.
2. **`read_file`**: Read file contents with safety guards (refuses files over 500 lines).
3. **`get_git_diff`**: Run `git diff` between two branches (truncated to 200 lines to keep it safe).
4. **`get_recent_commits`**: Fetch recent commit messages.
5. **`scan_todos`**: Recursively search directory for comment markers (`TODO`, `FIXME`, `HACK`, `XXX`).
6. **`find_large_functions`**: Identify functions/methods containing more than 40 lines of code.

### Resources
- **`project://readme`**: Exposes the repository's `README.md`.


## Installation & Setup

### Option A: Local Python Setup (Developer Mode)

1. **Prerequisites**:
   Ensure you have Python 3.10+ installed on your machine.

2. **Install dependencies**:
   ```bash
   cd packages/python/code-review-buddy
   pip install -e .
   ```

3. **Running the Server**:
   The server communicates over `stdio` transport. You can launch it using:
   ```bash
   fastmcp run src/api/mcp/server.py
   # Or using python directly if installed:
   python -m src.api.mcp.server
   ```

4. **Claude Desktop Integration**:
   Add the following configuration to your `claude_desktop_config.json` (typically located at `~/.config/Claude/claude_desktop_config.json` on Linux):
   ```json
   {
     "mcpServers": {
       "code-review-buddy": {
         "command": "python",
         "args": ["-m", "src.api.mcp.server"],
         "env": {
           "REPO_ROOT": "/home/btpl-lap-22/live/codeReview"
         },
         "cwd": "/home/btpl-lap-22/live/codeReview/packages/python/code-review-buddy"
       }
     }
   }
   ```

---

### Option B: Docker Setup (Team Distribution Mode)

1. **Build the Docker Image**:
   Build the image from the root of the sub-package:
   ```bash
   cd packages/python/code-review-buddy
   docker build -t code-review-buddy -f build/Dockerfile .
   ```

2. **Claude Desktop Integration**:
   Add the container execution command to your `claude_desktop_config.json`. Note that you must mount your target code repository to a volume in the container (e.g. `/project`) so the container has access to read files and run git:
   ```json
   {
     "mcpServers": {
       "code-review-buddy": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "-v",
           "/home/btpl-lap-22/live/codeReview:/project",
           "-e",
           "REPO_ROOT=/project",
           "code-review-buddy:latest"
         ]
       }
     }
   }
   ```

## Testing & Debugging (Without Claude Desktop)

### Option A: Browser (Deployed Render service)

Open the deployed URL directly — the MCP Inspector UI loads and auto-connects to the server:

```
https://mcp-code-review-buddy.onrender.com
```

No extra commands needed. The inspector connects automatically on page load.

> **Note:** The Render free plan spins down after inactivity. The first load may take ~30 seconds to cold-start.

### Option B: Local inspector against the deployed server

If you want to run the inspector UI locally pointed at the deployed SSE endpoint:

```bash
npx @modelcontextprotocol/inspector https://mcp-code-review-buddy.onrender.com/sse
```

> If you see `Proxy Server PORT IS IN USE at port 6277`, a previous inspector session is still running. Kill it with:
> ```bash
> lsof -ti:6277 | xargs kill
> ```

