# Assignment 1 — Reflection

## 1. What MCP enabled that plain prompting couldn't
MCP enables real-time, bidirectional connection to the developer's local machine and tools. With plain prompting, a user must copy and paste diffs, file lists, and file contents manually, which is slow and error-prone. MCP gives the LLM active context-awareness, letting it execute complex pipelines (e.g., list files, find TODOs, diff branches, check large functions) on the fly without human intervention.

## 2. A moment of surprise during tool use
During testing, Claude was able to intelligently chain multiple tools: it first read the README.md resource (`project://readme`) to understand project objectives, then automatically scanned for TODOs (`scan_todos`) in the source folders, and correlated the issues it found with the project gaps described in the README, doing all of this in a single turn.

## 3. Security risks and production mitigations
- **Risk**: The server has access to run git subprocesses and read filesystem files. If branch names or input paths contain shell metacharacters, it could lead to command/path injection.
- **Mitigation**:
  - Validated all branch names using strict regexes allowing only safe alphanumeric/punctuation characters.
  - Implemented strict path resolution with `is_relative_to` against the configured repository root to prevent directory traversal attacks (e.g., trying to read `/etc/passwd`).
  - Added line-count constraints to avoid denial-of-service/memory overflow when reading large files.

## 4. Improvements given another week
If given another week, I would integrate automated code style checkers (like `ruff` or `flake8` APIs) directly as tools to provide instant style feedback in PR descriptions, and build real-time interactive dashboards showing code quality metrics.
