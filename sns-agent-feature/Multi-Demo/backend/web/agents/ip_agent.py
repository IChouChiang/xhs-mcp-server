# agents/ip_agent.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..schemas import IPProfile
from .base import BaseAgent


# ===== 默认 IP 画像（可按需挪到 profile_store 里） =====

PRESET_IP_PROFILE = {
    "id": "conscious-architect",
    "name": "意识架构师 FF",
    "role": "探索意识结构与表达系统的跨学科创意者、创始人型创作者",
    "mission": (
        "以个体意识为核心，构建可复用的“意识表达系统”，把创作者的能量沉淀为"
        "作品、产品与数字分身，实现长期表达自由与商业自主。"
    ),
    "values": ["创造力", "理想主义", "美学", "洞察力", "成长性", "主权意识"],
    "style": "美学化、隐喻、极简但深、空间叙事感强，强调意识结构与多重人格视角。",
    "keywords": [
        "意识建筑师",
        "自我叙事",
        "未来意识",
        "跨学科创作",
        "个人品牌",
        "数字分身 Agent",
    ],
    "target_audience": (
        "自由职业者、早期创始人、自我探索者、热爱美学与设计的人，"
        "希望把意识与才华变成可增长资产的创作者。"
    ),
    "taboo": [
        "流水线内容",
        "廉价鸡汤式表达",
        "审美粗糙、没有人格感的内容",
        "过度迎合流量而牺牲自洽度",
    ],
}


def _build_ip_dev_path(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据《创作者IP自孵化方案》生成 IP 发展路径（简化版）。
    这里只返回静态结构，如果你后面想按 profile 做个性化可以再细化。
    """
    return {
        "business_routes": {
            "short_term": "创意服务：UI/UX、视觉与品牌、空间氛围设计，外加轻咨询式个人品牌辅导。",
            "mid_term": (
                "数字产品：AI 工具 + 创意模板、意识系统图谱与原型卡片、"
                "Agent 人格镜像/心理之旅等可复用数字体验。"
            ),
            "long_term": (
                "长线项目：个人网站作为创意空间入口，内容矩阵构成生态，"
                "以 IP 分身 Agent 和意识引擎作为长期复利资产。"
            ),
        },
        "product_routes": {
            "light": "1–4 周：表达体系模版、高维→低维转译、创意工作流模板、意识图谱卡片。",
            "medium": "1–3 月：AI 创作者工作流包、创始人 IP 孵化课程、自我探索数字手册。",
            "heavy": "长期：人格分身 Agent + 创始人意识引擎。",
        },
        "twelve_week_plan": [
            "Week 1–2：IP 画像定稿 + 内容风格统一",
            "Week 3–4：建立内容矩阵，启动多平台发布（小红书 / X / 抖音）",
            "Week 5–6：Framer 个人网站上线，作为创意空间与内容中枢",
            "Week 7–8：第一批轻产品上线（模版/卡片/工作流）",
            "Week 9–12：IP 分身 Agent V1 训练与迭代",
        ],
    }


class IPAgent(BaseAgent):
    """
    IP agent = 调度大脑 + 画像更新 + 闭环控制
    - 通过 res / cr 的循环，让 IP 画像和内容一起迭代
    """

    def __init__(self, llm, profile_store, research_agent, creator_agent):
        super().__init__(llm)
        self.profile_store = profile_store
        self.research_agent = research_agent
        self.creator_agent = creator_agent

    def list_profiles(self) -> List[IPProfile]:
        """Return list of available IP profiles."""
        # Currently returning the single preset profile
        # In future, this should query self.profile_store
        return [IPProfile(**PRESET_IP_PROFILE)]

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        IP agent 的 run = 整个闭环链路（包含循环）
        payload 约定：
        {
          "user_id": "...",
          "user_input": "...",   # 文本或上游结果（字符串）
          "mode": "suggest" | "edit" | "image" | "publish"
        }
        """

        user_id = payload["user_id"]
        user_input = payload["user_input"]
        mode = payload.get("mode", "suggest")

        # Step 0：获取 / 初始化画像
        profile = self.profile_store.get_profile(user_id)
        if profile is None:
            profile = self.profile_store.create_profile(user_id, PRESET_IP_PROFILE)

        # IP 发展路径（静态结构）
        ip_dev_path = _build_ip_dev_path(profile)

        # 循环上下文
        loop = True
        loop_count = 0
        max_loop = 3   # 可调
        final_outputs: Dict[str, Any] = {}

        # 循环开始
        while loop and loop_count < max_loop:
            loop_count += 1

            # ====== (1) 用大模型决定本轮任务 ======
            task = await self._decide_next_step(profile, user_input, mode)
            # task 结构：
            # {
            #   "research_input": {...},
            #   "creator_input": {...},
            #   "profile_patch": {...},
            #   "next_action": "res" / "cr" / "finish",
            #   "continue": true/false
            # }

            # 画像更新
            profile_patch = task.get("profile_patch")
            if profile_patch:
                profile = self.profile_store.update_profile(user_id, profile_patch)

            # ====== (2) 按 next_action 触发对应 agent ======
            next_action = task.get("next_action", "finish")

            if next_action == "res":
                res_result = await self.research_agent.run(task["research_input"])
                final_outputs[f"research_round_{loop_count}"] = res_result
                # 研究结果注入下一轮输入
                user_input = json.dumps(res_result, ensure_ascii=False)

            elif next_action == "cr":
                creator_payload = {
                    **task.get("creator_input", {}),
                    "profile": profile,
                }
                cr_result = await self.creator_agent.run(creator_payload)
                final_outputs[f"creator_round_{loop_count}"] = cr_result
                # 创作结果回流给 IP agent（例如给下一轮做研究或二次创作）
                user_input = json.dumps(cr_result, ensure_ascii=False)

            elif next_action == "finish":
                loop = False
                break

            # 是否进入下一轮循环
            loop = bool(task.get("continue", False))

        # ====== (3) 返回整合结果 ======
        return {
            "ip_profile": profile,
            "ip_dev_path": ip_dev_path,
            "loop_count": loop_count,
            "steps": final_outputs,
        }

    async def _decide_next_step(
        self,
        profile: Dict[str, Any],
        user_input: str,
        mode: str,
    ) -> Dict[str, Any]:
        """
        IP agent 的大脑：
        - 决定任务分解
        - 决定下一步调用 res / cr / 结束
        - 决定是否循环
        """

        messages = [
            {
                "role": "system",
                "content": """
你是 IP agent，你是整个系统的调度控制中心。

你必须严格输出一个 JSON（不要多余文本）：
{
  "research_input": {...},   // 如需调用 research agent，没有就用 {}
  "creator_input": {...},    // 如需调用 creator agent，没有就用 {}
  "profile_patch": {...},    // 对画像的更新，没有就用 {}
  "next_action": "res" | "cr" | "finish",
  "continue": true/false     // 是否进入下一轮循环
}

动线规则（非常重要，要内化成你的决策逻辑）：

1）mode = "suggest"（内容建议）
    - 第一步通常先调用 research agent（next_action = "res"）
        · 判断当前输入与 IP 画像是否强相关
        · 抓取相关热点话题、关键词
    - 然后进入一轮 creator agent（next_action = "cr"），生成 1-2 条简短内容建议
    - 一般不需要超过 2 轮循环，最后 next_action = "finish"，continue = false

2）mode = "edit"（内容编辑：扩写/优化/重写）
    - 如果用户原文比较粗糙或方向不清晰：先 res 再 cr
    - 如果只是语言润色：可以直接 cr
    - res 需要输出：编辑建议、结构优化思路、可以更新的人设信息，放到 profile_patch
    - cr 根据这些建议生成新版正文
    - 通常允许 1-3 轮循环（例如先结构编辑，再风格统一）

3）mode = "image"（图像生成/封面）
    - 先调用 research（next_action = "res"），去 Pinterest 等平台抓取风格参考，
      输出：参考图链接、风格关键词
    - 然后调用 creator（next_action = "cr"），生成适合 nano-banana 等模型的提示词，
      包含：构图、色调、质感、IP 角色特征
    - 一般 1-2 轮即可结束

4）mode = "publish"（一键发布）
    - 主要调用 creator（next_action = "cr"），按平台生成不同模版：
      小红书封面标题+正文、抖音脚本、X 推文等
    - 如有必要，可以先 res 分析目标平台最近热点再 cr
    - 通常 1 轮 cr + finish 即可

请根据上面的规则，结合当前画像和输入，设计本轮的 JSON。
不要解释，不要多余中文，只返回合法 JSON。
                """.strip()
            },
            {
                "role": "user",
                "content": f"""
当前画像：
{json.dumps(profile, ensure_ascii=False, indent=2)}

当前输入（可以是用户原始输入，也可能是上一轮 res/cr 的结果）：
{user_input}

当前模式：{mode}
                """.strip()
            },
        ]

        raw = await self.llm.chat(messages)
        return json.loads(raw)
