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

    @mcp.resource("project://tools")
    def get_tools_contract() -> str:
        """Expose the tools.json contract file as a resource."""
        contract_path = Path(__file__).parent.parent.parent.parent / "contracts" / "mcp" / "tools.json"
        if not contract_path.is_file():
            return "tools.json contract file not found."
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading tools contract: {e}"

    @mcp.resource("project://prompts")
    def get_prompts_contract() -> str:
        """Expose the prompts.json contract file as a resource."""
        contract_path = Path(__file__).parent.parent.parent.parent / "contracts" / "mcp" / "prompts.json"
        if not contract_path.is_file():
            return "prompts.json contract file not found."
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading prompts contract: {e}"

    @mcp.resource("git://status")
    def get_git_status() -> str:
        """Expose local repository git status output."""
        import subprocess
        try:
            res = subprocess.run(["git", "status"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
            return res.stdout
        except Exception as e:
            return f"Error running git status: {e}"

    @mcp.resource("git://branch")
    def get_git_branches() -> str:
        """Expose local repository branches list."""
        import subprocess
        try:
            res = subprocess.run(["git", "branch", "-a"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
            return res.stdout
        except Exception as e:
            return f"Error running git branch: {e}"


