import asyncio
from fastmcp import Client

async def main():
    async with Client("http://127.0.0.1:8001/mcp") as client:
        await client.ping()
        tools = await client.list_tools()
        print("TOOLS:", [t.name for t in tools])

        result = await client.call_tool(
            "search_candidates",
            {"cargo": "SENADOR", "uf": "SP", "q": ""}
        )
        print("RESULT:", result)

asyncio.run(main())
