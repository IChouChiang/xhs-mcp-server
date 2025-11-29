import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# Server Parameters
server_params = StdioServerParameters(
    command="node",
    args=["C:\\Users\\63091\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"],
    env=None
)

async def run_debug():
    print("Connecting to MCP Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected!")

            # Step 1: Navigate (New Window)
            print("\n--- Step 1: Navigate to XHS (New Window) ---")
            try:
                # We use newWindow=True to ensure we don't mess with the current context
                result = await session.call_tool("chrome_navigate", arguments={"url": "https://www.xiaohongshu.com", "newWindow": True})
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error calling chrome_navigate: {e}")

            # Wait a bit for the window to open
            await asyncio.sleep(2)

            # Step 2: List Tabs
            print("\n--- Step 2: List Tabs ---")
            try:
                result = await session.call_tool("get_windows_and_tabs", arguments={})
                if result.content:
                    content_text = result.content[0].text
                    print(f"Raw Content: {content_text[:200]}...") 
                    
                    # Try to parse JSON to find our new tab
                    try:
                        data = json.loads(content_text)
                        # The structure seems to be stringified JSON inside 'text' sometimes, or direct. 
                        # Based on previous logs: "{\"success\":true...}"
                        if isinstance(data, str):
                             data = json.loads(data)
                        
                        print(f"\nParsed Data Keys: {data.keys()}")
                    except:
                        print("Could not parse JSON content.")
            except Exception as e:
                print(f"Error calling get_windows_and_tabs: {e}")

if __name__ == "__main__":
    asyncio.run(run_debug())
