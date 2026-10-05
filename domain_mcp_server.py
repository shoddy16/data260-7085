import logging
import sys

from mcp.server.fastmcp import FastMCP

from domain.inspection_tools import default_inspection_tools


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

mcp = FastMCP("s7085-restaurant-inspections")


@mcp.tool()
def search(query: str, limit: int = 5) -> dict:
    """Search restaurant inspections by restaurant, location, category, or text."""
    return default_inspection_tools.search(query, limit)


@mcp.tool()
def detail_lookup(inspection_id: int) -> dict:
    """Return one inspection by its numeric database ID."""
    return default_inspection_tools.detail_lookup(inspection_id)


@mcp.tool()
def aggregate(group_by: str = "category") -> dict:
    """Count inspections and average scores by category or restaurant."""
    return default_inspection_tools.aggregate(group_by)


if __name__ == "__main__":
    mcp.run(transport="stdio")
