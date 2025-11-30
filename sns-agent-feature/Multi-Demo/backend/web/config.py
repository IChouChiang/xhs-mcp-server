"""Configuration helpers for the FastAPI backend."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    environment: str = Field(default="development", env="APP_ENV")
    llm_api_key: str = Field(default="", env="LLM_API_KEY")
    llm_model: str = Field(default="gpt-5-chat-latest", env="LLM_MODEL")
    llm_base_url: Optional[str] = Field(default="https://aihubmix.com/v1", env="LLM_BASE_URL")
    storage_path: Path = Field(
        default=Path("backend/web/.data/state.json"), env="BACKEND_STORAGE_PATH"
    )
    mcp_pinterest_token: Optional[str] = Field(
        default=None, env="MCP_PINTEREST_TOKEN"
    )
    mcp_platform_token: Optional[str] = Field(
        default=None, env="MCP_PLATFORM_TOKEN"
    )
    default_research_platform: str = Field(default="pinterest", env="DEFAULT_RESEARCH_PLATFORM")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        frozen = True

    @property
    def data_dir(self) -> Path:
        return self.storage_path.expanduser().resolve().parent


@lru_cache()
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
