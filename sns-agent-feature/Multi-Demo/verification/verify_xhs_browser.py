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
    
    # 2. Run a General Search Verification (Google)
    print(f"🔍 Starting General Search Verification (Google)...")
    
    task_description = """
    You are conducting a General Search Verification Test.
    
    1. `chrome_navigate`: Go to 'https://www.google.com' (newWindow=True).
    2. `chrome_fill_or_select`: Find the search bar (usually 'textarea[name="q"]' or 'input[name="q"]') and type 'China GDP 2024'.
    3. `chrome_keyboard`: Press 'Enter' to submit.
    4. `chrome_get_web_content`: Wait for results, then read the page content.
    5. `chrome_get_interactive_elements`: Find the first organic search result link.
    6. `chrome_click_element`: Click that link.
    7. `chrome_get_web_content`: Read the title of the new page.
    
    REPORT: Return the Title and URL of the page you ended up on.
    """
    
    try:
        # This call should trigger the full browser automation flow
        result = await browser.run_custom_task(task_description)
        
        print("\n✅ Browser Task Completed.")
        print("--- Raw Agent Output ---")
        print(result[:2000] + "..." if len(result) > 2000 else result)
        print("------------------------")
        
    except Exception as e:
        print(f"\n❌ Browser Search Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_xhs_search())
