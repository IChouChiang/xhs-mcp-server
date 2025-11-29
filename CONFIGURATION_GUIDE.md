# ⚙️ Configuration Guide (READ THIS FIRST)

This project was developed on a specific Windows environment. To run it on your machine, you **MUST** update the following configurations to match your local paths and credentials.

## 1. MCP Bridge Path (CRITICAL)

The Python agent communicates with Chrome via a Node.js bridge (`mcp-chrome-bridge`). The path to this bridge is currently **hardcoded** to the developer's machine.

**Files to Edit:**
1.  `agent_chrome.py` (Line ~16)
2.  `agent_server.py` (Line ~18)

**What to Change:**
Look for the `SERVER_PARAMS` section:

```python
SERVER_PARAMS = StdioServerParameters(
    command="node",
    # 👇 CHANGE THIS PATH TO YOUR LOCAL mcp-server-stdio.js
    args=["C:\\Users\\YOUR_USERNAME\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"],
    env=None
)
```

**How to find your path:**
If you installed the bridge globally (`npm install -g mcp-chrome-bridge`), you can find the path by running:
-   **Windows**: `where mcp-chrome-bridge` (then look for the `node_modules` folder nearby)
-   **Mac/Linux**: `which mcp-chrome-bridge`

*Tip: It is often located in your global `node_modules` folder.*

---

## 2. API Keys

The agent uses **DeepSeek** (compatible with OpenAI SDK) for reasoning.

**File to Create:**
-   Create a file named `searcher_api.txt` in the root directory (`E:\DOCUMENT\xhs-mcp-server\` or your equivalent).
-   Paste your API Key inside (e.g., `sk-xxxxxxxx`).

*Note: Do not commit this file to Git.*

---

## 3. Authentication (Cookies)

To automate Xiaohongshu (XHS), you must be logged in. The agent uses cookies injected from `auth.json`.

**File to Create/Update:**
-   `auth.json` in the root directory.

**How to get this file:**
1.  **Manual Method**:
    -   Log in to [xiaohongshu.com](https://www.xiaohongshu.com) in your regular Chrome browser.
    -   Use a "Cookie Editor" extension to export your cookies as JSON.
    -   Save them as `auth.json`.
    -   *Format*: The file should look like:
        ```json
        {
            "cookies": [ ... ],
            "origins": [ ... ] // Optional, for localStorage
        }
        ```

2.  **Automatic Method (Recommended)**:
    -   Run the included helper tool (if available): `get_cookies.exe` (Windows).
    -   Or use the `agent_chrome.py` script in "Interactive Mode" to log in manually, then dump the session (feature pending).

**Important Note on HttpOnly Cookies**:
The agent injects cookies via a Chrome Extension bridge. Some `HttpOnly` cookies cannot be injected this way due to browser security. If you find the agent is not logged in:
-   Ensure you have copied **all** cookies.
-   You may need to log in manually *once* inside the Agent's controlled browser window.

---

## 4. Environment Variables (Optional)

If you prefer using `.env` files or system environment variables:
-   **`OPENAI_API_KEY`**: Can be used instead of `searcher_api.txt`.
-   **`MCP_BRIDGE_PATH`**: (Future feature) To avoid hardcoding the path in Python files.

---

## 5. Troubleshooting

-   **"Connection Refused"**: Ensure the backend server (`agent_server.py`) is running.
-   **"Bridge Error"**: Check your Node.js path in Step 1.
-   **"Agent not responding"**: Check your API Key in Step 2.

-   `auth.json` in the root directory.

**How to get it:**
1.  Log in to [xiaohongshu.com](https://www.xiaohongshu.com) in your Chrome browser.
2.  Use a cookie export tool (EditThisCookie, or the provided `get_cookies.exe` if compatible) to export your cookies.
3.  Save them as `auth.json`.
4.  **Format**: The file should be a JSON array of cookie objects (standard Puppeteer/Selenium format).

---

## 4. Chrome Setup

The agent connects to an existing Chrome instance via the MCP Bridge.

**Requirement:**
-   You must have **Google Chrome** installed.
-   For best results, close all Chrome windows and start one with **Remote Debugging** enabled (though the bridge often handles this, manual startup is more reliable).

**Windows Command:**
```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

---

## 5. Python Environment

**Recommended:** Use Conda or venv.

```bash
# Install dependencies
pip install langchain langchain-openai langgraph mcp fastapi uvicorn requests
```

## 6. Frontend Environment

**Location:** `sns-agent/` folder.

```bash
cd sns-agent
npm install
```
