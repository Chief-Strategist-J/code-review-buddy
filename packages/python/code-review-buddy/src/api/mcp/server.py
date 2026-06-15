from mcp.server.fastmcp import FastMCP
from .tools import register_tools
from .router import register_resources
from .prompts import register_prompts

# Initialize FastMCP server
mcp = FastMCP("code-review-buddy")

# Register tools, resources, and prompts
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

def main() -> None:
    """Run the FastMCP server using stdio transport."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
