import asyncio
import os
import sys
import json
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from langchain_core.tools import StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.checkpoint.memory import MemorySaver

from agent_core import create_mcp_tools, build_agent_graph
from session_manager import inject_session

# --- Configuration ---
# Adjust path if necessary, matching agent_chrome.py
SERVER_PARAMS = StdioServerParameters(
    command="node",
    args=["C:\\Users\\63091\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"],
    env=None
)

# --- Canvas Tool Definition ---
class CanvasStyle(BaseModel):
    color: Optional[str] = None
    fontSize: Optional[int] = None
    fontWeight: Optional[str] = None
    backgroundColor: Optional[str] = None
    rotation: Optional[int] = None

class CanvasElementData(BaseModel):
    id: Optional[str] = None 
    type: Literal['text', 'image', 'drawing']
    content: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    styles: Optional[CanvasStyle] = None

class CanvasAction(BaseModel):
    action: Literal['add', 'update', 'delete']
    elementId: Optional[str] = Field(None, description="Required for update/delete")
    element: Optional[CanvasElementData] = Field(None, description="Required for add, optional for update")

class ModifyCanvasSchema(BaseModel):
    rationale: str = Field(..., description="Why you are making these changes")
    actions: List[CanvasAction]

def modify_canvas(rationale: str, actions: List[CanvasAction]):
    """
    Use this tool to modify the user's canvas. 
    You can add new elements (text, images), update existing ones (change color, position, text), or delete them.
    """
    return f"Canvas actions generated: {len(actions)} actions."

# Global State
class AppState:
    session: ClientSession = None
    agent = None
    config = None
    exit_stack = None

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== Starting MCP Agent Server ===")
    
    # Windows asyncio fix
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # We need to manually manage the context managers since they are async
    # and we want them to persist across requests.
    # Using an ExitStack would be cleaner but async exit stack is Python 3.7+
    from contextlib import AsyncExitStack
    state.exit_stack = AsyncExitStack()

    try:
        # 1. Connect to MCP Server
        read, write = await state.exit_stack.enter_async_context(stdio_client(SERVER_PARAMS))
        state.session = await state.exit_stack.enter_async_context(ClientSession(read, write))
        
        await state.session.initialize()
        print("Connected to MCP Server.")

        # 2. Inject Session (Cookies)
        print("Injecting session cookies...")
        await inject_session(state.session)

        # 3. Create Tools & Agent
        print("Creating tools...")
        tools = await create_mcp_tools(state.session)
        
        # Add the Canvas Modification Tool
        tools.append(StructuredTool.from_function(
            func=modify_canvas,
            name="modify_canvas",
            description="Modify the user's canvas (add/update/delete elements).",
            args_schema=ModifyCanvasSchema
        ))
        
        # Initialize Memory
        memory = MemorySaver()
        # Disable interrupts for the server so it executes tools automatically
        state.agent = build_agent_graph(tools, checkpointer=memory, interrupt=False)
        
        # Config for the agent
        state.config = {"configurable": {"thread_id": "server_thread"}, "recursion_limit": 50}
        
        print(f"Agent ready with {len(tools)} tools.")
        
        yield
        
    except Exception as e:
        print(f"Startup failed: {e}")
        raise e
    finally:
        print("Shutting down MCP Agent Server...")
        if state.exit_stack:
            await state.exit_stack.aclose()

app = FastAPI(lifespan=lifespan)

class PublishRequest(BaseModel):
    platform: str
    elements: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    prompt: str
    elements: List[Dict[str, Any]]

@app.post("/chat")
async def chat_post(request: ChatRequest):
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    print(f"\n[API] Received chat request: {request.prompt}")
    
    # Construct Prompt with Context
    elements_desc = json.dumps(request.elements, indent=2)
    context_prompt = (
        f"User is working on a canvas with the following elements:\n{elements_desc}\n\n"
        f"User says: '{request.prompt}'\n"
        "Please provide advice, suggestions, or perform actions based on this context. "
        "If the user asks for design advice, analyze the elements and give specific feedback. "
        "If the user asks to find resources (like images), use your tools to find them. "
        "If you want to modify the canvas (add images, change text, etc.), use the 'modify_canvas' tool."
    )

    print(f"[API] Context Prompt: {context_prompt[:100]}...")

    try:
        final_response = ""
        canvas_actions = []

        async for event in state.agent.astream(
            {"messages": [("user", context_prompt)]},
            config=state.config
        ):
            if "agent" in event:
                msg = event["agent"]["messages"][0]
                print(f"[Agent]: {msg.content}")
                final_response = msg.content
                
                # Check for tool calls in the agent's message
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if tool_call['name'] == 'modify_canvas':
                            print(f"[API] Captured modify_canvas action: {tool_call['args']}")
                            # Extract actions from the tool call arguments
                            if 'actions' in tool_call['args']:
                                canvas_actions.extend(tool_call['args']['actions'])

            if "tools" in event:
                for msg in event["tools"]["messages"]:
                    print(f"[Tool]: {msg.content[:100]}...")

        return {
            "status": "success", 
            "message": final_response,
            "actions": canvas_actions
        }

    except Exception as e:
        print(f"[API] Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/publish")
async def publish_post(request: PublishRequest):
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    print(f"\n[API] Received publish request for {request.platform}")
    
    # Construct Prompt
    elements_desc = json.dumps(request.elements, indent=2)
    prompt = (
        f"Please publish a post to {request.platform}. "
        f"Here is the content data from the canvas: \n{elements_desc}\n"
        "1. Analyze the elements (text, images). "
        "2. Navigate to the platform. "
        "3. Create a new post with the content. "
        "If you need to upload images, use the 'upload' related tools if available, "
        "or describe how you would do it."
    )

    print(f"[API] Prompt: {prompt[:100]}...")

    try:
        # Run Agent
        # We use astream to process steps, but for the API we'll collect the final response
        # or stream logs. For now, let's just run it and return the final message.
        
        final_response = ""
        async for event in state.agent.astream(
            {"messages": [("user", prompt)]},
            config=state.config
        ):
            if "agent" in event:
                msg = event["agent"]["messages"][0]
                print(f"[Agent]: {msg.content}")
                final_response = msg.content
            if "tools" in event:
                for msg in event["tools"]["messages"]:
                    print(f"[Tool]: {msg.content[:100]}...")

        return {"status": "success", "message": final_response}

    except Exception as e:
        print(f"[API] Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
