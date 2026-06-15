from typing import Any

from mcp.server.fastmcp import FastMCP

from ...features.fs.service import FileSystemService
from ...features.git.service import GitService
from ...features.scanner.service import ScannerService
from ...shared.config import REPO_ROOT


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools on the FastMCP instance.
    
    Args:
        mcp: The FastMCP server instance.

    """
    fs_service = FileSystemService(REPO_ROOT)
    git_service = GitService(REPO_ROOT)
    scanner_service = ScannerService(REPO_ROOT)

    @mcp.tool(name="list_files")
    def list_files(directory: str, extension: str | None = None) -> list[str]:
        """List all files in a directory relative to the repository root.
        
        Args:
            directory: Relative path to the directory from the repository root.
            extension: Optional file extension filter, e.g., '.py', '.java', '.ts'.

        """
        try:
            return fs_service.list_files(directory, extension)
        except ValueError as e:
            # Map validation errors to clear messages
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error listing files: {e}")

    @mcp.tool(name="read_file")
    def read_file(file_path: str) -> str:
        """Read the content of a file. Refuses to read files over 500 lines.
        
        Args:
            file_path: Path to the file to read relative to repository root.

        """
        try:
            return fs_service.read_file(file_path)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error reading file: {e}")

    @mcp.tool(name="get_git_diff")
    def get_git_diff(base_branch: str = "main", compare_branch: str = "HEAD") -> str:
        """Get the git diff between a base branch and compare branch. Truncated if large.
        
        Args:
            base_branch: Base branch to compare from (default: 'main').
            compare_branch: Compare branch to compare to (default: 'HEAD').

        """
        try:
            return git_service.get_git_diff(base_branch, compare_branch)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error getting git diff: {e}")

    @mcp.tool(name="get_recent_commits")
    def get_recent_commits(count: int = 5) -> list[dict[str, str]]:
        """Get recent git commits from the repository.
        
        Args:
            count: Number of recent commits to fetch (1-20, default: 5).

        """
        try:
            return git_service.get_recent_commits(count)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error getting recent commits: {e}")

    @mcp.tool(name="scan_todos")
    def scan_todos(directory: str) -> list[dict[str, Any]]:
        """Scan a directory recursively for files containing TODO, FIXME, HACK, XXX.
        
        Args:
            directory: Relative directory path to scan from repository root.

        """
        try:
            return scanner_service.scan_todos(directory)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error scanning TODOs: {e}")

    @mcp.tool(name="find_large_functions")
    def find_large_functions(file_path: str) -> list[dict[str, Any]]:
        """Identify large functions (over 40 lines) in a file using a simple heuristic.
        
        Args:
            file_path: Relative path to the file from the repo root.

        """
        try:
            return scanner_service.find_large_functions(file_path)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error finding large functions: {e}")

    @mcp.tool(name="write_file")
    def write_file(file_path: str, content: str) -> str:
        """Write content to a file, creating parent directories if necessary.
        
        Args:
            file_path: Relative path to the file from the repo root.
            content: The text content to write.

        """
        try:
            return fs_service.write_file(file_path, content)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error writing file: {e}")

    @mcp.tool(name="update_file")
    def update_file(file_path: str, target_text: str, replacement_text: str) -> str:
        """Update a file by replacing target_text with replacement_text.
        
        Args:
            file_path: Relative path to the file from the repo root.
            target_text: The exact string to find in the file.
            replacement_text: The replacement content.

        """
        try:
            return fs_service.update_file(file_path, target_text, replacement_text)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error updating file: {e}")

    @mcp.tool(name="commit_and_push_file")
    def commit_and_push_file(file_path: str, commit_message: str) -> str:
        """Stage, commit, and push a specific file to GitHub.
        
        Args:
            file_path: Relative path to the file from the repo root.
            commit_message: The git commit message.

        """
        try:
            return git_service.commit_and_push_file(file_path, commit_message)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error committing/pushing file: {e}")

    @mcp.tool(name="write_and_publish_file")
    def write_and_publish_file(file_path: str, content: str, commit_message: str) -> str:
        """Write content to a file, stage it, commit it, and push it in a single step-by-step workflow.
        
        Args:
            file_path: Relative path to the file from the repo root.
            content: The text content to write.
            commit_message: The git commit message.
        """
        try:
            write_res = fs_service.write_file(file_path, content)
            git_res = git_service.commit_and_push_file(file_path, commit_message)
            return f"Step 1: {write_res}\nStep 2: {git_res}"
        except ValueError as e:
            raise ValueError(f"Workflow validation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Workflow execution failed: {e}")

    @mcp.tool(name="update_and_publish_file")
    def update_and_publish_file(file_path: str, target_text: str, replacement_text: str, commit_message: str) -> str:
        """Update a file by replacing target_text with replacement_text, stage it, commit it, and push it in a single step-by-step workflow.
        
        Args:
            file_path: Relative path to the file from the repo root.
            target_text: The exact string to find in the file.
            replacement_text: The replacement content.
            commit_message: The git commit message.
        """
        try:
            update_res = fs_service.update_file(file_path, target_text, replacement_text)
            git_res = git_service.commit_and_push_file(file_path, commit_message)
            return f"Step 1: {update_res}\nStep 2: {git_res}"
        except ValueError as e:
            raise ValueError(f"Workflow validation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Workflow execution failed: {e}")

    @mcp.tool(name="get_advanced_diff")
    def get_advanced_diff(base_branch: str = "main", compare_branch: str = "HEAD", word_diff: bool = False, unified: int = 3, show_stat: bool = False, file_path: str | None = None) -> str:
        """Show advanced diff between branches with options for word diff, stats, unified context, and file filters."""
        try:
            return git_service.get_advanced_diff(base_branch, compare_branch, word_diff, unified, show_stat, file_path)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error getting advanced diff: {e}")

    @mcp.tool(name="get_branch_history")
    def get_branch_history(since: str | None = None, limit: int = 30) -> str:
        """Show a visual log graph of commits/branches history."""
        try:
            return git_service.get_branch_history(since, limit)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error getting branch history: {e}")

    @mcp.tool(name="get_file_history")
    def get_file_history(file_path: str, function_name: str | None = None, search_query: str | None = None, is_regex: bool = False) -> str:
        """Show commits modifying a specific file, with optional function filter (-L) or change query (-S or -G)."""
        try:
            return git_service.get_file_history(file_path, function_name, search_query, is_regex)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error getting file history: {e}")

    @mcp.tool(name="get_file_blame")
    def get_file_blame(file_path: str, line_range: str | None = None, ignore_whitespace: bool = True) -> str:
        """Show line-by-line git blame annotation of a file."""
        try:
            return git_service.get_file_blame(file_path, line_range, ignore_whitespace)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error getting file blame: {e}")

    @mcp.tool(name="inspect_commit")
    def inspect_commit(commit_sha: str) -> dict[str, str]:
        """Inspect a specific commit for metadata, file stats, and diff patch."""
        try:
            return git_service.inspect_commit(commit_sha)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error inspecting commit: {e}")

    @mcp.tool(name="check_merge_safety")
    def check_merge_safety(base_branch: str, feature_branch: str) -> dict[str, Any]:
        """Check if feature branch can merge cleanly into base branch and count commit difference."""
        try:
            return git_service.check_merge_safety(base_branch, feature_branch)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error checking merge safety: {e}")

    @mcp.tool(name="get_code_churn")
    def get_code_churn(limit: int = 15) -> dict[str, Any]:
        """Analyze repository history to identify top code churn risk files and totals."""
        try:
            return git_service.get_code_churn(limit)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error analyzing code churn: {e}")

    @mcp.tool(name="analyze_churn_risk")
    def analyze_churn_risk(base_branch: str = "main", compare_branch: str = "HEAD", file_path: str | None = None) -> dict[str, Any]:
        """Compute advanced churn risk scores, authorship entropy, or logical couplings."""
        try:
            return git_service.analyze_churn_risk(base_branch, compare_branch, file_path)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error running churn risk analysis: {e}")

    @mcp.tool(name="detect_code_similarity")
    def detect_code_similarity(base_branch: str = "main", compare_branch: str = "HEAD", similarity_threshold: int = 50, target_file: str | None = None) -> str:
        """Find copy-pasted code blocks, rename thresholds, or structural similarity across branches."""
        try:
            return git_service.detect_code_similarity(base_branch, compare_branch, similarity_threshold, target_file)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error detecting similarity: {e}")

    @mcp.tool(name="get_semantic_diff")
    def get_semantic_diff(base_branch: str = "main", compare_branch: str = "HEAD", file_pattern: str = "*") -> dict[str, Any]:
        """Extract API definition/signature changes and complexity proxy additions."""
        try:
            return git_service.get_semantic_diff(base_branch, compare_branch, file_pattern)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error fetching semantic diff: {e}")

    @mcp.tool(name="query_object_graph")
    def query_object_graph(action: str, param1: str, param2: str | None = None) -> Any:
        """Query Git object graph, ancestry paths, reflogs, reachabilities, or blob matches."""
        try:
            return git_service.query_object_graph(action, param1, param2)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error querying object graph: {e}")

    @mcp.tool(name="get_diff_with_algorithm")
    def get_diff_with_algorithm(base_branch: str = "main", compare_branch: str = "HEAD", algorithm: str = "histogram", pathspecs: list[str] | None = None) -> str:
        """Fetch diff between branches utilizing specific diff algorithms (patience, histogram, etc.) and file specs."""
        try:
            return git_service.get_diff_with_algorithm(base_branch, compare_branch, algorithm, pathspecs)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error getting diff: {e}")

    @mcp.tool(name="search_repository")
    def search_repository(query: str, search_all: bool = False, file_pattern: str = "*", and_query: str | None = None) -> list[str]:
        """Perform multidimensional grep searches inside current files, full history, or with AND combinations."""
        try:
            return git_service.search_repository(query, search_all, file_pattern, and_query)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error searching repository: {e}")

    @mcp.tool(name="run_pr_audit")
    def run_pr_audit(base_branch: str = "main", compare_branch: str = "HEAD", file_pattern: str = "*") -> dict[str, Any]:
        """Perform a full machine-auditable report of a PR branch (stats, API changes, churn, secrets, complexity)."""
        try:
            return git_service.run_pr_audit(base_branch, compare_branch, file_pattern)
        except ValueError as e:
            raise ValueError(f"Invalid parameters: {e}")
        except Exception as e:
            raise RuntimeError(f"Internal error running PR audit: {e}")





