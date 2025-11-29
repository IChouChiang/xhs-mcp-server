import asyncio
import os
from typing import Annotated, Literal, TypedDict

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

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

# Define server parameters for Stdio
# This connects directly to the Node.js process, avoiding network issues
server_params = StdioServerParameters(
    command="node",
    args=["C:\\Users\\63091\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"],
    env=None
)

# Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Global MCP Session
mcp_session = None

# We will dynamically create tools based on what the server offers, 
# but for LangChain we need to define them or wrap the generic call.
# For simplicity, we will create a generic "call_mcp_tool" or try to map them.
# However, LangChain's bind_tools expects a list of functions or schemas.
# We can fetch the tools from the server first, then create LangChain tools dynamically.

async def create_langchain_tools(session):
    tools_list = await session.list_tools()
    langchain_tools = []

    for tool_info in tools_list.tools:
        # We create a dynamic function for each tool
        # This is a bit tricky with async/closures in Python, so we define a wrapper class or factory
        
        tool_name = tool_info.name
        tool_description = tool_info.description or "No description provided."
        input_schema = tool_info.inputSchema
        
        # We'll define a generic tool function that calls this specific tool
        async def _dynamic_tool(**kwargs):
            # global mcp_session
            if not mcp_session:
                return "Error: MCP session not initialized."
            try:
                result = await mcp_session.call_tool(tool_name, arguments=kwargs)
                output = ""
                if result.content:
                    for content in result.content:
                        if content.type == "text":
                            output += content.text + "\n"
                        elif content.type == "image":
                            output += "[Image returned]\n"
                return output.strip()
            except Exception as e:
                return f"Error calling {tool_name}: {str(e)}"
        
        # Set metadata for LangChain
        _dynamic_tool.__name__ = tool_name
        _dynamic_tool.__doc__ = tool_description
        
        # Create the structured tool
        # Note: For robust schema validation, we should map input_schema to pydantic.
        # For now, we rely on the LLM to infer args from the description/name 
        # or we can use the StructuredTool class.
        from langchain_core.tools import StructuredTool
        
        # We need to convert JSON schema to something LangChain understands if we want validation,
        # but passing the raw function often works if the docstring is good.
        # However, DeepSeek might need explicit JSON schema.
        # Let's try using the StructuredTool.from_function
        
        l_tool = StructuredTool.from_function(
            func=None,
            coroutine=_dynamic_tool,
            name=tool_name,
            description=tool_description,
            # args_schema=... # We skip strict schema validation for this dynamic demo
        )
        langchain_tools.append(l_tool)
        
    return langchain_tools

async def run_agent():
    global mcp_session
    
    print(f"Connecting to Chrome MCP Server via Stdio...")

    # Connect via Stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            mcp_session = session
            
            # Initialize
            await session.initialize()
            
            # List available tools
            tools_list = await session.list_tools()
            tool_names = [t.name for t in tools_list.tools]
            print(f"Connected! Available tools: {tool_names}")
            
            # Create LangChain tools dynamically
            tools = await create_langchain_tools(session)
            
            # Setup LangGraph Agent
            llm = ChatOpenAI(
                base_url=BASE_URL,
                api_key=API_KEY,
                model="deepseek-chat",
                temperature=0,
            )
            
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

import sys

            # Run the Workflow
            print("\n--- Starting Chrome Agent ---")
            
            # Get user input from command line arguments or use default
            if len(sys.argv) > 1:
                user_input = " ".join(sys.argv[1:])
            else:
                user_input = "Open xiaohongshu.com and search for 'Github Copilot' using the search bar."
            
            print(f"User: {user_input}")
            
            inputs = {"messages": [("user", user_input)]}
            
            async for output in app.astream(inputs):
                for key, value in output.items():
                    print(f"Node '{key}':")
                    if "messages" in value:
                        last_msg = value["messages"][-1]
                        print(f"  Role: {last_msg.type}")
                        # print(f"  Content: {last_msg.content}")
                        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                            print(f"  Tool Calls: {last_msg.tool_calls}")
                        else:
                            print(f"  Content: {last_msg.content}")
            print("--- Agent Finished ---")

if __name__ == "__main__":
    asyncio.run(run_agent())
