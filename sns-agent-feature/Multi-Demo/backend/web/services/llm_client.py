"""LLM client abstraction used by multiple agents."""
from __future__ import annotations

import asyncio
import textwrap
from typing import Optional

try:  # Optional dependency for environments without OpenAI installed.
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[misc]

from ..config import Settings
from ..utils.logger import get_logger


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = get_logger("services.LLMClient")
        self._client = None
        if OpenAI and settings.llm_api_key:
            self._client = OpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )
        else:
            if not OpenAI:
                self._logger.warning("openai SDK not installed, using offline stub")
            elif not settings.llm_api_key:
                self._logger.warning("LLM_API_KEY missing, using offline stub")

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> str:
        if not self._client:
            return self._offline_stub(user_prompt)

        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=model or self._settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
            )
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as exc:  # pragma: no cover - logging only
            self._logger.error("LLM request failed: %s", exc)
            return self._offline_stub(user_prompt)

    def _offline_stub(self, user_prompt: str) -> str:
        preview = textwrap.shorten(user_prompt, width=160, placeholder="…")
        return textwrap.dedent(
            f"""
            【离线模拟输出】
            {preview}
            （提示：配置 LLM_API_KEY 以启用真实模型调用）
            """
        ).strip()
