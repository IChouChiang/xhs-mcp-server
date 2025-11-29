# 🛠️ Developer Guide & API Reference

This document provides a deep dive into the codebase, API contracts, and data structures. It is designed to help developers understand how to extend the system for complex features.

## 📂 File Structure Analysis

### Backend Directory (`/backend`)
- **`agent_server.py`**: The main entry point for the Backend.
    - **Role**: Hosts the FastAPI server and initializes the LangGraph Agent.
    - **Key Components**:
        - `lifespan`: Async context manager that handles MCP connection, Session Injection (`auth.json`), and Tool creation.
        - `/chat` Endpoint: Handles user interaction, context injection, and tool execution.
        - `/publish` Endpoint: Handles automation tasks.
        - `ModifyCanvasSchema`: Defines the strict structure for AI UI modifications.
- **`agent_core.py`**: The brain of the Agent.
    - **Role**: Contains the core logic for the LangGraph agent and Tool definitions.
    - **Key Components**:
        - `SYSTEM_PROMPT`: The master instruction set for the AI (Browser control rules, XHS specifics).
        - `create_mcp_tools`: Dynamically wraps MCP tools (from `mcp-chrome-bridge`) into LangChain tools.
        - `extract_images_from_page`: A custom tool injecting JS to find hidden/lazy-loaded images.
        - `build_agent_graph`: Constructs the StateGraph (Nodes: Agent, Tools).
- **`session_manager.py`**: Authentication Handler.
    - **Role**: Injects cookies and `localStorage` from `auth.json` into the Chrome instance.
    - **Key Function**: `inject_session` - Opens a new window, navigates to XHS, injects script, and reloads.
- **`agent_chrome.py`**: CLI Debugger.
    - **Role**: A standalone script to run the agent in the terminal without the Web UI. Useful for testing tools in isolation.

### Frontend Directory (`/frontend`)
- **`app/aipost/App.tsx`**: The Main Application Logic.
    - **Role**: Manages the Canvas state (`elements`), Selection state (`selectedElementIds`), and AI communication.
    - **Key Functions**:
        - `handleAIModify`: Packs the current canvas state and sends it to `/chat`.
        - `addElement`, `updateElement`: State mutators used by the AI's response.
- **`app/aipost/components/AIDialog.tsx`**: The Chat Interface.
    - **Role**: Renders the chat history and "Quick Suggestions".
    - **Key Logic**: Displays the `suggestions` array returned by the backend as clickable chips.

---

## 🔌 API Reference

### 1. Chat Endpoint (`POST /chat`)
**Purpose**: The primary channel for User <-> Agent interaction. It allows the AI to "see" the canvas and "act" on it.

#### Request Payload (`ChatRequest`)
```json
{
  "prompt": "Make the title bigger and search for cat images",
  "elements": [
    {
      "id": "el-123",
      "type": "text",
      "content": "Summer Party",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 50,
      "styles": { "color": "#000000", "fontSize": 24 }
    }
  ],
  "selectedIds": ["el-123"]
}
```
- **`prompt`** *(string)*: The user's natural language instruction.
- **`elements`** *(Array)*: The FULL state of the canvas. The AI needs this to understand context (what is currently on screen).
- **`selectedIds`** *(Array)*: IDs of elements currently selected by the user. Helps the AI know what "this" or "it" refers to.

#### Response Payload
```json
{
  "status": "success",
  "message": "I have updated the title size and found some images.",
  "actions": [
    {
      "action": "update",
      "elementId": "el-123",
      "element": { "styles": { "fontSize": 48 } }
    },
    {
      "action": "add",
      "element": { "type": "image", "content": "http://...", "x": 0, "y": 0 }
    }
  ],
  "suggestions": [
    "Change background to yellow",
    "Add a date text",
    "Align all elements"
  ]
}
```
- **`message`** *(string)*: The AI's textual reply.
- **`actions`** *(Array)*: A list of concrete operations to perform on the frontend state.
    - **`action`**: `add` | `update` | `delete`
    - **`element`**: The data for the element (partial for updates, full for adds).
- **`suggestions`** *(Array)*: **EXACTLY 3** short, actionable strings. These are displayed as buttons to the user.

### 2. Publish Endpoint (`POST /publish`)
**Purpose**: Triggers the automation sequence to post content to a platform.

#### Request Payload (`PublishRequest`)
```json
{
  "platform": "xiaohongshu",
  "elements": [ ... ] // Same canvas data
}
```

#### Response Payload
```json
{
  "status": "success",
  "message": "Successfully published the post!"
}
```

---

## 🧠 Data Packing & Logic Flow

### The "Context Loop"
1.  **Frontend Packing**:
    -   When the user sends a message, `App.tsx` serializes the `elements` array and `selectedIds`.
    -   It sends this snapshot to the backend.
2.  **Backend Context Construction** (`agent_server.py`):
    -   The server receives the snapshot.
    -   It constructs a **System Prompt** that includes:
        -   JSON dump of `elements`.
        -   JSON dump of `selectedIds`.
        -   The user's `prompt`.
    -   *Crucial*: It appends the **"Exactly 3 Suggestions"** rule to the prompt.
3.  **AI Processing** (`agent_core.py`):
    -   DeepSeek receives the prompt + context.
    -   It decides whether to:
        -   Call `modify_canvas` (to change UI).
        -   Call `chrome_navigate` / `search` (to browse web).
        -   Just reply with text.
4.  **Tool Execution**:
    -   If `modify_canvas` is called, the arguments (`actions`, `suggestions`) are captured.
    -   If browser tools are called, they execute via MCP.
5.  **Response Parsing**:
    -   The server aggregates the final text response, the captured `actions`, and the `suggestions`.
    -   It returns them to the frontend.
6.  **Frontend Unpacking**:
    -   `App.tsx` receives the response.
    -   `actions` are iterated:
        -   `add`: Checks for duplicate IDs, then appends to state.
        -   `update`: Finds element by ID and merges props.
        -   `delete`: Filters out the element.
    -   `suggestions` replace the current "Quick Suggestions".

---

## 🛠️ Extending the System

### Adding a New Tool
1.  **Define the Tool**: In `agent_core.py`, add a new function (e.g., `analyze_image`).
2.  **Wrap it**: Use `StructuredTool.from_function`.
3.  **Register it**: Add it to the `tools` list in `create_mcp_tools`.
4.  **Update Prompt**: If necessary, mention the tool in `SYSTEM_PROMPT`.

### Adding a New Canvas Feature (e.g., "Groups")
1.  **Frontend**: Update `CanvasElement` interface in `App.tsx` to support groups.
2.  **Backend Schema**: Update `CanvasElementData` in `agent_server.py` to include `groupId`.
3.  **Prompt**: Update `context_prompt` in `agent_server.py` to explain how to use groups.


##  LLM Integration (AiHubMix)

The project uses **AiHubMix** as the LLM provider, which aggregates models like OpenAI, Gemini, and Claude.

### Configuration
Configuration is stored in ackend/llm_config.json (do not commit this file if it contains real keys, use uth.json pattern or env vars in production).

`json
{
  "llm_api_key": "sk-...",
  "llm_base_url": "https://aihubmix.com/v1",
  "llm_model": "gpt-4o"
}
``n
### Tested Models
We have verified the following models work correctly with the platform:

1.  **Text Chat**: gpt-4o
    *   Standard OpenAI chat completion format.
2.  **Search / Knowledge**: gemini-3-pro-preview-search
    *   **Note**: This specific model ID is required for search capabilities. Generic gemini-pro IDs may fail.
3.  **Image Generation**: dall-e-3
    *   Standard OpenAI image generation format.

### Testing
A test script ackend/test_aihubmix.py is available to verify connectivity and model capabilities.

### Tested Models
We have verified the following models work correctly with the platform:

1.  **Text Chat**: gpt-4o
    *   Standard OpenAI chat completion format.
2.  **Search / Knowledge**: gemini-3-pro-preview-search
    *   **Note**: This specific model ID is required for search capabilities. Generic gemini-pro IDs may fail.
3.  **Image Generation**: dall-e-3
    *   Standard OpenAI image generation format.

### Testing
A test script ackend/test_aihubmix.py is available to verify connectivity and model capabilities.
