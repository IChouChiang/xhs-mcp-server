# Context
1. **The Brain:** I want to use `langgraph` to orchestrate the workflow.
2. **The LLM:** I am using **DeepSeek-V3** (via `ChatOpenAI` client with `base_url="https://api.deepseek.com"`, the api is stored in the file `searcher_api.txt`).
3. **The Tools:** we just build that could login in the explore page.

# Your Task
Write a complete Python script (`agent.py`) that implements a **ReAct Agent** using LangGraph.

# Specific Requirements
1. **MCP Integration:** - Use the `mcp` Python SDK (or `subprocess` if simpler) to connect to my local Go binary (`./xhs-server.exe`).
   - Wrap the MCP tool `xhs_search_keyword` into a standard LangChain `@tool` so the LLM can call it.

2. **The Workflow (Graph):**
   - **Input:** User provides a topic (e.g., "Github Student Verification").
   - **Node 1 (Agent):** DeepSeek decides to call the search tool.
   - **Node 2 (Tools):** Execute the tool. The Go server will open the Chrome tab to `xiaohongshu.com/search_result?keyword=...`.
   - **Loop:** The agent should verify the tool ran successfully and stop.

3. **Code Structure:**
   - Use `StateGraph` and `MessagesState`.
   - Use `ChatOpenAI` initialized with my DeepSeek API Key.
   - Include a `main` block to test it with the query: "Find tutorials for GitHub Student Verification".

# Tech Stack
- Python 3.10+
- `langgraph`, `langchain`, `langchain_openai`
- `mcp` (Python SDK)