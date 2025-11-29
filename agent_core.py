import asyncio
import json
import os
import requests
from typing import Annotated, Literal, TypedDict

from langchain_core.tools import StructuredTool
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# --- Configuration ---
BASE_URL = "https://api.deepseek.com"

def load_api_key():
    try:
        with open("searcher_api.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: searcher_api.txt not found.")
        return None

API_KEY = load_api_key()

# --- System Prompt ---
SYSTEM_PROMPT = """You are an expert Browser Automation Agent. You control a real Chrome/Edge browser via MCP tools.

### CRITICAL RULES:

1. **STARTING A TASK**:
   - **ALWAYS** start by opening a **NEW WINDOW**.
   - Use: `chrome_navigate(url='...', newWindow=True)`
   - **DO NOT** try to use the current tab (it might be the agent controller).

2. **VERIFY NAVIGATION**:
   - After navigating, **ALWAYS** call `get_windows_and_tabs` to confirm the new window is open and get its `tabId`.
   - This ensures you are targeting the correct page.

3. **INTERACTION**:
   - **Selectors**: Avoid long, brittle chains like `div > div > div`. Use unique IDs, classes, or attributes (e.g., `button[aria-label='Save']`, `img[alt*='Bride']`).
   - **Click Failures**: If `chrome_click_element` fails, try `chrome_execute_script(script="document.querySelector('YOUR_SELECTOR').click()")`.
   - **Downloads**: To download an image or file, **DO NOT** try to click "Download". Instead, extract the `src` or `href` URL and use the `download_file` tool.

4. **IMAGE EXTRACTION (XIAOHONGSHU SPECIAL)**:
   - Xiaohongshu (XHS) often hides images in `background-image` CSS or lazy-loads them.
   - **ALWAYS** use the `extract_images_from_page` tool to find images. It runs a special script to find both `<img>` tags and CSS background images.
   - If you see a 404 or 403 error when downloading, it might be an anti-hotlink protection. The `download_file` tool handles some of this, but ensure the URL is correct.

5. **FORBIDDEN**:
   - **DO NOT** use `chrome_network_request` (it's invisible).
   - **DO NOT** use `chrome_inject_script` for navigation.
   - **DO NOT** close the tab immediately after opening it.

6. **TIMEOUTS**:
   - If a tool takes too long, it might be stuck. Try a different approach or refresh the page.

7. **COMPLETION**:
   - When you have achieved the user's goal, **STOP** using tools.
   - Provide a final text answer to the user summarizing what you did.
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
                                output += "[Image returned]\n"
                    
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

            // 1. IMG tags
            document.querySelectorAll('img').forEach(img => {
                add(img.src, 'img', img.alt || img.title || '');
            });

            // 2. Background images (common in XHS)
            // We scan divs and spans which are most likely to have bg images
            document.querySelectorAll('div, span, a, section').forEach(el => {
                const style = window.getComputedStyle(el);
                const bg = style.backgroundImage;
                if (bg && bg.startsWith('url(')) {
                    const url = bg.slice(4, -1).replace(/["']/g, "");
                    add(url, 'bg', el.innerText.slice(0, 30));
                }
            });
            
            return JSON.stringify(images.slice(0, 50)); // Limit to 50 to avoid overflow
        })();
        """
        print(f"\n[AGENT] Calling Tool: extract_images_from_page")
        try:
            # We use the existing session to call execute_script
            result = await session.call_tool("chrome_execute_script", arguments={"script": js_script})
            
            # Parse output
            output = ""
            if result.content:
                for content in result.content:
                    if content.type == "text":
                        output += content.text
            
            # The bridge returns JSON string in the text usually
            parsed = parse_tool_output(output)
            return parsed
            
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
def build_agent_graph(tools, checkpointer=None):
    """Builds the LangGraph agent."""
    
    llm = ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model="deepseek-chat",
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

    if checkpointer:
        return workflow.compile(checkpointer=checkpointer, interrupt_before=["tools"])
    
    return workflow.compile()
