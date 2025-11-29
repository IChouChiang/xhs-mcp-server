# Chrome MCP Server 部署与使用指南

本指南将帮助您在当前工作区部署和配置 `mcp-chrome`，将您的 Chrome 浏览器转变为 AI 助手。

## 1. 项目简介

`mcp-chrome` 是一个基于 Chrome 插件的 MCP (Model Context Protocol) 服务器。它允许 AI 模型（如 Claude, DeepSeek 等）直接控制您的浏览器，执行网页操作、内容提取等任务。

**核心优势：**
- 直接使用您现有的 Chrome 浏览器（保留登录态、插件、配置）。
- 无需启动额外的浏览器进程（比 Playwright 更轻量）。
- 支持跨标签页操作和语义搜索。

## 2. 部署步骤

### 第一步：安装 Native Bridge (桥接程序)

这是连接 Chrome 插件和 MCP 客户端的桥梁。

**选项 A：使用 npm 全局安装（推荐）**
在终端中运行：
```powershell
npm install -g mcp-chrome-bridge
```

**选项 B：从源码运行 (如果您想利用当前克隆的代码)**
由于本项目是 Monorepo 且依赖 `pnpm`，如果您没有安装 `pnpm`，建议使用选项 A。
如果您想尝试源码构建：
1. 安装 pnpm: `npm install -g pnpm`
2. 进入目录: `cd mcp-chrome`
3. 安装依赖: `pnpm install`
4. 构建: `pnpm run build`

### 第二步：安装 Chrome 扩展

1. **下载扩展**：
   - 访问 Release 页面：[https://github.com/hangwin/mcp-chrome/releases](https://github.com/hangwin/mcp-chrome/releases)
   - 下载最新的 `chrome-mcp-server-x.x.x.zip` (或类似名称的压缩包)。
   - 解压该压缩包到任意目录（例如 `E:\DOCUMENT\xhs-mcp-server\mcp-chrome-extension`）。

2. **加载扩展**：
   - 打开 Chrome 浏览器，在地址栏输入 `chrome://extensions/`。
   - 打开右上角的 **"开发者模式" (Developer mode)** 开关。
   - 点击左上角的 **"加载已解压的扩展程序" (Load unpacked)**。
   - 选择刚才解压的文件夹。

3. **连接**：
   - 点击浏览器右上角的 `Chrome MCP Server` 插件图标。
   - 确保状态显示为 **Connected** (通常会自动连接)。
   - 您会看到类似 `Streamable HTTP URL: http://127.0.0.1:12306/mcp` 的信息。

### Edge 浏览器支持

如果您使用的是 Microsoft Edge，请执行以下额外步骤：

1. **允许来自其他应用商店的扩展**：
   - 在 Edge 中打开 `edge://extensions/`。
   - 开启左下角的 **"允许来自其他应用商店的扩展"**。

2. **注册 Native Host**：
   - `mcp-chrome-bridge` 默认只注册 Chrome。您需要运行我们提供的脚本来支持 Edge。
   - 在终端中运行：
     ```powershell
     ./register_edge.ps1
     ```

3. **加载扩展**：
   - 步骤同 Chrome（加载已解压的扩展程序）。

## 3. 配置 MCP 客户端

现在您需要配置您的 AI 客户端（如 Claude Desktop, Cherry Studio, 或我们自己的 LangGraph Agent）来连接这个服务器。

### 方式一：Streamable HTTP (推荐)

这是最简单的方式，适用于支持 HTTP MCP 的客户端。

**配置示例 (JSON):**
```json
{
  "mcpServers": {
    "chrome-mcp-server": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:12306/mcp"
    }
  }
}
```

### 方式二：Stdio (标准输入输出)

如果您需要通过 Stdio 方式运行（例如在某些不支持 HTTP 的客户端中），您需要指向 `mcp-chrome-bridge` 的可执行文件。

**配置示例 (JSON):**
```json
{
  "mcpServers": {
    "chrome-mcp-server": {
      "command": "mcp-chrome-bridge",
      "args": []
    }
  }
}
```
*(前提是您已经全局安装了 `mcp-chrome-bridge`)*

## 4. 在本项目 (LangGraph Agent) 中使用

如果您想让我们之前构建的 Python Agent 使用这个 Chrome MCP Server，您需要修改 `agent.py`。

**修改思路：**
目前 `agent.py` 是启动本地的 Go server (`./xhs-server.exe`)。
要使用 Chrome MCP，我们需要连接到 `http://127.0.0.1:12306/mcp` (使用 `mcp[sse]` 库) 或者通过 Stdio 调用 `mcp-chrome-bridge`。

由于 Python SDK 对 SSE/HTTP 的支持可能需要额外的客户端代码，最简单的方法是让 Agent 同时支持多个 Server，或者替换当前的 Server。

**注意：** `mcp-chrome` 提供的工具可能与我们自己写的 `xhs-server` 不同。它提供了通用的浏览器操作工具（如 `click`, `type`, `screenshot` 等），而不是专门的 `xhs_search_keyword`。这意味着 Agent 的 Prompt 需要调整，让它知道如何使用通用工具来操作小红书。

## 5. 常见问题

- **连接失败？** 确保 `mcp-chrome-bridge` 正在运行（通常插件会自动唤起，或者您可以手动运行 `mcp-chrome-bridge`）。
- **端口冲突？** 默认端口是 12306，如果被占用，请检查插件设置。
