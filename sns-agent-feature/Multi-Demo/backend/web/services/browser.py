"""
Browser Service - Wraps the ChromeMCP functionality for the backend.
"""
from __future__ import annotations

import asyncio
import json
import sys
import os
from typing import List, Optional, Dict, Any

# Add project root to path to import backend modules
# We need to add the parent of 'backend' to sys.path so we can do 'from backend.agent_core import ...'
# The file is at E:\DOCUMENT\xhs-mcp-server\sns-agent-feature\Multi-Demo\backend\web\services\browser.py
# We want to reach E:\DOCUMENT\xhs-mcp-server\backend\agent_core.py
# So we need to add E:\DOCUMENT\xhs-mcp-server to sys.path

# Calculate the path to E:\DOCUMENT\xhs-mcp-server
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 4 levels: services -> web -> backend -> Multi-Demo -> sns-agent-feature -> xhs-mcp-server
# Wait, the structure is:
# E:\DOCUMENT\xhs-mcp-server\
#   backend\
#     agent_core.py
#   sns-agent-feature\
#     Multi-Demo\
#       backend\
#         web\
#           services\
#             browser.py

# So we need to go up 5 levels from browser.py to reach xhs-mcp-server root
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.checkpoint.memory import MemorySaver

# Import from the existing backend/agent_core.py
try:
    # We need to be careful because 'backend' is ambiguous.
    # There is 'backend' in 'sns-agent-feature/Multi-Demo/backend' (the new one)
    # And 'backend' in 'xhs-mcp-server/backend' (the old one)
    
    # To import the old backend, we can try to import it directly from the path
    # or rename the import temporarily.
    
    import importlib.util
    
    # Define the path to the old agent_core.py
    old_backend_path = os.path.join(project_root, "backend", "agent_core.py")
    old_session_path = os.path.join(project_root, "backend", "session_manager.py")
    
    if os.path.exists(old_backend_path):
        spec = importlib.util.spec_from_file_location("old_backend_agent_core", old_backend_path)
        agent_core_module = importlib.util.module_from_spec(spec)
        sys.modules["old_backend_agent_core"] = agent_core_module
        spec.loader.exec_module(agent_core_module)
        
        create_mcp_tools = agent_core_module.create_mcp_tools
        build_agent_graph = agent_core_module.build_agent_graph
        
        spec_session = importlib.util.spec_from_file_location("old_backend_session_manager", old_session_path)
        session_module = importlib.util.module_from_spec(spec_session)
        sys.modules["old_backend_session_manager"] = session_module
        spec_session.loader.exec_module(session_module)
        
        inject_session = session_module.inject_session
    else:
        raise ImportError(f"File not found: {old_backend_path}")

except Exception as e:
    # Fallback for when running in a different context or if imports fail
    print(f"Warning: Could not import backend.agent_core: {e}. Browser functionality will be limited.")
    create_mcp_tools = None
    build_agent_graph = None
    inject_session = None

from ..utils.logger import get_logger
from ..config import Settings

# Hardcoded path to the MCP server (same as in agent_chrome.py)
# In a real deployment, this should be in config
MCP_SERVER_PATH = "C:\\Users\\63091\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"

class BrowserService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._logger = get_logger("services.BrowserService")
        self._server_params = StdioServerParameters(
            command="node",
            args=[MCP_SERVER_PATH],
            env=None
        )
        self._agent = None
        self._tools = []
        self._session_context = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Initialize the connection to the MCP server."""
        if not os.path.exists(MCP_SERVER_PATH):
            self._logger.error(f"MCP Server not found at {MCP_SERVER_PATH}")
            return

        self._logger.info("Starting Browser Service...")
        # Note: stdio_client is an async context manager. 
        # To keep it alive, we might need a different approach or wrap the execution.
        # For this version, we will connect per-request or use a long-running task.
        # Given the complexity of keeping stdio pipes open in FastAPI, 
        # we will implement a 'run_task' method that connects, runs, and disconnects for now,
        # or we can try to maintain the session if we run this in a background loop.
        pass

    async def search(self, topic: str, platform: str) -> str:
        """
        Run a search task using the Browser Agent.
        Returns the raw text summary/result from the agent.
        """
        if not create_mcp_tools:
            return "Browser integration not available (ImportError)."

        # Enhanced prompt with specific instructions for the browser agent
        # These instructions are derived from the successful patterns in agent_core.py
        prompt = (
            f"TASK: Search for '{topic}' on {platform} and extract relevant content.\n\n"
            f"INSTRUCTIONS:\n"
            f"1. START: Open a NEW WINDOW using `chrome_navigate(url='...', newWindow=True)`.\n"
            f"   - If {platform} is 'xiaohongshu' or 'xhs', go to 'https://www.xiaohongshu.com'.\n"
            f"   - If {platform} is 'google', go to 'https://www.google.com'.\n"
            f"2. VERIFY: Call `get_windows_and_tabs` to confirm the new window is active.\n"
            f"3. SEARCH: Find the search input box, type '{topic}', and press Enter.\n"
            f"   - Use `chrome_fill_or_select` or `chrome_keyboard`.\n"
            f"4. BROWSE: Wait for results to load. Scroll down if necessary.\n"
            f"5. EXTRACT: Identify the top 3-5 most relevant results.\n"
            f"   - For each result, extract: Title, URL, and a brief Summary.\n"
            f"   - If on Xiaohongshu, use `extract_images_from_page` to find image URLs.\n"
            f"6. OUTPUT: Return the final result as a JSON string list of objects with keys: topic, source, title, url, summary.\n"
        )

        self._logger.info(f"Executing browser task: {prompt}")

        # Connect and run
        # We use a fresh connection for each task to ensure stability for now
        try:
            async with stdio_client(self._server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Inject cookies if available (important for XHS)
                    if inject_session:
                        await inject_session(session)

                    tools = await create_mcp_tools(session)
                    memory = MemorySaver()
                    # We must set interrupt=False so the agent runs tools automatically
                    agent = build_agent_graph(tools, checkpointer=memory, interrupt=False)

                    config = {"configurable": {"thread_id": "browser_search_task"}, "recursion_limit": 50}
                    
                    final_response = ""
                    
                    # Run the agent
                    # We need to handle the tool execution loop manually if we are not using the interrupt mechanism
                    # or if we want to ensure it runs to completion.
                    # The 'agent' returned by build_agent_graph is a compiled LangGraph.
                    
                    # In agent_chrome.py, it iterates over events.
                    # We need to do the same here.
                    
                    self._logger.info("Starting agent execution loop...")
                    
                    async for event in agent.astream(
                        {"messages": [("user", prompt)]},
                        config=config
                    ):
                        if "agent" in event:
                            msg = event["agent"]["messages"][0]
                            if msg.content:
                                final_response = msg.content

                    return final_response

        except Exception as e:
            self._logger.error(f"Browser task failed: {e}")
            return f"Error executing browser task: {e}"
