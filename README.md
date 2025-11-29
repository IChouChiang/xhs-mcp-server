# xhs-mcp-server

A Model Context Protocol (MCP) server implementation for interacting with the Xiaohongshu (Little Red Book) platform. This project aims to provide a standardized interface for AI models to access XHS data and publishing capabilities.

## Features

### Cookie Harvester Utility
Due to complex login security measures (QR code/SMS verification), this project includes a manual utility to securely capture the full browser session (cookies + local storage).

**Location:** `cmd/get_cookies/main.go`

**Usage:**
1. Run the utility:
   ```bash
   go run cmd/get_cookies/main.go
   ```
2. Two browser tabs will open:
   - Tab 1: XHS Creator Studio
   - Tab 2: XHS Explore Page
3. Log in manually on **BOTH** tabs using your preferred method (QR code or SMS).
4. Once logged in on both tabs, return to the terminal and press **Enter**.
5. The combined session state will be serialized and saved to `auth.json` in the project root.

### Login Verification
You can verify that the captured session works correctly using the check login utilities.

**Creator Studio:**
```bash
go run cmd/check_login/main.go
```

**Explore Page:**
```bash
go run cmd/check_explore/main.go
```

### MCP Server
The core of this project is the MCP server which exposes XHS functionality (like searching) to AI agents.

**Location:** `cmd/server/main.go`

**Build:**
```bash
go build -o xhs-server.exe ./cmd/server/main.go
```

### LangGraph Agent
A Python-based agent that uses LangGraph and DeepSeek-V3 to orchestrate interactions with the MCP server.

**Location:** `agent.py`

## Chrome/Edge Automation (New)

We have added support for controlling a real browser (Microsoft Edge) via the `mcp-chrome` extension. This allows for more robust automation that shares your existing login session.

### Quick Start
1.  **Setup**: Follow [docs/setup_edge_mcp.md](docs/setup_edge_mcp.md) to install the extension and register the bridge.
2.  **Run**:
    ```powershell
    & "path/to/python" agent_chrome.py "Open xiaohongshu.com and search for 'AI Tools'"
    ```

### Documentation
*   [Architecture Overview](docs/architecture.md)
*   [Setup Guide](docs/setup_edge_mcp.md)
*   [Usage Guide](docs/usage_agent.md)

## License
MIT

## Prerequisites

- Go 1.23+
- Playwright for Go
- Python 3.10+ (for the agent)
- Conda (recommended)

## Installation

### 1. Go Dependencies
1. Clone the repository.
2. Install Go dependencies:
   ```bash
   go mod download
   ```
3. Install Playwright browsers:
   ```bash
   go run github.com/playwright-community/playwright-go/cmd/playwright@latest install chromium
   ```

### 2. Python Environment (for Agent)
1. Create a Conda environment:
   ```bash
   conda create -n xhs_env python=3.11 -y
   conda activate xhs_env
   ```
2. Install Python dependencies:
   ```bash
   pip install langgraph langchain langchain_openai mcp
   ```
3. Configure API Key:
   - Create a file named `searcher_api.txt` in the root directory.
   - Paste your DeepSeek API key into it.

## Usage Workflow

1. **Harvest Cookies:** Run `go run cmd/get_cookies/main.go` and login.
2. **Build Server:** Run `go build -o xhs-server.exe ./cmd/server/main.go`.
3. **Run Agent:**
   ```bash
   # Ensure you are in the xhs_env environment
   python agent.py
   ```

