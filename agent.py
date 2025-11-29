import asyncio
import os
import subprocess
from typing import Annotated, Literal, TypedDict

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load API Key
def load_api_key():
    try:
        with open("searcher_api.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: searcher_api.txt not found.")
        return None

API_KEY = load_api_key()
BASE_URL = "https://api.deepseek.com"

# Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Global MCP Session (for simplicity in this script)
# In a production app, you'd manage this lifecycle better.
mcp_session = None

@tool
async def xhs_search_tool(keyword: str) -> str:
    """
    Search for a keyword on Xiaohongshu (Little Red Book) and open the results in a browser.
    Use this tool when the user asks to search for something on XHS.
    """
    global mcp_session
    if not mcp_session:
        return "Error: MCP session not initialized."
    
    try:
        # Call the tool via MCP
        result = await mcp_session.call_tool("xhs_search_keyword", arguments={"keyword": keyword})
        
        # Format the result
        output = ""
        if result.content:
            for content in result.content:
                if content.type == "text":
                    output += content.text + "\n"
        return output.strip()
    except Exception as e:
        return f"Error calling xhs_search_keyword: {str(e)}"

async def run_agent():
    global mcp_session
    
    # 1. Start MCP Server
    server_params = StdioServerParameters(
        command="./xhs-server.exe", # Ensure this path is correct relative to where you run python
        args=[],
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            mcp_session = session
            
            # Initialize tools
            await session.initialize()
            
            # List tools to verify (optional)
            tools_list = await session.list_tools()
            print(f"Connected to MCP Server. Available tools: {[t.name for t in tools_list.tools]}")

            # 2. Setup LangGraph Agent
            llm = ChatOpenAI(
                base_url=BASE_URL,
                api_key=API_KEY,
                model="deepseek-chat", # or deepseek-reasoner
                temperature=0,
            )
            
            tools = [xhs_search_tool]
            llm_with_tools = llm.bind_tools(tools)

            def agent_node(state: AgentState):
                messages = state["messages"]
                response = llm_with_tools.invoke(messages)
                return {"messages": [response]}

            def should_continue(state: AgentState) -> Literal["tools", END]:
                messages = state["messages"]
                last_message = messages[-1]
                if last_message.tool_calls:
                    return "tools"
                return END

            workflow = StateGraph(AgentState)
            workflow.add_node("agent", agent_node)
            workflow.add_node("tools", ToolNode(tools))

            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges("agent", should_continue)
            workflow.add_edge("tools", "agent")

            app = workflow.compile()

            # 3. Run the Workflow
            print("\n--- Starting Agent ---")
            user_input = "Find tutorials for GitHub Student Verification"
            print(f"User: {user_input}")
            
            inputs = {"messages": [("user", user_input)]}
            
            async for output in app.astream(inputs):
                for key, value in output.items():
                    print(f"Node '{key}':")
                    # print(value) # Debug: print full state
                    if "messages" in value:
                        last_msg = value["messages"][-1]
                        print(f"  Role: {last_msg.type}")
                        print(f"  Content: {last_msg.content}")
                        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                            print(f"  Tool Calls: {last_msg.tool_calls}")
            print("--- Agent Finished ---")

if __name__ == "__main__":
    asyncio.run(run_agent())
