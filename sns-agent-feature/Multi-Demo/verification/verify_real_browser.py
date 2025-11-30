import asyncio
import sys
import os

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from backend.web.services.browser import BrowserService
    from backend.web.config import Settings
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def test_real_browser():
    print("🚀 Starting Real Browser Verification...")
    
    # 1. Initialize Settings & Service
    settings = Settings()
    browser = BrowserService(settings)
    
    # 2. Run a simple search
    # Note: This requires the MCP server to be running or accessible via stdio
    # and the 'searcher_api.txt' to be present for the agent to work.
    
    print("🔍 Attempting to search for 'Python' on 'google'...")
    try:
        result = await browser.search("Python", "google")
        print("\n✅ Browser Search Result:")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"\n❌ Browser Search Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_browser())
