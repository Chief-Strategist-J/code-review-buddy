from typing import Any
from mcp.server.fastmcp import FastMCP
from ...shared.config import REPO_ROOT
from ...features.fs.service import FileSystemService
from ...features.git.service import GitService
from ...features.scanner.service import ScannerService

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
