基础
快速开始
​
1️⃣ 直接调用 AiHubMix API
其中 <AIHUBMIX_API_KEY> 替换为 Aihubmix Key，注意 key 的有效期和额度限制。
可使用的 model 列表，可查阅 模型广场 ，复制模型名称替换即可。
Copy

import requests
import json

response = requests.post(
  url="https://aihubmix.com/v1/chat/completions",
  headers={
    "Authorization": "Bearer <AIHUBMIX_API_KEY>",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "gpt-4o-mini", # 替换模型 id
    "messages": [
      {
        "role": "user",
        "content": "What is the meaning of life?"
      }
    ]
  })
)

支持流式调用，只需要增加参数 stream: true
​
2️⃣ 使用 OpenAI SDK
其中 <AIHUBMIX_API_KEY> 替换为 Aihubmix Key，注意 key 的有效期和额度限制。 可使用的 model 列表，可查阅 模型广场 ，复制模型名称替换即可。
Copy

from openai import OpenAI

client = OpenAI(
  base_url="https://aihubmix.com/v1",
  api_key="<AIHUBMIX_API_KEY>",
)

completion = client.chat.completions.create(
  model="gpt-4o-mini", # 替换模型 id
  messages=[
    {
      "role": "developer",
      "content": "总是用中文回复"
    },    
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ],
  temperature=0.8,
  max_tokens=1024,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0,
  seed=random.randint(1, 1000000000),
)

print(completion.choices[0].message.content)

对于支持搜索的模型，可以追加下方参数来支持：
Copy

  web_search_options={}, # 搜索参数

可用模型：gpt-4o-search-preview、gpt-4o-mini-search-preview。
注意搜索模型暂不支持 temperature 等细节参数。
​
3️⃣ 通过第三方客户端发起请求
参考 场景示例