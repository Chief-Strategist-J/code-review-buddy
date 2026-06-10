from mcp.server.fastmcp import FastMCP
from .tools import register_tools
from .router import register_resources

# Initialize FastMCP server
mcp = FastMCP("code-review-buddy")

# Register tools and resources
register_tools(mcp)
register_resources(mcp)

def main() -> None:
    """Run the FastMCP server using stdio transport."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
