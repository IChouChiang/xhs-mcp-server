import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

server_params = StdioServerParameters(
    command="node",
    args=["C:\\Users\\63091\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"],
    env=None
)

async def list_tools():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Schema: {tool.inputSchema}")
                print("-" * 20)

if __name__ == "__main__":
    asyncio.run(list_tools())
