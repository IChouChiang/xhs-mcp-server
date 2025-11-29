# Usage Guide

## Running the Chrome Agent

The `agent_chrome.py` script connects to your running Edge browser and performs tasks using the MCP protocol.

### 1. Prepare the Browser
*   Open Microsoft Edge.
*   Ensure the MCP Extension icon is **Green**.
*   Open a tab to `https://www.xiaohongshu.com` (or leave it open).

### 2. Run the Agent
Use your configured Python environment. If using Anaconda:

```powershell
& "E:\DevTools\anaconda3\envs\xhs_env\python.exe" agent_chrome.py "Your task here"
```

**Examples:**

*   **Search:**
    ```powershell
    ... agent_chrome.py "Open xiaohongshu.com and search for 'Python tutorials'"
    ```

*   **Navigate:**
    ```powershell
    ... agent_chrome.py "Go to google.com"
    ```

### Troubleshooting

*   **"Connection Refused" / Timeout**: The agent is now configured to use `Stdio` (Standard Input/Output) instead of HTTP/SSE. This launches the Node.js bridge directly as a subprocess, which is more stable.
*   **Browser "Stuck"**: If the agent says the browser is on `127.0.0.1`, manually click a link or open a new tab in Edge to "wake up" the active tab state.
