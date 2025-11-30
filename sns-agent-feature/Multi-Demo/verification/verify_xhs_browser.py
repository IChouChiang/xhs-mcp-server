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

async def verify_xhs_search():
    print("🚀 Starting XHS Browser Verification...")
    print("⚠️  Please ensure your MCP Server (Node.js) is running and Chrome is closed (or ready).")
    
    # 1. Initialize Settings & Service
    settings = Settings()
    browser = BrowserService(settings)
    
    # 2. Run a search specifically for Xiaohongshu
    topic = "2025 Spring Fashion Trends"
    platform = "xiaohongshu"
    
    print(f"🔍 Attempting to search for '{topic}' on '{platform}'...")
    print("👀 Watch your screen! You should see:")
    print("   1. A new Chrome window open.")
    print("   2. Navigation to Xiaohongshu.")
    print("   3. Search query being typed.")
    
    try:
        # This call should trigger the full browser automation flow
        result = await browser.search(topic, platform)
        
        print("\n✅ Browser Task Completed.")
        print("--- Raw Agent Output ---")
        print(result[:1000] + "..." if len(result) > 1000 else result)
        print("------------------------")
        
    except Exception as e:
        print(f"\n❌ Browser Search Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_xhs_search())
