# Setup Guide: Edge Browser & MCP Extension

This guide explains how to set up the "Human-in-the-loop" automation using Microsoft Edge.

## Prerequisites
1.  **Node.js**: Installed and available in PATH.
2.  **Python**: Anaconda environment (`xhs_env`) recommended.
3.  **Microsoft Edge**.

## Step 1: Install the Extension
1.  Clone or download the `mcp-chrome` repository (or use the pre-built extension if available).
2.  Open Edge and go to `edge://extensions`.
3.  Enable **Developer Mode**.
4.  Click **Load unpacked** and select the `extension` folder from the `mcp-chrome` project.
5.  **Note the Extension ID** (e.g., `jamhCw...`).

## Step 2: Register Native Host
The browser needs permission to talk to the Node.js script on your computer.
1.  Run the `register_edge.ps1` script in this repository:
    ```powershell
    ./register_edge.ps1
    ```
    This adds the necessary Registry keys for Edge.

## Step 3: Fix Extension ID
The Native Host manifest must match your specific Extension ID.
1.  Open `fix_id.ps1`.
2.  Ensure the ID inside matches the one you saw in `edge://extensions`.
3.  Run the script:
    ```powershell
    ./fix_id.ps1
    ```

## Step 4: Verify Connection
1.  Restart Edge.
2.  Click the MCP Extension icon in the toolbar.
3.  It should show a **Green Dot** and say "Connected".

## Step 5: Python Environment
Ensure you have the required Python packages:
```bash
pip install mcp langchain langchain-openai langgraph
```
(Or use the `xhs_env` conda environment).
