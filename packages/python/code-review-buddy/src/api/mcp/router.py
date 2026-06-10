import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from ...shared.config import REPO_ROOT

def register_resources(mcp: FastMCP) -> None:
    """Register all MCP resources on the FastMCP instance.
    
    Args:
        mcp: The FastMCP server instance.
    """
    
    @mcp.resource("project://readme")
    def get_readme() -> str:
        """Expose the repository's README.md as a resource."""
        readme_path = Path(REPO_ROOT) / "README.md"
        if not readme_path.is_file():
            # If README.md doesn't exist, return a descriptive message or try to read readme.md
            lower_readme = Path(REPO_ROOT) / "readme.md"
            if lower_readme.is_file():
                readme_path = lower_readme
            else:
                return "README.md file not found in the repository root."
        
        try:
            with open(readme_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"Error reading README.md: {str(e)}"

