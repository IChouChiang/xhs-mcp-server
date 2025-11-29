from __future__ import annotations

from typing import Optional

from .config import Settings
from .schemas import GenerationRequest, GenerationResponse, IPProfile, AgentStep, ResearchFinding
from .services.llm_client import LLMClient
from .services.mcp_tools import MCPToolExecutor
from .services.storage import StorageClient
from .agents.ip_agent import IPAgent
from .agents.research_agent import ResearchAgent
from .agents.creator_agent import CreatorAgent
from .utils.logger import get_logger


class Orchestrator:
    """
    The central coordinator that manages the lifecycle of a user request.
    It initializes the agents and routes the request through the IP Agent.
    """

    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        storage: StorageClient,
        mcp_executor: MCPToolExecutor,
    ) -> None:
        self._settings = settings
        self._llm_client = llm_client
        self._storage = storage
        self._mcp_executor = mcp_executor
        self._logger = get_logger("orchestrator")

        # Initialize Agents
        # 1. Research Agent (The Eyes) - Needs LLM and MCP Tools
        self.research_agent = ResearchAgent(
            llm=llm_client,
            executor=mcp_executor
        )

        # 2. Creator Agent (The Hands) - Needs LLM
        self.creator_agent = CreatorAgent(
            llm_client=llm_client
        )

        # 3. IP Agent (The Brain) - Needs LLM, Storage, and access to other agents
        self.ip_agent = IPAgent(
            llm=llm_client,
            profile_store=storage,
            research_agent=self.research_agent,
            creator_agent=self.creator_agent
        )

    async def run(self, request: GenerationRequest) -> GenerationResponse:
        """
        Execute the orchestration flow.
        
        The flow is primarily driven by the IP Agent, which decides:
        1. Whether to update the IP Profile.
        2. Whether to call the Research Agent.
        3. Whether to call the Creator Agent.
        """
        self._logger.info(f"Starting orchestration for input: {request.input[:50]}...")

        # Construct the payload for the IP Agent
        # We map the Pydantic request model to the dictionary format expected by IPAgent.run
        payload = {
            "user_id": "default_user", # TODO: Extract from auth context if available
            "user_input": request.input,
            "mode": "suggest", # Default mode, can be inferred or passed explicitly
            "context": {
                "user_brief": request.user_brief,
                "goal": request.goal,
                "prefer_ip_id": request.prefer_ip_id,
                "research_topics": request.research_topics
            }
        }

        # Run the IP Agent
        # The IP Agent is responsible for calling other agents and aggregating results.
        result = await self.ip_agent.run(payload)

        # Transform the dictionary result back into a GenerationResponse
        steps_dict = result.get("steps", {})
        content = ""
        steps = []
        research_notes = []

        for key, value in steps_dict.items():
            if "creator" in key:
                # Creator returns a string (content)
                content = str(value)
                steps.append(AgentStep(agent="creator", action=key, content=content))
            elif "research" in key:
                # Research returns List[ResearchFinding]
                # We serialize it for the step content
                steps.append(AgentStep(agent="research", action=key, content=str(value)))
                if isinstance(value, list):
                    research_notes.extend(value)

        return GenerationResponse(
            content=content,
            ip_profile=IPProfile(**result.get("ip_profile", {})),
            reason=f"Processed in {result.get('loop_count', 0)} loops",
            steps=steps,
            research_notes=research_notes
        )
