"""FastAPI entry point for the backend service."""
from __future__ import annotations

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .orchestrator import Orchestrator
from .schemas import GenerationRequest, GenerationResponse, IPProfile
from .services.llm_client import LLMClient
from .services.mcp_tools import MCPToolExecutor
from .services.browser import BrowserService
from .services.storage import StorageClient
from .utils.logger import get_logger

settings: Settings = get_settings()
logger = get_logger("web.main")
storage = StorageClient(settings.storage_path)
llm_client = LLMClient(settings)
browser_service = BrowserService(settings)

mcp_executor = MCPToolExecutor(
    llm_client=llm_client,
    browser_service=browser_service,
    pinterest_token=settings.mcp_pinterest_token,
    platform_token=settings.mcp_platform_token,
)
orchestrator = Orchestrator(
    settings=settings,
    llm_client=llm_client,
    storage=storage,
    mcp_executor=mcp_executor,
)

app = FastAPI(title="IP Orchestrator", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    await browser_service.start()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "environment": settings.environment}


@app.get("/ip-profiles", response_model=List[IPProfile])
async def list_ip_profiles() -> List[IPProfile]:
    return orchestrator.ip_agent.list_profiles()


@app.get("/sessions")
async def list_sessions() -> list:
    return storage.list_sessions()


@app.post("/orchestrate", response_model=GenerationResponse)
async def orchestrate(request: GenerationRequest) -> GenerationResponse:
    logger.info("Received orchestrate request")
    return await orchestrator.run(request)
