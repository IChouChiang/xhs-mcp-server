# Xiaohongshu (XHS) MCP Agent

An advanced AI Agent that controls a local Chrome/Edge browser to automate tasks on Xiaohongshu (Little Red Book). Built with **LangGraph**, **MCP (Model Context Protocol)**, and **DeepSeek-V3**.

## 🚀 Features

- **Dual Interface**:
  - **CLI (`agent_chrome.py`)**: A robust command-line chat interface.
  - **Web UI (`web_ui.py`)**: A modern Streamlit-based web interface.
- **Smart Browser Control**: Uses `mcp-chrome-bridge` to control a real browser instance.
- **Advanced Tools**:
  - `extract_images_from_page`: Detects hidden images (CSS backgrounds, lazy-loaded) that standard scrapers miss.
  - `download_file`: Downloads files/images directly to your local disk with anti-hotlink headers.
  - `chrome_navigate`, `chrome_click`, `chrome_fill`: Full browser interaction.
- **Robustness**:
  - **Auto-Retry**: Handles timeouts and page loading issues.
  - **Session Injection**: Automatically loads `auth.json` cookies to keep you logged in.
  - **New Window Policy**: Always opens tasks in a new window to prevent interference.

## 🛠️ Prerequisites

1.  **Python 3.10+**
2.  **Node.js** (for the bridge)
3.  **Chrome or Edge Browser**
4.  **DeepSeek API Key** (saved in `searcher_api.txt`)

## 📦 Installation

1.  **Install Python Dependencies**:
    ```bash
    pip install langchain langchain-openai langgraph mcp streamlit requests
    ```

2.  **Install MCP Chrome Bridge**:
    ```bash
    npm install -g mcp-chrome-bridge
    # Ensure the bridge is built and accessible (see agent_core.py config)
    ```

3.  **Configure API Key**:
    Create a file named `searcher_api.txt` in the root directory and paste your DeepSeek API key.

4.  **Prepare Cookies**:
    Save your XHS cookies into `auth.json` (using the provided Go tools or manual export) to enable authenticated browsing.

## 🏃 Usage

### 1. CLI Agent (Command Line)
Best for quick testing and debugging.
```powershell
python agent_chrome.py
```

### 2. Web UI (Streamlit)
A user-friendly chat interface.
```powershell
streamlit run web_ui.py
```

## 📂 Project Structure

- **`agent_core.py`**: The "Brain". Contains the tool definitions, graph logic, and system prompts.
- **`agent_chrome.py`**: The CLI entry point.
- **`web_ui.py`**: The Web UI entry point.
- **`session_manager.py`**: Handles cookie injection.
- **`scripts/`**: PowerShell scripts for setup and registration.
- **`archive/`**: Old versions and deprecated files.

## 💡 Tips

- **Image Downloading**: The agent is optimized to find hidden images on XHS. Just ask it to "find and download images".
- **Navigation**: The agent will always open a new window. Do not close it manually while the agent is working.

