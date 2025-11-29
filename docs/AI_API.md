# AI Agent API Documentation

The Agent Server (`agent_server.py`) exposes a REST API for the frontend to interact with the AI Agent.

## Base URL
`http://127.0.0.1:8000`

## Endpoints

### 1. Chat with Agent
Send a message to the agent. The agent can use tools (search, browser control, canvas modification) to fulfill the request.

- **URL**: `/chat`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body:**
```json
{
  "message": "Search for cat images and add a text box saying 'Cute Cats'"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "I have searched for cat images and added the text box to your canvas."
}
```

### 2. Publish Post
Trigger the automated publishing workflow.

- **URL**: `/publish`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body:**
```json
{
  "platform": "xhs",
  "content": "My post content...",
  "images": ["http://...", "http://..."]
}
```

## Available Tools

The agent has access to the following tools:

### Browser Control (via MCP)
- `navigate_to(url)`: Go to a website.
- `click_element(selector)`: Click an element.
- `type_text(selector, text)`: Type into an input.
- `scroll_down()`: Scroll the page.
- `get_page_content()`: Read the current page text.

### Canvas Control (Frontend Integration)
- `modify_canvas(action, data)`: Modify the user's design canvas in the Next.js frontend.
  - **Actions**: `add_text`, `add_image`, `update_element`, `delete_element`.
  - **Example**:
    ```python
    modify_canvas(action="add_text", data={"text": "Hello World", "x": 100, "y": 100})
    ```

### Search & Utilities
- `search_google(query)`: Search the web.
- `extract_images()`: Find images on the current page.

## Server Configuration

The server is configured to run in **Auto-Pilot Mode** (`interrupt=False`).
This means when the AI decides to use a tool, it executes it immediately without waiting for human approval in the terminal. This is essential for the HTTP API to function correctly without timing out.
