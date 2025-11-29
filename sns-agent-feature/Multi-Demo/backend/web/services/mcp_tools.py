"""Minimal MCP tool wrappers used by the research agent."""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import List, Optional

from ..utils.logger import get_logger


@dataclass
class MCPRecord:
    topic: str
    source: str
    title: str
    url: str
    summary: str


class MCPToolExecutor:
    """Thin wrapper around hypothetical MCP integrations.

    The current implementation keeps things simple and generates
    deterministic mock data when API tokens are not configured.
    """

    def __init__(
        self,
        *,
        pinterest_token: Optional[str] = None,
        platform_token: Optional[str] = None,
    ) -> None:
        self._pinterest_token = pinterest_token
        self._platform_token = platform_token
        self._logger = get_logger("services.MCPToolExecutor")

    async def search(self, topic: str, platform: str) -> List[MCPRecord]:
        if not topic.strip():
            return []

        if not self._has_credentials:
            return [self._mock_record(topic, platform)]

        return await asyncio.to_thread(self._remote_search, topic, platform)

    @property
    def _has_credentials(self) -> bool:
        return bool(self._pinterest_token or self._platform_token)

    def _mock_record(self, topic: str, platform: str) -> MCPRecord:
        seed = abs(hash(topic + platform)) % 10_000
        random.seed(seed)
        adjectives = ["新鲜", "爆火", "前沿", "深潜", "实操"]
        keywords = random.sample(
            ["策略", "案例", "数据", "灵感", "趋势", "打法"], k=3
        )
        title = f"{random.choice(adjectives)} {topic} {keywords[0]}"
        summary = (
            f"基于 {platform} 热度信号，{topic} 相关的 {keywords[1]} 和 {keywords[2]} "
            "值得重点关注。"
        )
        url = f"https://{platform}.example.com/search?q={topic}"
        return MCPRecord(
            topic=topic,
            source=platform,
            title=title,
            url=url,
            summary=summary,
        )

    def _remote_search(self, topic: str, platform: str) -> List[MCPRecord]:  # pragma: no cover
        self._logger.info("Calling MCP service", extra={"topic": topic, "platform": platform})
        # Placeholder for real MCP API call. The method returns an empty list for now.
        return []
