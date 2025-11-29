# AI API 说明（前后端对接）

前端已提供3个占位接口，供后端接入真实 AI 服务时参考。接口均为 POST，传输 JSON。
前端是一个ai辅助的社交媒体帖子设计工具，用户可以在画布上添加文本、图片、涂鸦等元素。

## 1. 获取提示卡片 `/api/ai/suggestions 前端会把画布上的元素发给后端，后端分析后返回优化建议列表，前端展示为可点击的提示卡片。`

- **方法**：POST  
- **请求体**：

```json
{
  "elements": [
    {
      "id": "text-123",
      "type": "text | image | drawing",
      "x": 100,
      "y": 120,
      "width": 200,
      "height": 50,
      "content": "当前元素内容或图片 dataURL",
      "styles": {
        "fontSize": 16,
        "fontWeight": "normal",
        "color": "#000000",
        "backgroundColor": "transparent",
        "opacity": 1,
        "rotation": 0
      }
    }
  ]
}
```

- **响应体（示例）**：

```json
{
  "suggestions": [
    "让标题更有张力",
    "换成问句吸引互动",
    "统一配色为蓝色"
  ]
}
```

- **当前行为**：仅在服务器控制台 `console.log` 打印选中元素并返回固定建议。后端可在此处接入真实推荐逻辑。

## 2. 应用 AI 修改 `/api/ai/apply`

- **方法**：POST  
- **请求体**：

```json
{
  "prompt": "用户输入的指令，例如：让标题加粗并变成蓝色",
  "elements": [
    {
      "id": "text-123",
      "type": "text | image | drawing",
      "x": 100,
      "y": 120,
      "width": 200,
      "height": 50,
      "content": "当前元素内容或图片 dataURL",
      "styles": {
        "fontSize": 16,
        "fontWeight": "normal",
        "color": "#000000",
        "backgroundColor": "transparent",
        "opacity": 1,
        "rotation": 0
      }
    }
  ]
}
```

- **响应体（示例）**：

```json
{
  "status": "ok"
}
```

- **当前行为**：服务器端打印 `prompt` 与 `elements`，前端收到响应后会用本地规则（关键字）模拟修改。后端接入后，可在此返回新的元素属性（例如新的内容、样式、位置等），前端可调整为以响应结果为准。

## 集成要点

1) 两个接口均在 Next.js App 路由下，部署后走同域调用。  
2) 若后端地址独立，可将 fetch URL 改为你的网关地址；保持字段一致即可。  
3) 返回字段建议保持以上结构，便于前端直接替换本地模拟逻辑。  
4) 目前仅打印日志，无鉴权与限流，如需要请在路由中增加校验与错误返回。

## 3. 发布（AI 生成并推送） `/api/ai/publish`

- **方法**：POST  
- **用途**：点击「发布」时调用，提交当前画布所有元素。后端可在此：
  1) 调用 AI 分析画布并生成帖子标题/正文/标签等；
  2) 通过 MCP 或内部网关将内容分发至各社交媒体。

- **请求体**：

```json
{
  "elements": [
    {
      "id": "text-123",
      "type": "text | image | drawing",
      "x": 100,
      "y": 120,
      "width": 200,
      "height": 50,
      "content": "当前元素内容或图片 dataURL",
      "styles": {
        "fontSize": 16,
        "fontWeight": "normal",
        "color": "#000000",
        "backgroundColor": "transparent",
        "opacity": 1,
        "rotation": 0
      }
    }
  ]
}
```

- **响应体（示例）**：

```json
{
  "status": "ok",
  "message": "publish stub called"
}
```

- **当前行为**：仅在服务器控制台打印元素数组，未调用真实 AI/发布逻辑。后端接入时可返回生成的帖子内容和发布结果。
