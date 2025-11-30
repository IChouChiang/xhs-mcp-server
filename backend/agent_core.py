import asyncio
import json
import os
import requests
import base64
import time
from typing import Annotated, Literal, TypedDict, Any, Dict, List, Optional

from langchain_core.tools import StructuredTool
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from pydantic import create_model, Field

# --- Configuration ---
BASE_URL = "https://aihubmix.com/v1"
# BASE_URL = None # Use default OpenAI URL

def load_api_key():
    try:
        # Try to find searcher_api.txt in the same directory as this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(current_dir, "searcher_api.txt")
        if os.path.exists(key_path):
            with open(key_path, "r") as f:
                return f.read().strip()
        
        # Fallback to current working directory
        with open("searcher_api.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: searcher_api.txt not found.")
        return None

API_KEY = load_api_key()

# --- System Prompt ---
SYSTEM_PROMPT = """You are an expert Browser Automation Agent powered by GPT-5. You control a real Chrome/Edge browser via Model Context Protocol (MCP) tools.

### 🧠 CORE PHILOSOPHY
1. **Think Step-by-Step**: Before taking any action, briefly explain your plan.
2. **Action -> Reaction**: Filling a form does nothing until you **Submit** it. Always follow `fill` with `click` or `Enter`.
3. **Verify & Explore**: Don't just assume it worked. Check the page content.
   - **Challenge**: Try to use *different* tools to verify your state (e.g., scroll down, read text, check interactive elements) to prove you have full control.

### 🛠️ TOOL USAGE MASTERY
You have access to tools for controlling the browser. You MUST use them correctly.

**1. Navigation (`chrome_navigate`)**
   - **Usage**: `chrome_navigate(url="https://...", newWindow=True)`
   - **Rule**: ALWAYS start a new task with `newWindow=True`.

**2. Finding Elements (`chrome_get_interactive_elements`)**
   - **Usage**: `chrome_get_interactive_elements(textQuery="Search")`
   - **Rule**: Use this to find selectors when you don't know them. It returns a list of interactive elements with their CSS selectors.

**3. Interaction (`chrome_fill_or_select`, `chrome_click_element`)**
   - **Usage**: `chrome_fill_or_select(selector="#search-input", value="My Query")`
   - **Usage**: `chrome_click_element(selector="button.submit")`
   - **CRITICAL**: After filling an input, the page **WILL NOT UPDATE** automatically.
   - **PREFERRED**: Find and **CLICK** the search button (icon). This is more reliable than "Enter".
   - **FALLBACK**: If you must use "Enter", ensure the input is focused first.

**4. Keyboard (`chrome_keyboard`)**
   - **Usage**: `chrome_keyboard(keys="Enter")`
   - **Rule**: Use this only if there is no clear submit button.

**5. Content Extraction (`chrome_get_web_content`, `extract_images_from_page`)**
   - **Usage**: `chrome_get_web_content(htmlContent=False)` for text.
   - **Usage**: `extract_images_from_page()` for images (especially on Xiaohongshu).

### 🚨 CRITICAL RULES
- **Arguments**: Ensure all tool arguments are valid JSON. Do not pass empty objects `{}` if the tool requires parameters.
- **Xiaohongshu (XHS) Specifics**:
  - **Search**: The "Enter" key often fails on XHS. **ALWAYS** try to click the "Search" button/icon next to the input bar.
  - **Images**: Images are often in `background-image`. Use `extract_images_from_page`.
  - **Anti-scraping**: Use `download_file` tool which mimics browser headers.
- **Errors**: If a tool returns an error, READ it. If it says "Element not found", do not retry the exact same selector. Get new selectors.

### 🏁 GOAL
Your goal is to complete the user's request efficiently. When done, provide a summary of what you found or achieved.
"""

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# --- Helper: Output Parser ---
def parse_tool_output(raw_output):
    """Parses the nested JSON output from the bridge."""
    try:
        # 1. Parse the outer bridge JSON (if it's JSON)
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            return raw_output

        if not isinstance(data, dict): return raw_output
        
        # Check for bridge error
        if data.get("isError"):
            return f"❌ Bridge Error: {data.get('message')}"
            
        # 2. Extract the inner content
        # The bridge usually puts the result in data.content[0].text
        inner_content = data.get("data", {}).get("content", [])
        # Sometimes it's directly in 'content' if it's a direct MCP response
        if not inner_content and "content" in data:
             inner_content = data["content"]

        if not inner_content: return raw_output
        
        text_content = ""
        if isinstance(inner_content, list):
            if len(inner_content) > 0:
                text_content = inner_content[0].get("text", "")
        
        # 3. Try to parse the inner JSON (the actual tool result)
        try:
            inner_data = json.loads(text_content)
            if isinstance(inner_data, dict):
                # If it has a 'message', return that (it's usually the human readable part)
                if "message" in inner_data:
                    return f"✅ {inner_data['message']}\n\nFull Data: {json.dumps(inner_data, indent=2, ensure_ascii=False)}"
                return json.dumps(inner_data, indent=2, ensure_ascii=False)
        except:
            pass
            
        return text_content if text_content else raw_output
    except Exception as e:
        return f"Error parsing output: {str(e)}\nRaw: {raw_output}"

# --- Local Tools ---
def download_file(url: str, filename: str = None) -> str:
    """
    Downloads a file from a URL to the local 'downloads' folder.
    Includes headers to mimic a real browser to avoid 403/404 errors.
    """
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
            
        if not filename:
            # Clean filename from URL
            filename = url.split("/")[-1].split("?")[0] or "downloaded_file"
            if not "." in filename:
                filename += ".jpg" # Default extension
            
        filepath = os.path.join("downloads", filename)
        
        print(f"[TOOL] Downloading {url} to {filepath}...")
        
        # Mimic Chrome to avoid anti-scraping
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return f"✅ Successfully downloaded to: {filepath}"
    except Exception as e:
        return f"❌ Download failed: {str(e)}"

def create_pydantic_model_from_schema(name: str, schema: Dict[str, Any]):
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    fields = {}
    for field_name, field_info in properties.items():
        field_type = str
        t = field_info.get("type")
        if t == "boolean":
            field_type = bool
        elif t == "integer":
            field_type = int
        elif t == "number":
            field_type = float
        elif t == "array":
            field_type = list
        elif t == "object":
            field_type = dict
            
        # Determine default value
        if field_name in required:
            default = ...
        else:
            default = None
            
        fields[field_name] = (field_type, Field(default=default, description=field_info.get("description", "")))
        
    return create_model(f"{name}Schema", **fields)

# --- Tool Factory ---
async def create_mcp_tools(session):
    """
    Dynamically creates LangChain tools from an MCP session.
    Includes argument unwrapping and timeouts.
    """
    tools_list = await session.list_tools()
    langchain_tools = []

    # 1. Add MCP Tools
    for tool_info in tools_list.tools:
        tool_name = tool_info.name
        tool_description = tool_info.description or "No description provided."
        
        # Create Pydantic model for args
        args_schema = None
        if tool_info.inputSchema:
             try:
                 args_schema = create_pydantic_model_from_schema(tool_name, tool_info.inputSchema)
             except Exception as e:
                 print(f"Warning: Could not create schema for {tool_name}: {e}")

        # Factory to capture the specific tool_name for this iteration
        def create_tool_wrapper(name):
            async def _dynamic_tool(**kwargs):
                # 1. Unwrap arguments (Fix for LangChain/DeepSeek kwargs issue)
                actual_args = kwargs
                if "kwargs" in kwargs and len(kwargs) == 1:
                    actual_args = kwargs["kwargs"]
                
                print(f"\n[AGENT] Calling Tool: {name}")
                print(f"[AGENT] Args: {json.dumps(actual_args, ensure_ascii=False)}")

                try:
                    # 2. Call with Timeout (30s)
                    result = await asyncio.wait_for(
                        session.call_tool(name, arguments=actual_args),
                        timeout=30.0
                    )
                    
                    # 3. Format Output
                    output = ""
                    if result.content:
                        for content in result.content:
                            if content.type == "text":
                                output += content.text + "\n"
                            elif content.type == "image":
                                # Save image to disk
                                try:
                                    if not os.path.exists("downloads"):
                                        os.makedirs("downloads")
                                    timestamp = int(time.time())
                                    filename = f"screenshot_{timestamp}.png"
                                    filepath = os.path.join("downloads", filename)
                                    
                                    image_data = base64.b64decode(content.data)
                                    with open(filepath, "wb") as f:
                                        f.write(image_data)
                                    
                                    output += f"✅ Image saved to: {filepath}\n"
                                    print(f"[TOOL] Saved image to {filepath}")
                                except Exception as e:
                                    output += f"❌ Failed to save image: {str(e)}\n"
                    
                    parsed_output = parse_tool_output(output.strip())
                    print(f"[TOOL] Result: {parsed_output[:200]}...") # Log summary
                    return parsed_output

                except asyncio.TimeoutError:
                    err_msg = f"Error: Tool '{name}' timed out after 30 seconds."
                    print(f"[TOOL] {err_msg}")
                    return err_msg
                except Exception as e:
                    err_msg = str(e)
                    # Detect critical connection errors
                    if "Failed to connect" in err_msg or "Broken pipe" in err_msg or "Connection refused" in err_msg:
                        print(f"\n[CRITICAL] Connection to MCP server lost: {err_msg}")
                        raise ConnectionError("MCP Connection Lost") from e
                    
                    err_msg = f"Error calling {name}: {err_msg}"
                    print(f"[TOOL] {err_msg}")
                    return err_msg
            return _dynamic_tool

        # Create the wrapper
        tool_func = create_tool_wrapper(tool_name)
        tool_func.__name__ = tool_name
        tool_func.__doc__ = tool_description
        
        # Create StructuredTool
        l_tool = StructuredTool.from_function(
            func=None,
            coroutine=tool_func,
            name=tool_name,
            description=tool_description,
            args_schema=args_schema
        )
        langchain_tools.append(l_tool)
    
    # 2. Add Local Tools
    langchain_tools.append(StructuredTool.from_function(
        func=download_file,
        name="download_file",
        description="Downloads a file from a URL to the local 'downloads' folder. Use this to save images or files."
    ))

    # 3. Add Image Extraction Tool (Specialized for XHS)
    async def extract_images_from_page():
        """
        Scans the current page for all images, including hidden CSS background-images.
        Useful for sites like Xiaohongshu where images are not simple <img> tags.
        """
        # JS to find images and set document.title
        js_script = """
        (function() {
            const images = [];
            const seen = new Set();
            
            function add(src, type, meta) {
                if (src && src.startsWith('http') && !seen.has(src)) {
                    seen.add(src);
                    images.push({src, type, meta: meta.trim().replace(/\\n/g, ' ')});
                }
            }

            document.querySelectorAll('img').forEach(img => {
                add(img.src, 'img', img.alt || img.title || '');
            });

            document.querySelectorAll('div, span, a, section').forEach(el => {
                const style = window.getComputedStyle(el);
                const bg = style.backgroundImage;
                if (bg && bg.startsWith('url(')) {
                    const url = bg.slice(4, -1).replace(/["']/g, "");
                    add(url, 'bg', el.innerText.slice(0, 30));
                }
            });
            
            const result = JSON.stringify(images.slice(0, 50));
            document.title = "MCP_IMAGES_RESULT:" + result;
        })();
        """
        print(f"\n[AGENT] Calling Tool: extract_images_from_page")
        try:
            # 1. Inject Script
            # Note: chrome_inject_script expects 'jsScript' and 'type'='js'
            await session.call_tool("chrome_inject_script", arguments={"jsScript": js_script, "type": "js"})
            
            # 2. Read Title
            await asyncio.sleep(0.5)
            content_result = await session.call_tool("chrome_get_web_content", arguments={})
            
            # Parse output
            title = ""
            if content_result.content:
                for content in content_result.content:
                    if content.type == "text":
                        try:
                            # The tool returns a JSON string
                            data = json.loads(content.text)
                            if isinstance(data, dict):
                                title = data.get("title", "")
                        except:
                            pass
            
            if title.startswith("MCP_IMAGES_RESULT:"):
                json_str = title.replace("MCP_IMAGES_RESULT:", "", 1)
                return json_str
            else:
                return "[]" # No images found or script failed
            
        except Exception as e:
            return f"Error extracting images: {str(e)}"

    langchain_tools.append(StructuredTool.from_function(
        func=None,
        coroutine=extract_images_from_page,
        name="extract_images_from_page",
        description="Scans the current page for all images, including hidden CSS background-images. Returns a list of image URLs."
    ))
        
    return langchain_tools

# --- Graph Builder ---
def build_agent_graph(tools, checkpointer=None, interrupt=True):
    """Builds the LangGraph agent."""
    
    llm = ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model="gpt-5-chat-latest",
        temperature=0,
    )
    
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        messages = state["messages"]
        # Prepend System Prompt
        full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm_with_tools.invoke(full_messages)
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

    interrupt_before = ["tools"] if (checkpointer and interrupt) else None
    return workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt_before)
