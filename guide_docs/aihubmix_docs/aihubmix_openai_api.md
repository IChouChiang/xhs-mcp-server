Openai Responses API 支持
支持 Openai 的 Responses API 多功能接口，已经上线的功能接口如下：

    Text input：文本输入
    Image input：图文输入
    Streaming：流式调用
    Web search：搜索
    Deep research：深度研究
    Reasoning：推理深度控制，支持 4 档 (minimal / low / medium /high)，其中，minimal 仅适用于 gpt-5 系列，completion 端口中参数名为 reasoning_effort
    Verbosity：输出篇幅，gpt-5 系列支持 3 档 (low / medium / high)，其中，gpt-5-chat 仅支持 medium，completions 端口需要更新 openai 包来支持此参数
    Functions：函数调用
    image_generation：绘图工具调用，图片生成部分按 gpt-image-1 计价
    Code Interpreter：代码解析器，与 gpt-5 搭配时，不支持 reasoning.effort ‘minimal’ 档位
    Remote MCP：MCP 调用
    Computer Use：自动操作

​
使用 (Python 调用)：
与官方的 OpenAI 调用方式一致，只是替换 api_key 和 base_url 进行转发。 大陆可以直连访问。
Copy

client = OpenAI(
    api_key="AIHUBMIX_API_KEY", # 换成你在后台生成的 Key "sk-***"
    base_url="https://aihubmix.com/v1"
)

    对于推理模型，支持通过以下参数来输出推理总结，总结细节的丰富程度为 detailed > auto > None，其中 auto 为最佳平衡。

Copy

"summary": "auto" 

    gpt-5-chat 在不传入 reasoning.effort 的情况下，相当于关闭推理，适用于会话场景。
    深度研究模型可选：o3-deep-research 和 o4-mini-deep-research，仅支持 responses 端口
    gpt-5 系列强调稳定推理和一致性输出，不再支持用于控制随机性的 temprature 和 top_p 参数，如果你需要更多自由度，可以尝试支持 temprature 的 gpt-5-chat-latest
    推理模型（o 系列 / gpt-5 系列）已废弃 ‎max_tokens，请使用 completion 的 ‎max_completion_tokens 或 responses 的 max_output_tokens 明确限定输出 token 上限。

Copy

from openai import OpenAI

client = OpenAI(
    api_key="AIHUBMIX_API_KEY", # 换成你在后台生成的 Key "sk-***"
    base_url="https://aihubmix.com/v1"
)

response = client.responses.create(
    model="gpt-5", # gpt-5, gpt-5-chat-latest, gpt-5-mini, gpt-5-nano
    input="塔罗占卜为何有效，背后的原理和可迁移的方法是什么？Output format: Markdown", # GPT-5 默认不使用 Markdown 格式输出，需要明确指定。
    reasoning={
        "effort": "minimal" # 推理深度 - Controls how many reasoning tokens the model generates before producing a response. value can be "minimal", "low", "medium", "high", default is "medium"
    },
    text={
        "verbosity": "low" # 输出篇幅 - Verbosity determines how many output tokens are generated. value can be "low", "medium", "high", Models before GPT-5 have used medium verbosity by default. 
    },
    stream=True
)

for event in response:
  print(event)

注意：

    最新的 `codex-mini-latest` 不支持搜索
    Computer use 需要配合 Praywright 使用，建议参考官方仓库

已知细节问题：

    调用用例复杂
    截图大量，耗时久，任务成功率低
    或触发 CAPTCHA 验证或 Cloudflare 真人验证，可能遇到无限循环
