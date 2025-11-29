import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent_core import create_mcp_tools, build_agent_graph
from session_manager import inject_session

# --- Configuration ---
# Use the path that was working in web_ui.py
SERVER_PARAMS = StdioServerParameters(
    command="node",
    args=["C:\\Users\\63091\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"],
    env=None
)

async def main():
    print("=== MCP Chrome Agent (CLI) ===")
    
    # 1. Connect to MCP Server
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to MCP Server.")

            # 2. Inject Session (Cookies)
            print("Injecting session cookies...")
            await inject_session(session)

            # 3. Create Tools & Agent
            print("Creating tools...")
            tools = await create_mcp_tools(session)
            agent = build_agent_graph(tools)
            print(f"Agent ready with {len(tools)} tools.")

            # 4. Interactive Loop
            print("\nType your command (or 'quit' to exit):")
            while True:
                try:
                    user_input = input("> ").strip()
                    if user_input.lower() in ["quit", "exit"]:
                        break
                    if not user_input:
                        continue

                    print("\n--- Agent Running ---")
                    
                    # Run the agent
                    async for event in agent.astream(
                        {"messages": [("user", user_input)]},
                        config={"recursion_limit": 150}
                    ):
                        # Print agent's thought process (messages)
                        if "agent" in event:
                            msg = event["agent"]["messages"][0]
                            print(f"\n[Agent]: {msg.content}")
                        
                        # Print tool outputs
                        if "tools" in event:
                            for msg in event["tools"]["messages"]:
                                print(f"\n[Tool Output]: {msg.content[:200]}...")

                    print("\n--- Done ---")

                except KeyboardInterrupt:
                    print("\nInterrupted.")
                    break
                except Exception as e:
                    print(f"\nError: {e}")

if __name__ == "__main__":
    # Windows asyncio fix
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
