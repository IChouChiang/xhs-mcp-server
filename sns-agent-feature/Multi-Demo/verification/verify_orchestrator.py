import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add the project root directory to sys.path
# Assumes this script is in <project_root>/verification/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from backend.web.orchestrator import Orchestrator
    from backend.web.config import Settings
    from backend.web.schemas import GenerationRequest
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def verify():
    print("🚀 Starting Orchestrator Verification...")

    # 1. Mock Dependencies
    # We don't want to make real API calls for a structural verification
    mock_llm = MagicMock()
    mock_storage = MagicMock()
    mock_mcp = MagicMock()
    
    # Mock the Settings
    settings = Settings(
        llm_api_key="test_key",
        llm_model="gpt-5-chat-latest",
        storage_path="backend/web/.data/state.json"
    )

    print("📦 Dependencies mocked.")

    # 2. Initialize Orchestrator
    try:
        orchestrator = Orchestrator(
            settings=settings,
            llm_client=mock_llm,
            storage=mock_storage,
            mcp_executor=mock_mcp
        )
        print("✅ Orchestrator initialized successfully.")
    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        return

    # 3. Verify Agent Initialization
    if orchestrator.ip_agent and orchestrator.research_agent and orchestrator.creator_agent:
        print("✅ All internal agents (IP, Research, Creator) instantiated.")
    else:
        print("❌ Some agents failed to instantiate.")
        return

    # 4. Test a simple run (Dry Run)
    # We mock the ip_agent.run method to avoid complex logic, 
    # just to verify the orchestrator's run method wiring.
    
    # Mocking the return value of ip_agent.run to match what Orchestrator expects
    orchestrator.ip_agent.run = MagicMock()
    
    # We need to make the mock awaitable since ip_agent.run is async
    future = asyncio.Future()
    future.set_result({
        "content": "Test Content",
        "ip_profile": {
            "id": "test-id",
            "name": "Test Agent",
            "role": "Tester",
            "mission": "Testing",
            "values": ["Test"],
            "style": "Testy",
            "keywords": ["test"],
            "targetAudience": "Testers", # Note: alias in schema
            "taboo": []
        },
        "reason": "Test Reason",
        "steps": {
            "research_round_1": [{"topic": "test", "source": "test", "title": "test", "url": "http://test", "summary": "test"}],
            "creator_round_1": "Created content"
        },
        "loop_count": 1
    })
    orchestrator.ip_agent.run.return_value = future

    req = GenerationRequest(
        input="Test input",
        user_brief="Brief",
        goal="Goal",
        prefer_ip_id="test-id",
        research_topics=["topic1"]
    )

    print("🔄 Attempting to run orchestrator flow...")
    try:
        response = await orchestrator.run(req)
        print("✅ Orchestrator.run() executed successfully.")
        print(f"   -> Response Content: {response.content}")
        print(f"   -> Response Reason: {response.reason}")
    except Exception as e:
        print(f"❌ Orchestrator.run() failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())
