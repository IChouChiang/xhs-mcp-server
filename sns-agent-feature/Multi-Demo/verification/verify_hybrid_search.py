import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from backend.web.services.mcp_tools import MCPToolExecutor
    from backend.web.services.browser import BrowserService
    from backend.web.services.llm_client import LLMClient
    from backend.web.config import Settings
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def verify_hybrid_search():
    print("🚀 Starting Hybrid Search Verification...")

    # 1. Mock Dependencies
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.acomplete = AsyncMock()
    
    mock_browser = MagicMock(spec=BrowserService)
    mock_browser.search = AsyncMock()

    # 2. Initialize Executor
    executor = MCPToolExecutor(
        llm_client=mock_llm,
        browser_service=mock_browser
    )
    print("📦 Executor initialized.")

    # 3. Test Case A: General Search (Should route to LLM)
    print("\n🧪 Test Case A: General Search ('AI Trends', 'google')")
    
    # Mock LLM response for search
    mock_llm.acomplete.return_value.content = """
    [
        {"title": "AI Trends 2025", "url": "http://ai.com", "summary": "AI is growing."}
    ]
    """
    
    results_a = await executor.search("AI Trends", "google")
    
    if len(results_a) == 1 and results_a[0].source == "google":
        print("✅ Routed to LLM correctly.")
    else:
        print(f"❌ Routing failed. Results: {results_a}")

    # 4. Test Case B: Browser Search (Should route to Browser)
    print("\n🧪 Test Case B: Browser Search ('Fashion', 'xiaohongshu')")
    
    # Mock Browser response
    mock_browser.search.return_value = "Found a post about Red Fashion."
    
    # Mock LLM response for parsing
    mock_llm.acomplete.return_value.content = """
    [
        {"title": "Red Fashion Post", "url": "http://xhs.com/1", "summary": "Found a post about Red Fashion."}
    ]
    """
    
    results_b = await executor.search("Fashion", "xiaohongshu")
    
    if len(results_b) == 1 and results_b[0].source == "xiaohongshu":
        print("✅ Routed to Browser correctly.")
        print(f"   -> Browser Output Parsed: {results_b[0].title}")
    else:
        print(f"❌ Routing failed. Results: {results_b}")

if __name__ == "__main__":
    asyncio.run(verify_hybrid_search())
