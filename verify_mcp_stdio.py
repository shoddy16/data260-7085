"""Run actual MCP STDIO tool calls and save their machine-readable results."""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "hw05" / "raw" / "mcp_stdio_results.json"


async def run_server(script: str, calls: list[tuple[str, dict]]):
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / script)],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = [tool.name for tool in listed.tools]
            outputs = []
            for name, arguments in calls:
                try:
                    result = await session.call_tool(name, arguments)
                    content = [getattr(item, "text", str(item)) for item in result.content]
                    parsed = None
                    if len(content) == 1:
                        try:
                            parsed = json.loads(content[0])
                        except json.JSONDecodeError:
                            pass
                    outputs.append({
                        "tool": name,
                        "input": arguments,
                        "is_error": result.isError,
                        "content": content,
                        "parsed": parsed,
                    })
                except Exception as exc:
                    outputs.append({"tool": name, "input": arguments, "is_error": True,
                                    "exception": f"{type(exc).__name__}: {exc}"})
            return {"server_script": script, "discovered_tools": names, "calls": outputs}


async def main():
    domain = await run_server("domain_mcp_server.py", [
        ("search", {"query": "Restaurant 1", "limit": 2}),
        ("search", {"query": " ", "limit": 5}),
        ("detail_lookup", {"inspection_id": 4}),
        ("detail_lookup", {"inspection_id": 0}),
        ("aggregate", {"group_by": "category"}),
        ("aggregate", {"group_by": "unknown"}),
    ])
    meals = await run_server("meals_server.py", [
        ("search_meals_by_name", {"query": "Arrabiata", "limit": 2}),
        ("meals_by_ingredient", {"ingredient": "chicken", "limit": 2}),
        ("random_meal", {}),
        ("meal_details", {"id": 52772}),
    ])
    payload = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "transport": "STDIO, MCP Python ClientSession",
        "results": [domain, meals],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for server in (domain, meals):
        print(server["server_script"], "tools:", ", ".join(server["discovered_tools"]))
        for call in server["calls"]:
            print(call["tool"], "ERROR" if call["is_error"] else "OK")
    print(f"Saved {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
