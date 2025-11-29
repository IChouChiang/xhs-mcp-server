# 🤖 Xiaohongshu (XHS) MCP Agent System

A full-stack AI Agent system for automating social media tasks (specifically Xiaohongshu). It combines a **Next.js Frontend**, a **FastAPI Backend**, and a **LangGraph/MCP Agent** to control a local Chrome browser.

![System Architecture](https://img.shields.io/badge/Architecture-Next.js%20%2B%20FastAPI%20%2B%20LangGraph-blue)

## 🌟 System Components

1.  **Frontend (`sns-agent/`)**:
    -   A modern "Canva-like" visual editor built with **Next.js 16**.
    -   Features a drag-and-drop canvas and an **AI Chat Assistant**.
    -   Communicates with the backend to "Publish" posts or "Chat" with the agent.

2.  **Backend (`agent_server.py`)**:
    -   A **FastAPI** server that exposes the Agent's capabilities via HTTP.
    -   Endpoints: `/chat` (for advice) and `/publish` (for automation).

3.  **The Agent (`agent_core.py`)**:
    -   Powered by **DeepSeek-V3** and **LangGraph**.
    -   Uses **MCP (Model Context Protocol)** to control Chrome via `mcp-chrome-bridge`.
    -   Can navigate, click, extract images, and download files.

4.  **CLI Tool (`agent_chrome.py`)**:
    -   A standalone command-line version of the agent for testing and "Auto-Pilot" mode.

---

## ⚠️ Configuration (Crucial!)

**Before running anything, you MUST configure the paths for your machine.**

👉 **[READ THE CONFIGURATION GUIDE HERE](CONFIGURATION_GUIDE.md)** 👈

*Key items to configure:*
1.  Path to `mcp-server-stdio.js` in `agent_server.py` and `agent_chrome.py`.
2.  `searcher_api.txt` (API Key).
3.  `auth.json` (Cookies).

---

## 🚀 Quick Start Guide

### Step 1: Start the Backend (Agent)

Open a terminal in the root directory (`xhs-mcp-server/`):

```powershell
# Activate your Python environment
# conda activate xhs_env
python agent_server.py
```

The server will start on `http://127.0.0.1:8000`. It runs in **Auto-Pilot Mode**, meaning it executes tools automatically without pausing for confirmation.

### Step 2: Start the Frontend

Open a new terminal in `xhs-mcp-server/sns-agent/`:

```powershell
cd sns-agent
npm run dev
```

Open `http://localhost:3000` in your browser.

### Step 3: Use the System

1.  **Chat**: Use the "AI Assistant" panel on the right to ask the agent to do things (e.g., "Search for design trends", "Add a title saying 'Hello'").
2.  **Canvas**: The agent can now **modify your canvas** directly!
3.  **Publish**: Click the "Publish" button to let the agent automate the posting process to Xiaohongshu.

---

## 📚 Documentation

-   [**Developer Guide & API Reference**](DEVELOPER_GUIDE.md) - **Start Here for Deep Dives!** Detailed analysis of file structure, API contracts, and data flow.
-   [**Configuration Guide**](CONFIGURATION_GUIDE.md) - Essential setup steps (Cookies, API Keys).
-   [**Architecture Overview**](docs/architecture.md)
-   [**Agent Usage Guide**](docs/usage_agent.md)

---

# Run the Server
python agent_server.py
```
*Wait until you see: `Agent ready with X tools.`*

### Step 2: Start the Frontend (UI)

Open a **second terminal** and navigate to the frontend folder:

```powershell
cd sns-agent

# Install dependencies (first time only)
npm install

# Start the Dev Server
npm run dev
```
*Wait until you see: `Ready in ... http://localhost:3000`*

### Step 3: Use the System

1.  Open **http://localhost:3000** in your browser.
2.  **Chat with AI**:
    -   Click the "AI Assistant" button (top right).
    -   Type: *"Search for cat images on Xiaohongshu"*.
    -   The Agent (in Terminal 1) will open Chrome, search, and reply to you in the chat.
3.  **Publish**:
    -   Create a design on the canvas.
    -   Click **Publish** -> **Xiaohongshu**.
    -   The Agent will navigate to the publish page and attempt to upload (WIP).

---

## 🛠️ Development & Debugging

### Running the CLI Agent (Auto-Pilot)
If you don't want to use the Web UI, you can run the agent directly in the terminal:

```powershell
python agent_chrome.py
```
-   **Interactive Mode**: Type commands manually.
-   **Auto-Pilot**: Type `auto` to let it run autonomously.
-   **Pause**: Press `p` to pause execution.

### Common Issues

**1. "Failed to connect to MCP server"**
-   **Cause**: The Node.js bridge path is wrong OR Chrome is not reachable.
-   **Fix**: Check `CONFIGURATION_GUIDE.md`. Ensure `mcp-server-stdio.js` path is correct. Try opening Chrome with `--remote-debugging-port=9222` manually.

**2. "Agent not initialized" (API Error)**
-   **Cause**: The Python server failed to connect to the bridge on startup.
-   **Fix**: Check the logs in Terminal 1. Restart `agent_server.py`.

---

## 📂 File Structure

```text
xhs-mcp-server/
├── agent_server.py       # 🟢 Backend API (FastAPI)
├── agent_chrome.py       # 🔵 CLI Agent Tool
├── agent_core.py         # 🧠 Agent Logic (LangGraph)
├── session_manager.py    # 🍪 Cookie Injection
├── CONFIGURATION_GUIDE.md # ⚙️ Setup Instructions
├── sns-agent/            # 🎨 Frontend (Next.js)
│   ├── app/              #    React Components
│   └── ...
└── ...
```

