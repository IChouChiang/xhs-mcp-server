"""
ResearchAgent — 轻量研究 Agent，通过 MCP 工具获取热点/图像参考，
再用 LLM 进行结构化内容整理。

功能流程：
1. 接收 topic 关键词
2. 调用 MCP 热点/图像搜索工具
3. 将原始 records 整合给 LLM
4. LLM 按 system prompt 输出统一 JSON 格式：
   {
       "summary": "...",
       "content_paths": [...],
       "hot_points": [...],
       "image_directions": [...]
   }
"""

from __future__ import annotations 
from typing import List, Optional, Any, Dict

from .base import BaseAgent
from ..schemas import ResearchFinding
from ..services.mcp_tools import MCPToolExecutor


# ============================
# Research Agent System Prompt
# ============================
RESEARCH_SYSTEM_PROMPT = """
你是 Research Agent（res ag），你的任务是将 topic 关键词 + MCP 工具搜索结果
转化为结构化的研究结论，用于支持后续的内容创作、IP 分析与图像方向输出。

========================
你的职责：
========================

1. 接收来自上游 IP Agent 的 topic（包含用户意图、研究方向与关键词）。
2. 读取 tools_results（MCP 工具返回的热点记录与图像参考记录）。
3. 基于全部原始 records 完成以下处理：
   - 内容聚合：整合不同来源的热点、文本、摘要与图像信息
   - 信息压缩：去冗余、提取高价值内容
   - 相关性筛选：聚焦与 topic 最相关的部分
   - 趋势与关键词提取：识别关键趋势、模式和可行动方向
4. 输出一个严格结构化的 JSON，供 downstream（Creator Agent / IP Agent）直接消费。

强制要求：
- 必须只输出 JSON（不得包含任何解释、额外文字或非 JSON 内容）
- JSON 字段必须完全一致，不可新增或删减
- 字段内容必须来源于 topic 或 records，不得幻觉

==========================================
JSON 字段定义（必须严格遵守）
==========================================

{
  "summary": "对 topic 的 50-120 字中文摘要。总结趋势、主题核心、用户可用的洞察。",

  "content_paths": [
    "基于 records 得出的内容方向建议（可用于内容创作或研究路径规划）",
    "每条 10-30 字，强调 angle（角度）与切入点"
  ],

  "hot_points": [
    "从热点记录中提取的高价值要点（趋势、观点、引用、数据）",
    "必须是来自原始 records 的聚合结果，不得凭空生成"
  ],

  "image_directions": [
    "基于图像参考记录整理的视觉方向建议",
    "可包括：视觉风格 / 画面元素 / 构图关键词 / 叙事线索",
    "不得生成具体人物或涉及真实身份的描述"
  ]
}

==========================================
你的目标：
==========================================
- 生成简洁、可直接使用的结构化研究结果
- 帮助 Creator Agent 快速获得创作方向、内容路径与图像方向
- 帮助 IP Agent 完成后续的内容画像与发展路径构建
- 所有输出必须真实、可靠、基于 topic 和 records

请严格按照上方规范输出 JSON。
"""



# ============================
# ResearchAgent
# ============================
class ResearchAgent(BaseAgent):
    """
    ResearchAgent：
    - 调用 MCP 搜索工具获取热点内容和图像参考
    - 将 findings 提交给 LLM
    - 输出结构化 JSON 研究结果
    """

    def __init__(
        self,
        executor: MCPToolExecutor,
        llm,
        default_platform: str = "google"
    ) -> None:
        
# --------------------------------------------
    # Step 1 — MCP 搜索：获取热点内容和图像参考
    # --------------------------------------------
    async def run(
        self,
        topics: List[str],
        *,
        platform: Optional[str] = None
    ) -> List[ResearchFinding]:

        if not topics:
            return []

        findings: List[ResearchFinding] = []

        for topic in topics:
            records = await self._executor.search(
                topic,
                platform=platform or self._default_platform
            )
            for record in records:
                findings.append(
                    ResearchFinding(
                        topic=record.topic,
                        source=record.source,
                        title=record.title,
                        url=record.url,
                        summary=record.summary,
                    )
                )

        return findings

    # --------------------------------------------
    # Step 2 — LLM 分析：结构化研究结果
    # --------------------------------------------
    async def analyze(self, findings: List[ResearchFinding]) -> Dict[str, Any]:

        formatted_records = [
            {
                "topic": f.topic,
                "source": f.source,
                "title": f.title,
                "url": f.url,
                "summary": f.summary
            }
            for f in findings
        ]

        prompt = (
            f"{RESEARCH_SYSTEM_PROMPT}\n\n"
            f"以下是外部 MCP 工具返回的搜索结果：\n"
            f"{formatted_records}\n\n"
            f"请按要求生成 JSON："
        )

        response = await self._llm.acomplete(prompt)
        return response.json()

    # --------------------------------------------
    # Step 3 — 统一入口：研究 → 结构化输出
    # --------------------------------------------
    async def research(self, topics: List[str]) -> Dict[str, Any]:
        findings = await self.run(topics)
        return await self.analyze(findings)
