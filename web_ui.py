import streamlit as st
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent_core import create_mcp_tools, build_agent_graph
from session_manager import inject_session

# --- Configuration ---
st.set_page_config(page_title="XHS MCP Agent", page_icon="🤖", layout="wide")

# Server Parameters
SERVER_PARAMS = StdioServerParameters(
    command="node",
    args=["C:\\Users\\63091\\AppData\\Roaming\\npm\\node_modules\\mcp-chrome-bridge\\dist\\mcp\\mcp-server-stdio.js"],
    env=None
)

# --- Async Helper ---
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# --- Main App ---
async def main():
    st.title("🤖 Xiaohongshu MCP Agent")

    # Initialize Session State
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("What should I do?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Run Agent
        with st.chat_message("assistant"):
            status_container = st.status("Agent is working...", expanded=True)
            
            try:
                # Connect to MCP
                async with stdio_client(SERVER_PARAMS) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        status_container.write("✅ Connected to MCP Server")
                        
                        # Inject Session
                        await inject_session(session)
                        status_container.write("✅ Session Injected")
                        
                        # Create Tools & Agent
                        tools = await create_mcp_tools(session)
                        agent = build_agent_graph(tools)
                        status_container.write(f"✅ Agent Ready ({len(tools)} tools)")
                        
                        # Run Graph
                        response_placeholder = st.empty()
                        full_response = ""
                        
                        # Convert session history to LangChain format
                        # (Simplified: just pass the last user message for now to avoid context window issues, 
                        # or pass full history if needed. Here we pass just the prompt for simplicity in this demo)
                        # Ideally, we should map st.session_state.messages to LangChain messages.
                        
                        async for event in agent.astream(
                            {"messages": [("user", prompt)]},
                            config={"recursion_limit": 50}
                        ):
                            # Tool Outputs
                            if "tools" in event:
                                for msg in event["tools"]["messages"]:
                                    status_container.write(f"🛠️ **Tool Output**: {msg.content[:200]}...")
                            
                            # Agent Thoughts/Response
                            if "agent" in event:
                                msg = event["agent"]["messages"][0]
                                full_response = msg.content
                                response_placeholder.markdown(full_response)
                        
                        status_container.update(label="Task Completed", state="complete", expanded=False)
                        
                        # Add assistant message to history
                        st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                status_container.update(label="Error", state="error")
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Windows asyncio fix
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
