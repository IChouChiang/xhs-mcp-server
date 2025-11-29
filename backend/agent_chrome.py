import asyncio
import sys
import os
import uuid
import time
import msvcrt  # Windows only, for non-blocking input
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.checkpoint.memory import MemorySaver

from agent_core import create_mcp_tools, build_agent_graph
from session_manager import inject_session

# --- Configuration ---
SERVER_PARAMS = StdioServerParameters(
    command="node",
    args=["C:\\Users\\63091\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"],
    env=None
)

async def main():
    print("=== MCP Chrome Agent (CLI - Interactive) ===")
    
    try:
        # 1. Connect to MCP Server
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected to MCP Server.")

                # 2. Inject Session (Cookies)
                print("Injecting session cookies...")
                await inject_session(session)

                # 3. Create Tools & Agent with Checkpointer
                print("Creating tools...")
                tools = await create_mcp_tools(session)
                
                # Initialize Memory for Human-in-the-loop
                memory = MemorySaver()
                agent = build_agent_graph(tools, checkpointer=memory)
                
                print(f"Agent ready with {len(tools)} tools.")
                print("Interactive Mode: The agent will PAUSE before executing tools.")
                print("  - Press 'y' to approve.")
                print("  - Type 'auto' to switch to Auto-Pilot mode.")
                print("  - Type a new command to redirect.")
                print("  - Press 'n' to stop.")
                print("  - Type 'quit' to exit the program.")

                # 4. Interactive Loop
                thread_id = str(uuid.uuid4())
                config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 150}
                auto_mode = False

                print("\nType your command (or 'quit' to exit):")
                while True:
                    user_input = input("> ").strip()
                    if user_input.lower() in ["quit", "exit"]:
                        print("Exiting...")
                        os._exit(0) # Force exit immediately
                    
                    if not user_input:
                        continue

                    print("\n--- Agent Running ---")
                    
                    # Initial Run
                    async for event in agent.astream(
                        {"messages": [("user", user_input)]},
                        config=config
                    ):
                        if "agent" in event:
                            msg = event["agent"]["messages"][0]
                            print(f"\n[Agent]: {msg.content}")
                            
                            # Check if tool calls exist
                            if msg.tool_calls:
                                print(f"\n[PAUSED] Agent wants to call: {[t['name'] for t in msg.tool_calls]}")

                    # Handle Interrupts (Human-in-the-loop)
                    while True:
                        # Check if we are paused
                        snapshot = agent.get_state(config)
                        if not snapshot.next:
                            print("\n--- Task Completed ---")
                            break
                        
                        # Determine Approval
                        approval = ""
                        
                        if auto_mode:
                            print(f"\n[Auto-Pilot] Running... (Press 'p' to pause)")
                            # Wait briefly to allow interruption
                            paused_by_user = False
                            for _ in range(5): # 0.5 seconds wait
                                if msvcrt.kbhit():
                                    key = msvcrt.getch()
                                    if key.lower() == b'p':
                                        auto_mode = False
                                        paused_by_user = True
                                        print("\n[!] Paused by user.")
                                        # Clear any extra keys
                                        while msvcrt.kbhit(): msvcrt.getch()
                                        break
                                time.sleep(0.1)
                            
                            if not paused_by_user:
                                approval = "y"
                        
                        # If not auto-approved (or paused), ask user
                        if not approval:
                            print("\n[?] Proceed? (y/n/auto/new command)")
                            approval = input(">>> ").strip()
                        
                        if approval.lower() in ["quit", "exit"]:
                            print("Exiting...")
                            os._exit(0) # Force exit immediately

                        if approval.lower() == "auto":
                            auto_mode = True
                            approval = "y"

                        if approval.lower() == "y":
                            # Resume execution
                            if not auto_mode: print("Resuming...")
                            async for event in agent.astream(None, config=config):
                                if "tools" in event:
                                    for msg in event["tools"]["messages"]:
                                        print(f"\n[Tool Output]: {msg.content[:200]}...")
                                if "agent" in event:
                                    msg = event["agent"]["messages"][0]
                                    print(f"\n[Agent]: {msg.content}")
                                    if msg.tool_calls:
                                        print(f"\n[PAUSED] Agent wants to call: {[t['name'] for t in msg.tool_calls]}")
                        
                        elif approval.lower() == "n":
                            print("Aborted by user.")
                            break
                        
                        else:
                            # Inject new command (Redirect)
                            print(f"Redirecting with: '{approval}'")
                            async for event in agent.astream(
                                {"messages": [("user", approval)]},
                                config=config
                            ):
                                if "agent" in event:
                                    msg = event["agent"]["messages"][0]
                                    print(f"\n[Agent]: {msg.content}")
                                    if msg.tool_calls:
                                        print(f"\n[PAUSED] Agent wants to call: {[t['name'] for t in msg.tool_calls]}")

    except KeyboardInterrupt:
        print("\nInterrupted.")
        os._exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        os._exit(1)

if __name__ == "__main__":
    # Windows asyncio fix
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("Goodbye.")
        os._exit(0)
