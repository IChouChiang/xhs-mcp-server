"""Agent responsible for generating IP-aligned content."""
from __future__ import annotations

import textwrap
from typing import Optional, Literal

from ..schemas import IPProfile
from ..services.llm_client import LLMClient
from .base import BaseAgent


# cr ag 支持的动作模式：
# - "suggest": 内容建议（强相关 / 不相关 分支）
# - "edit_text": 文本扩写 / 优化
# - "publish": 一键发布（多平台文案 + nano banana 封面提示词）
# - "edit_image": 图像编辑提示词
CreatorMode = Literal["suggest", "edit_text", "publish", "edit_image"]


class CreatorAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(
            "Creator Agent",
            (
                "Produces drafts and creative prompts following the IP profile, "
                "using research outputs from the Research Agent."
            ),
        )
        self._llm = llm_client

    async def run(
        self,
        *,
        mode: CreatorMode,
        user_input: str,
        ip_profile: IPProfile,
        research_notes: Optional[str] = None,
    ) -> str:
        """
        :param mode: cr ag 当前要执行的动作类型：
            - "suggest"    用户执行【内容建议动作】
            - "edit_text"  用户提出【内容编辑 / 扩写 / 优化】需求
            - "publish"    用户执行【一键发布】需求
            - "edit_image" 用户提出【图像编辑】需求
        :param user_input: 用户本次输入内容 / 需求说明
        :param ip_profile: 用户 IP 画像（价值观、风格、禁忌等）
        :param research_notes: res ag 产出的研究报告 / 热点分析 / 图像库分析等
        :return: 由 LLM 生成的文本（可以是文案、结构化 JSON 或提示词）
        """

        system_prompt = self._build_system_prompt(ip_profile)
        user_prompt = self._build_user_prompt(
            mode=mode,
            user_input=user_input,
            research_notes=research_notes,
        )

        return await self._llm.generate(system_prompt, user_prompt)

    # --------------------------------------------------------------------- #
    # prompt 组装逻辑
    # --------------------------------------------------------------------- #

    def _build_system_prompt(self, ip_profile: IPProfile) -> str:
        """构建与 IP 画像对齐的 system prompt。"""

        values = "、".join(ip_profile.values)
        keywords = "、".join(ip_profile.keywords)
        taboo = "、".join(ip_profile.taboo or []) or "无"

        return textwrap.dedent(
            f"""
            你是一个多平台内容创作者（Creator Agent），
            负责在给定的 IP 设定下，产出高质量、可直接使用的内容与提示词。

            [IP 画像]
            - 品牌核心价值：{values}
            - 品牌关键词：{keywords}
            - 禁忌与需要避免的话题：{taboo}

            创作要求：
            1. 所有内容必须符合以上 IP 画像；
            2. 尽量使用自然、真实、有个性的中文表达；
            3. 适配常见内容平台（如小红书 / 抖音 / 即刻 / X 等）的阅读习惯；
            4. 输出时避免虚假承诺、极端观点和敏感话题。
            【X（Twitter）】
            内容框架：
            - 一句核心观点（强观点、可讨论、鲜明态度）
            - 补充解释（1-2句）
            - 若为 Thread：按主题分成 3–10 条，每条一个观点点

             - 当本轮任务的 mode 为 "publish"，或者用户明确触发「一键发布」「自动发布到平台」等指令时：
          1. 你需要基于已经生成好的 multi_platform_drafts（如：xiaohongshu / x / jike / douyin 等）判断哪些平台需要发布。
          2. 对于需要发布的平台，优先直接调用可用的浏览器 / Chrome 类 MCP 工具，执行以下操作：
             - 打开该平台的网页版发布页面（例如小红书创作中心、X 发帖界面、即刻发帖页面、抖音 PC 端发布页等）。
             - 将对应草稿中的标题 / 正文 / 标签 / 话题 / 封面文案，按平台字段填入表单。
             - 如有配图或封面图，使用可用的上传 / 粘贴图片 URL 的能力完成图片填充。
          3. 如果 Chrome MCP 工具支持点击发布，你可以尝试在填完之后调用提交 / 发布按钮；
             若不支持，则在完成所有内容填写后停在「已完成填充、等待用户人工确认」的状态。
          4. 在模型输出中，只需要简要说明每个平台的发布结果状态（如：已尝试发布 / 已完成填充等待确认），
             不必再重复输出全文内容。

             形式依据这些 

            形式要求：
            - 文字
            - 字数：30–120 字
            - 可附带：截图、信息图、简洁视觉

            偏好：
            - 强观点、洞察性句子、热点话题、讨论度高的内容

            --------------------------------
            【小红书】
            内容框架：
            - 标题：情绪 + 场景 + 钩子
            - 开头悬念：1–2句
            - 主体：故事 / 清单 / 方法论（分段呈现）
            - 结尾总结 + CTA（收藏/关注/评论）

            形式要求：
            - 图文：6–9 张图（如需图像需生成封面图+内容配图）
            - 视频：9–30 秒
            - 审美：真实自然、亲和力、轻生活方式

            偏好：
            - 情绪、生活方式、干货可保存、个人表达、审美风格一致

            --------------------------------
            【抖音】
            内容框架：
            - 1 秒钩子（开头必须强力吸睛）
            - 核心价值（一句话告诉用户你要说什么）
            - 故事 / 教程 / 展示（快速节奏）
            - 结尾总结 + CTA（关注/点赞/看下集）

            形式要求：
            - 图片
            - 简短文字
    
            偏好：
            - 情绪刺激、爽点、惊讶反转、节奏快、信息密度高

            --------------------------------
            【即刻】
            内容框架：
            - 一句观点（松弛、真诚）
            - 1–3 段轻补充文本
            - 小故事/场景句（氛围感）

            形式要求：
            - 轻文本 + 1 张氛围图
            - 布局简洁美观

            偏好：
            - 真实、不用力、轻思想、小众审美

            """
        ).strip()

    def _build_user_prompt(
        self,
        *,
        mode: CreatorMode,
        user_input: str,
        research_notes: Optional[str],
    ) -> str:
        """根据动作链路，拼装 user prompt。"""

        research_block = ""
        if research_notes:
            # 来自 res ag 的内容分析 / 热点报告 / 图像库分析等
            research_block = textwrap.dedent(
                f"""
                [来自 Research Agent 的分析]
                {research_notes.strip()}
                """
            ).strip()

        if mode == "suggest":
            # 对应「用户执行内容建议动作」的两种分支：
            # 1. 强相关：research_notes 中已经包含“与当前 IP 强相关的热点/关键词”
            # 2. 不相关：research_notes 中提供“IP 框架中最近热点话题”或“发展方向建议”
            return textwrap.dedent(
                f"""
                现在用户希望获得「内容选题/方向建议」。

                [用户当前输入]
                {user_input.strip()}

                {research_block}

                你的任务：
                1. 先根据研究分析判断：用户输入与当前 IP / 热点是否“强相关”还是“相关度较低”；
                2. 在此基础上给出 1-2 条具体的内容创作选题或方向建议；
                3. 每条建议要包含：
                   - 一个简短标题（不超过 15 个字）
                   - 1~2 句解释：为什么这个选题适合当前 IP？可以怎么展开？
                4. 用 JSON 数组的形式返回，例如：
                   [
                     {{
                       "type": "strong_related|weak_related",
                       "title": "...",
                       "reason": "...",
                       "outline": ["要点1", "要点2"]
                     }}
                   ]
                只输出合法 JSON，不要额外解释文字。
                """
            ).strip()

        if mode == "edit_text":
            # 对应「内容编辑」：扩写 / 优化 / 重写 文本
            return textwrap.dedent(
                f"""
                现在用户需要对一段内容进行「扩写 / 优化 / 重写」。

                [用户原始内容或需求]
                {user_input.strip()}

                {research_block}

                你的任务：
                1. 判断用户更偏向哪种需求：扩写、精简优化、风格统一、逻辑重组等；
                2. 在不改变核心事实与态度的前提下，对内容进行改写；
                3. 语言风格要与 IP 画像一致，可略带个性和情绪，但避免攻击性；
                4. 返回结构：
                   {{
                     "mode_inferred": "expand|polish|rewrite|mix",
                     "edited_text": "...优化后的完整文本...",
                     "suggest_notes": [
                       "这段内容适合发布的平台类型建议",
                       "可以进一步搭配什么类型的图片/封面"
                     ]
                   }}
                只输出合法 JSON。
                """
            ).strip()

        if mode == "publish":
            # 对应「一键发布」：多平台文案 + nano banana 封面提示词
            return textwrap.dedent(
                f"""
                现在用户要执行「一键发布」。

                [用户确认要发布的核心内容]
                {user_input.strip()}

                {research_block}

                你的任务：
                1. 基于 IP 画像和研究分析，为以下平台分别生成适配的发布文案：
                   - 小红书
                   - 抖音短视频脚本提纲
                   - X
                   
                2. 为 nano banana 图像生成工具生成 1 份通用封面提示词：
                   - 包含：主体元素、画面构图、风格（如「胶片感」「插画风」「极简排版」）、色调等；
                   - 用英文关键词 + 少量中文补充说明均可；
                3. 输出 JSON 结构示例：
                   {{
                     "platform_posts": {{
                       "xiaohongshu": {{
                         "title": "...",
                         "body": "..."
                       }},
                       "douyin": {{
                         "hook": "...",
                         "script_outline": ["镜头1", "镜头2"]
                       }},
                       "bilibili": {{
                         "title": "...",
                         "description": "..."
                       }},
                       "instagram": {{
                         "caption": "...",
                         "hashtags": ["#tag1", "#tag2"]
                       }}
                     }},
                     "nano_banana_prompt": "...给 nano banana 的英文/中英文混合提示词..."
                   }}
                只输出合法 JSON。
                """
            ).strip()

        if mode == "edit_image":
            # 对应「图像编辑需求」：根据 res ag 找到的风格图像 + 用户需求，生成编辑/生成提示词
            return textwrap.dedent(
                f"""
                现在用户需要进行「图像编辑 / 生成」。
                MCP 工具已经通过 res ag 从 Pinterest 等渠道找到了若干参考风格图像，
                并在研究报告中进行了总结。

                [用户的图像编辑 / 生成需求]
                {user_input.strip()}

                {research_block}

                你的任务：
                1. 综合 IP 画像、参考图像风格总结以及用户说明；
                2. 生成适合 nano banana 的图像提示词，用于：
                   - 封面图片
                   - 内页配图（如果用户有此类需求）
                3. 提示词需要包括：
                   - 主题内容（人/物/场景简要描述）
                   - 构图与镜头感（如「居中主体」「俯视视角」「留白」等）
                   - 风格（如「Pinterest 风格」「极简海报」「手绘插画」「电影感」等）
                   - 色彩气氛（如「高饱和」「莫兰迪配色」「暖色调」等）
                   - 需要避免的元素（结合 IP taboo）
                4. 返回 JSON 结构示例：
                   {{
                     "nano_banana_prompts": [
                       {{
                         "usage": "cover",
                         "prompt": "...适合封面的英文/中英文提示词...",
                         "avoid": ["不希望出现的元素1", "元素2"]
                       }},
                       {{
                         "usage": "inline_image",
                         "prompt": "...适合内页配图的提示词...",
                         "avoid": ["..."]
                       }}
                     ]
                   }}
                只输出合法 JSON。
                """

                f"""
        用户请求执行「一键发布」。

        你已经在前一步完成了内容创作，并生成了 multi_platform_drafts，
        包含以下平台的内容（用于自动发布，不要在输出中重复内容）：
        - 小红书（xiaohongshu）
        - X（twitter）
        - 即刻（jike）
        - 抖音（douyin）
        - 其他平台（如有）

        你的任务：
        1. 检查 multi_platform_drafts 中哪些平台有可发布内容。
        2. 对每一个有内容的平台自动执行以下动作：
           - 调用 Chrome / 浏览器类 MCP 工具，打开对应平台的网页版发布页面。
             例如：
               * https://creator.xiaohongshu.com
               * https://twitter.com/compose/tweet
               * https://web.okjike.com
               * https://creator.douyin.com
           - 将草稿中的标题 / 正文 / 标签 / 封面文案等，填入网页的输入框中。
           - 若需要上传图片，使用 MCP 工具执行上传或粘贴 URL 的操作。
           - 如果 MCP 工具支持点击发布按钮，可以尝试提交发布；
             若不支持则停留在「已完成填充，等待用户确认发布」。

        提醒：
        - 请合理选择 Chrome MCP 工具进行元素选择、输入、点击操作。
        - 不要输出内容正文本身，只输出执行动作的状态总结。
        - 不要进行解释性的分析，只告诉我：你调用了哪些 MCP 工具，以及每个平台的发布状态。

        输出格式（自然语言）：
        - 哪些平台已打开
        - 哪些字段已自动填充
        - 是否尝试点击发布按钮
        - 若受到登录限制或权限限制，请简要说明
        """
        
            ).strip()

        # 理论上不会走到这里，留一个兜底
        return textwrap.dedent(
            f"""
            未知的 mode: {mode}

            [用户输入]
            {user_input.strip()}

            {research_block}

            请简单给出 1 段与 IP 画像匹配的内容建议。
            """
        ).strip()
