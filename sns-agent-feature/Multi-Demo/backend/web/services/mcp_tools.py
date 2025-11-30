"""Minimal MCP tool wrappers used by the research agent."""
from __future__ import annotations

import asyncio
import json
import random
from dataclasses import dataclass
from typing import List, Optional

from ..utils.logger import get_logger
from .llm_client import LLMClient
from .browser import BrowserService


@dataclass
class MCPRecord:
    topic: str
    source: str
    title: str
    url: str
    summary: str


class MCPToolExecutor:
    """
    Hybrid Retrieval Executor.
    Routes search requests to either:
    1. AiHubMix (LLM) for general knowledge and high-speed queries.
    2. ChromeMCP (Browser) for platform-specific, anti-crawl, or visual content (XHS, Pinterest).
    """

    def __init__(
        self,
        *,
        llm_client: Optional[LLMClient] = None,
        browser_service: Optional[BrowserService] = None,
        pinterest_token: Optional[str] = None,
        platform_token: Optional[str] = None,
    ) -> None:
        self._llm_client = llm_client
        self._browser_service = browser_service
        self._pinterest_token = pinterest_token
        self._platform_token = platform_token
        self._logger = get_logger("services.MCPToolExecutor")

    async def search(self, topic: str, platform: str) -> List[MCPRecord]:
        if not topic.strip():
            return []

        # Routing Logic
        platform_lower = platform.lower()
        browser_platforms = ["xiaohongshu", "xhs", "rednote", "pinterest", "douyin", "tiktok"]
        
        use_browser = any(p in platform_lower for p in browser_platforms)

        if use_browser and self._browser_service:
            self._logger.info(f"Routing to Browser Service: {topic} on {platform}")
            return await self._search_via_browser(topic, platform)
        elif self._llm_client:
            self._logger.info(f"Routing to LLM Service: {topic} on {platform}")
            return await self._search_via_llm(topic, platform)
        else:
            self._logger.warning("No services available, falling back to mock.")
            return [self._mock_record(topic, platform)]

    async def _search_via_llm(self, topic: str, platform: str) -> List[MCPRecord]:
        """Use AiHubMix to simulate a search or retrieve general knowledge."""
        prompt = (
            f"Please act as a search engine. The user wants to search for '{topic}' on '{platform}'. "
            f"Provide 3-5 distinct search results that you would expect to find. "
            f"For each result, provide a title, a realistic URL, and a brief summary. "
            f"Return ONLY a JSON list of objects with keys: 'title', 'url', 'summary'."
        )
        try:
            response = await self._llm_client.acomplete(prompt)
            data = json.loads(response.content)
            records = []
            for item in data:
                records.append(MCPRecord(
                    topic=topic,
                    source=platform,
                    title=item.get("title", "Unknown Title"),
                    url=item.get("url", "http://example.com"),
                    summary=item.get("summary", "No summary provided.")
                ))
            return records
        except Exception as e:
            self._logger.error(f"LLM search failed: {e}")
            return [self._mock_record(topic, platform)]

    async def _search_via_browser(self, topic: str, platform: str) -> List[MCPRecord]:
        """Use ChromeMCP to browse the actual website."""
        raw_result = await self._browser_service.search(topic, platform)
        
        # Use LLM to parse the raw browser output into structured MCPRecords
        parse_prompt = (
            f"I have raw text output from a browser agent searching for '{topic}' on '{platform}'. "
            f"Please extract the structured data into a JSON list of objects with keys: 'title', 'url', 'summary'. "
            f"Raw Output:\n{raw_result}\n\n"
            f"JSON:"
        )
        try:
            response = await self._llm_client.acomplete(parse_prompt)
            # Clean up potential markdown code blocks
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            
            records = []
            for item in data:
                records.append(MCPRecord(
                    topic=topic,
                    source=platform,
                    title=item.get("title", "Browser Result"),
                    url=item.get("url", "http://example.com"),
                    summary=item.get("summary", str(item))
                ))
            return records
        except Exception as e:
            self._logger.error(f"Browser result parsing failed: {e}")
            # Fallback: return the raw text as a single record
            return [MCPRecord(
                topic=topic,
                source=platform,
                title=f"Raw Browser Result for {topic}",
                url="browser://session",
                summary=raw_result[:200] + "..."
            )]

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
