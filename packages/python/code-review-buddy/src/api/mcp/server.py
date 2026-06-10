from mcp.server.fastmcp import FastMCP
from .tools import register_tools
from .router import register_resources

# Initialize FastMCP server
mcp = FastMCP(
    name="code-review-buddy",
    version="1.0.0",
    description="A local MCP server for repository inspection, diffing, and scan utilities"
)

# Register tools and resources
register_tools(mcp)
register_resources(mcp)

def main() -> None:
    """Run the FastMCP server using stdio transport."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
