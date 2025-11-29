# agents/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.services.llm_client import LLMClient
from ..utils.logger import get_logger

class BaseAgent(ABC):

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        self.llm = llm
        self.name = name or self.__class__.__name__
        self.description = description or ""
        self.logger = get_logger(f"agents.{self.name}")

    async def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.run(payload)

    @abstractmethod
    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic."""
        raise NotImplementedError
