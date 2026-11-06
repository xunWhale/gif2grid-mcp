import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="/home/fish/projects/gif2grid-mcp/.venv/bin/python",
        args=["-m", "gif2grid_mcp.server"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:", [t.name for t in tools.tools])
            result = await session.call_tool(
                "gif_to_grid",
                {"source": "/home/fish/projects/gif2grid/demo/motion.gif", "frames": 6},
            )
            kinds = [c.type for c in result.content]
            print("content kinds:", kinds)
            for c in result.content:
                if c.type == "text":
                    print("summary:", c.text[:200])

asyncio.run(main())
