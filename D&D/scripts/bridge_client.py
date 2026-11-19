"""Call the real local MCP server when the host has not reloaded its tools yet.

Run with the bridge virtualenv's Python (which contains the MCP SDK).
No dashboard token or HTTP port is required for this stdio transport.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def connect(agent: str = "codex"):
    if agent not in ("codex", "antigravity"):
        raise ValueError("Use codex or antigravity as the agent identity")
    config = json.loads((PROJECT / ".agents" / "mcp_config.json").read_text(encoding="utf-8-sig"))
    entry = config["mcpServers"]["arcanum-bridge"]
    args = list(entry["args"])
    args[args.index("--agent") + 1] = agent
    params = StdioServerParameters(command=entry["command"], args=args, cwd=str(PROJECT))
    async with asyncio.timeout(40):
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                yield session


async def call(session: ClientSession, tool: str, arguments: dict):
    result = await session.call_tool(tool, arguments)
    if result.isError:
        raise RuntimeError("; ".join(getattr(item, "text", "") for item in result.content))
    data = result.structuredContent
    if data is not None:
        return data.get("result", data)
    texts = [item.text for item in result.content if hasattr(item, "text")]
    if not texts:
        return []
    if len(texts) == 1:
        return json.loads(texts[0])
    return [json.loads(text) for text in texts]


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", help="MCP tool name, e.g. bridge_health")
    parser.add_argument("--arguments", default="{}", help="JSON object of tool arguments")
    parser.add_argument("--agent", choices=("codex", "antigravity"), default="codex")
    options = parser.parse_args()
    arguments = json.loads(options.arguments)
    if not isinstance(arguments, dict):
        parser.error("--arguments must be a JSON object")
    async with connect(options.agent) as session:
        result = await call(session, options.tool, arguments)
        print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
