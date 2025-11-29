import json
import asyncio

AUTH_FILE = "auth.json"

def load_auth_data():
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading auth.json: {e}")
        return None

async def inject_session(mcp_session):
    """
    Injects cookies and localStorage from auth.json into the current browser session.
    """
    data = load_auth_data()
    if not data:
        return "Error: auth.json not found or invalid."

    # 1. Open XHS in a new window to ensure we are on the right origin
    # We use chrome_navigate with newWindow=True
    print("Opening XHS to inject session...")
    await mcp_session.call_tool("chrome_navigate", arguments={"url": "https://www.xiaohongshu.com", "newWindow": True})
    
    # Wait for the window to be ready (simple sleep for now, ideally we check tabs)
    await asyncio.sleep(3)
    
    # 2. Prepare Injection Script
    # We need to find the localStorage for www.xiaohongshu.com
    target_origin = "https://www.xiaohongshu.com"
    local_storage_items = []
    
    if "origins" in data:
        for origin_data in data["origins"]:
            if origin_data.get("origin") == target_origin:
                local_storage_items = origin_data.get("localStorage", [])
                break
    
    # Prepare Cookies (Non-HttpOnly)
    cookies = data.get("cookies", [])
    valid_cookies = [c for c in cookies if not c.get("httpOnly") and "xiaohongshu.com" in c.get("domain", "")]

    js_script = f"""
    console.log("Starting Session Injection...");
    
    // 1. Clear existing (optional, but safer)
    // localStorage.clear(); 
    
    // 2. Set LocalStorage
    const lsData = {json.dumps(local_storage_items)};
    lsData.forEach(item => {{
        localStorage.setItem(item.name, item.value);
    }});
    
    // 3. Set Cookies
    const cookies = {json.dumps(valid_cookies)};
    cookies.forEach(c => {{
        let cookieStr = `${{c.name}}=${{c.value}}; path=${{c.path || '/'}}`;
        if (c.domain) cookieStr += `; domain=${{c.domain}}`;
        if (c.expires) cookieStr += `; expires=${{new Date(c.expires * 1000).toUTCString()}}`;
        document.cookie = cookieStr;
    }});
    
    console.log("Injection Complete. Reloading...");
    // location.reload(); // We will reload from Python to be sure
    """
    
    # 3. Inject Script
    # We assume the new window is the active one (which it should be)
    print("Injecting script...")
    await mcp_session.call_tool("chrome_inject_script", arguments={
        "type": "MAIN",
        "jsScript": js_script
    })
    
    # 4. Reload to apply changes
    await asyncio.sleep(1)
    await mcp_session.call_tool("chrome_navigate", arguments={"refresh": True})
    
    return "Session injected successfully! (Note: HttpOnly cookies cannot be injected via this method, so full login might not persist if session relies on them.)"
