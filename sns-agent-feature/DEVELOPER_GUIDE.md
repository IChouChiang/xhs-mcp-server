# Multi:Demo Developer Handbook

This repository bundles three workstreams:

- **FastAPI backend** (`backend/web`) that orchestrates IP/persona aware content generation across multiple agents.
- **Chrome extension** (top-level JS, HTML, `_locales`, `content-scripts`, `inject-scripts`, `workers`, etc.) that exposes MCP (Model Context Protocol) style browser automation tools.
- **React/Vite frontend** (`frontend/`) that is currently a scaffold for a richer dashboard.

The goal of this handbook is to enumerate every available API, describe how each file participates in the system, and provide the context necessary for teammates to extend or consume the project safely.

---

## 1. Backend (FastAPI) service

### 1.1 Configuration (`backend/web/config.py`)

- `Settings` extends `BaseSettings` and loads environment variables (`APP_ENV`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, `BACKEND_STORAGE_PATH`, `MCP_PINTEREST_TOKEN`, `MCP_PLATFORM_TOKEN`, `DEFAULT_RESEARCH_PLATFORM`).
- Call `get_settings()` once and reuse (it is memoized with `@lru_cache`).
- `storage_path` defaults to `backend/web/.data/state.json`; `data_dir` resolves parent path to ensure directories exist.

### 1.2 Service clients

**LLMClient (`backend/web/services/llm_client.py`):**

- Instantiate with `Settings`; lazily configures `openai.OpenAI` if `LLM_API_KEY` is present else falls back to `_offline_stub`.
- `await LLMClient.generate(system_prompt, user_prompt, model=None)` sends a chat-completion call to the configured OpenAI-compatible endpoint, temperature 0.4. Returns stripped string or a stubbed response preview when offline.

**MCPToolExecutor (`backend/web/services/mcp_tools.py`):**

- Stores optional Pinterest/Platform tokens.
- `await search(topic: str, platform: str)` returns `List[MCPRecord]`. If credentials are missing, deterministic mock data is produced by `_mock_record`; if present, `_remote_search` would perform the real call (currently placeholder).
- `MCPRecord` dataclass: `topic`, `source`, `title`, `url`, `summary`.

**StorageClient (`backend/web/services/storage.py`):**

- Manages a JSON file at the configured path.
- `record_generation(prompt: str, response: GenerationResponse)` appends a timestamped log including IP profile, reasoning, steps, research notes.
- `list_sessions()` returns all stored prompt/response histories.
- Uses helper `_load()` / `_dump()` to manage the JSON blob; auto-creates the file structure on first use.

### 1.3 Schemas (`backend/web/schemas.py`)

- `IPProfile`: IP persona definition (includes alias `targetAudience`).
- `IPDecisionRequest`/`IPDecisionResponse`: used when selecting a profile for a user brief.
- `ResearchTask`, `ResearchFinding`: capture MCP research jobs and results.
- `AgentStep`: timeline entries for orchestrator steps.
- `GenerationRequest`: top-level POST payload with `input`, optional `user_brief`, `goal`, `prefer_ip_id`, override `ip_profile`, `research_topics`.
- `GenerationResponse`: final content, selected `ip_profile`, `reason`, step log, research notes.

### 1.4 Agents

**BaseAgent (`backend/web/agents/base.py`):** Abstract class with async `run(payload)` and `__call__` alias. Stores shared `LLMClient`, name, and logger per agent.

**IPAgent (`backend/web/agents/ip_agent.py`):**

- Constructor expects `llm`, `profile_store`, `research_agent`, `creator_agent`.
- `run(payload)` orchestrates the creative feedback loop. Payload keys: `user_id`, `user_input`, optional `mode` (`suggest`, `edit`, `image`, `publish`).
- Flow:
  1. Look up or create the user IP profile (default `PRESET_IP_PROFILE`).
  2. Build an IP development path (`_build_ip_dev_path`).
  3. Run up to three loops: `_decide_next_step` uses the LLM brain to emit JSON describing `research_input`, `creator_input`, `profile_patch`, `next_action` (`res`, `cr`, `finish`), and `continue` flag.
  4. Depending on `next_action`, call `research_agent.run()` or `creator_agent.run()` and feed results back into the next loop.
  5. Return consolidated `ip_profile`, `ip_dev_path`, `loop_count`, and `steps`.
- `_decide_next_step(profile, user_input, mode)` constructs a structured system prompt that codifies the loop rules for each `mode` and demands strict JSON output from the LLM.

**ResearchAgent (`backend/web/agents/research_agent.py`):**

- Designed to run MCP-powered search before summarizing via LLM.
- `run(topics: List[str], platform: Optional[str])` loops through topics, calls `self._executor.search` (where `_executor` should be an `MCPToolExecutor` configured in the constructor; the current file is missing the assignments and needs to set `self._executor` / `self._default_platform`), and converts `MCPRecord` objects into `ResearchFinding` entries.
- `analyze(findings)` composes `RESEARCH_SYSTEM_PROMPT` plus the raw findings, calls the LLM (`self._llm.acomplete`) and expects structured JSON with keys `summary`, `content_paths`, `hot_points`, `image_directions`.
- `research(topics)` convenience method for `run` + `analyze`.

**CreatorAgent (`backend/web/agents/creator_agent.py`):**

- `run(mode, user_input, ip_profile, research_notes=None)` builds prompts based on `CreatorMode`:
  - `"suggest"`: return JSON array of suggestions with `type`, `title`, `reason`, `outline`.
  - `"edit_text"`: return JSON with `mode_inferred`, `edited_text`, `suggest_notes`.
  - `"publish"`: return JSON containing per-platform drafts (`xiaohongshu`, `douyin`, `x`, etc.) and `nano_banana_prompt`.
  - `"edit_image"`: output `nano_banana_prompts` for cover/inline usage, with `avoid` lists.
  - Additional guard rails describe how to auto-publish via Chrome MCP tools and the tone/structure per platform.
- Uses `LLMClient.generate(system_prompt, user_prompt)` assembled via `_build_system_prompt` (injects IP profile values, keywords, taboos, global publishing instructions) and `_build_user_prompt` (mode-specific instructions plus optional research notes).

### 1.5 Orchestrator & FastAPI entrypoint

- `backend/web/orchestrator.py` currently provides a minimal stub:
  - Constructor stores an `ip_agent`.
  - `await handle(user_id, text, mode="suggest")` calls `ip_agent.run` with the expected payload. (Note: `backend/web/main.py` imports `Orchestrator` with a richer signature that is not implemented yet, so aligning these modules should be prioritized.)
- `backend/web/main.py` wires the FastAPI app:
  - Instantiates global `settings`, `StorageClient`, `LLMClient`, `MCPToolExecutor`, and `Orchestrator`.
  - Adds permissive CORS middleware.
  - **HTTP APIs:**
    - `GET /health` → `{"status":"ok","environment":settings.environment}`.
    - `GET /ip-profiles` → `List[IPProfile]` via `orchestrator.ip_agent.list_profiles()` (requires `IPAgent` to expose that method).
    - `GET /sessions` → raw history list from `StorageClient`.
    - `POST /orchestrate` → accepts `GenerationRequest`, logs the call, awaits `orchestrator.run(request)` (not defined in current orchestrator stub) and returns a `GenerationResponse`. After implementing `orchestrator.run`, remember to call `StorageClient.record_generation`.

### 1.6 Backend API usage guide

| Endpoint / Method | Request payload | Response | Usage notes |
| --- | --- | --- | --- |
| `GET /health` | none | `{"status": "ok", "environment": "development"}` | Use for liveness checks. |
| `GET /ip-profiles` | none | `[IPProfile, ...]` | Relies on `IPAgent` exposing stored personas; make sure the agent is initialized with a `profile_store`. |
| `GET /sessions` | none | `[{prompt, content, ip_profile, reason, …}, ...]` | Reads from JSON storage; use to display historical generations. |
| `POST /orchestrate` | `GenerationRequest` JSON. Example:<br>`{"input":"帮我写一个短视频脚本","user_brief":"女性创业者","goal":"增加粉丝","research_topics":["短视频趋势"]}` | `GenerationResponse` JSON mirroring schema. | Main orchestration entry. Should fan out to ResearchAgent & CreatorAgent and persist via `StorageClient`. |

### 1.7 Typical orchestration flow

1. Client sends `POST /orchestrate`.
2. FastAPI layer converts to `GenerationRequest`, loads settings, ensures `LLMClient`, `MCPToolExecutor`, `StorageClient`, and `IPAgent` exist.
3. Orchestrator builds the agent payload (`user_id`, `input`, `mode`) and enters the IPAgent loop.
4. IPAgent:
   - Loads/creates IP profile via `profile_store`.
   - Calls `_decide_next_step` (LLM) to determine whether to research (`ResearchAgent.run`/`analyze`) or create (`CreatorAgent.run`).
   - After each loop, merges `profile_patch` updates.
5. Upon completion, orchestrator should map the combined outputs back into `GenerationResponse` and call `StorageClient.record_generation`.
6. FastAPI responds with the structured content; clients can inspect `steps`, `research_notes`, and `ip_profile`.

---

## 2. Chrome extension & MCP toolchain

This side of the repo is a full-featured Chrome extension that exposes browser automation tools over a native messaging host (`com.chromemcp.nativehost`). Most files are already transpiled/bundled; edit source files in the upstream project if available.

### 2.1 Manifest & shared assets

- `manifest.json`: MV3 manifest registering icons, background service worker (`background.js`), popup UI (`popup.html`), offscreen document (`offscreen.html`), default content script (`content-scripts/content.js`), native messaging options, CSP, permissions (`nativeMessaging`, `tabs`, `scripting`, `debugger`, etc.), and web-accessible resources (models/workers).
- Icons (`icon/*.png`) and `wxt.svg` supply branding.
- `_locales/messages.json`, `_locales/en/messages.json`, `_locales/zh_CN/messages.json` describe localization strings for both Simplified Chinese and English.
- `assets/popup-OnFboBpW.css` is the compiled popup stylesheet.

### 2.2 Background, popup, offscreen bundles

- `background.js` (service worker) contains the compiled orchestration logic:
  - Registers tool names (`chrome_get_web_content`, `chrome_click_element`, etc.).
  - Implements a messaging protocol for launching/stopping the native host, bridging to MCP tool calls, and managing a semantic similarity engine (see constants such as `BACKGROUND_MESSAGE_TYPES`, `OFFSCREEN_MESSAGE_TYPES`, `TOOL_MESSAGE_TYPES`).
  - Maintains server status, handles `ping`/`pong` commands, caches semantic model downloads, and routes Chrome debugging APIs.
- `popup.html` mounts the bundled popup React/Vite app (`chunks/popup-CNE4nbSP.js`) and CSS.
- `offscreen.html` is the entry point for the semantic similarity engine worker bundle (`chunks/offscreen-QDezJN9Y.js`), preloading `chunks/semantic-similarity-engine-D0u7zDKx.js`.

### 2.3 Content script (`content-scripts/content.js`)

- Minimal stub generated by WXT: matches `*://*.google.com/*`, establishes a context watching URL changes, and sets up standard message plumbing to the extension runtime. Use it as the hook for page-level instrumentation if required.

### 2.4 Injected helper scripts (`inject-scripts/…`)

These scripts are injected dynamically by Chrome tooling commands defined in the background service worker. Each script keeps a guard flag (`window.__*_INITIALIZED__`) to avoid double initialization and listens to `chrome.runtime.onMessage` or custom events to perform tasks:

| File | Purpose & APIs |
| --- | --- |
| `interactive-elements-helper.js` | Enumerates buttons, links, inputs, checkboxes, radios, selects, tabs, and generic interactive elements. Exposes utilities to compute visibility, accessible names, selectors, and returns `ElementInfo` structures. Used by the `chrome_get_interactive_elements` MCP tool. |
| `screenshot-helper.js` | Handles messages: `chrome_screenshot_ping`, `preparePageForCapture`, `getPageDetails`, `getElementDetails`, `scrollPage`, `resetPageAfterCapture`. Temporarily hides fixed elements and scrolls the page to support stitched screenshots. |
| `click-helper.js` | Provides `clickElement` (selector or coordinates), optional navigation waiters, and `simulateClick`. Responds to MCP actions for clicking DOM nodes. |
| `fill-helper.js` | Offers `fillElement(selector, value)` that validates element types, scrolls/focuses, dispatches `input`/`change` events, and responds with metadata. Drives the `chrome_fill_or_select` tool. |
| `keyboard-helper.js` | Parses key combos (e.g., `Ctrl+Shift+S`, `Enter`) and dispatches corresponding `keydown`/`keypress`/`keyup` events, supporting modifiers. Backs the `chrome_keyboard` tool. |
| `web-fetcher-helper.js` | Embedded Readability.js clone that can extract clean article content/text/HTML for the `chrome_get_web_content` tool. |
| `network-helper.js` | Implements `replayNetworkRequest` with fetch + timeout, including cookies. Handles messages `chrome_network_request_ping` and `sendPureNetworkRequest`. |
| `inject-bridge.js` | Sets up a MAIN-world <-> extension bridge for executing scripts and relaying responses via custom DOM events (`chrome-mcp:execute`, `chrome-mcp:response`, `chrome-mcp:cleanup`). |

### 2.5 Workers, libs, and heavy assets

- `libs/ort.min.js`: ONNX Runtime Web binary loaded inside workers for semantic similarity.
- `workers/similarity.worker.js`: Custom worker that loads ONNX models (via `initializeModel`), batch/individual inference (`runInference`, `runBatchInference`), exposes stats, and handles messages (`init`, `infer`, `batchInfer`, `getStats`, `clearBuffers`). Uses transferables for efficiency.
- `workers/ort-wasm-simd-threaded*.wasm|.mjs|.jsep.mjs`: Precompiled backends for ONNX Runtime (SIMD/threaded variations). Required for both threaded and async instantiations.
- `workers/simd_math.js` / `workers/simd_math_bg.wasm`: Additional math helper for SIMD operations referenced by the semantic engine.

### 2.6 Localization and UI assets

- `_locales/messages.json` (zh), `_locales/en/messages.json` (English), `_locales/zh_CN/messages.json` (Simplified Chinese). Each file mirrors the same keys to ensure the UI text is localized (labels for semantic engine status, buttons, error messages, etc.).
- `assets/popup-OnFboBpW.css` and `chunks/*` are generated by Vite/WXT build pipelines. Avoid manual edits—rebuild from the upstream sources instead.

### 2.7 Using the Chrome MCP APIs

To call a browser tool from the native host:

1. Send a `NativeMessageType.CALL_TOOL` message through `chrome.runtime.connectNative`.
2. In `background.js`, resolve the tool name to an implementation (e.g., `TOOL_NAMES.BROWSER.CLICK`).
3. The background script injects the relevant helper (`click-helper.js`, `fill-helper.js`, etc.) if not already present, then forwards a message with `action` derived from `TOOL_MESSAGE_TYPES`.
4. The helper responds with a result payload (`success`, `elementInfo`, `error`, etc.) that propagates back to the native host as `CALL_TOOL_RESPONSE`.
5. Use the available actions:
   - `chrome_screenshot_*` actions for capture.
   - `chrome_get_interactive_elements`, `chrome_click_element`, `chrome_fill_or_select`, `chrome_keyboard`.
   - `chrome_get_web_content` for readable article extraction.
   - `chrome_network_*` (capture start/stop, debugger, request replay) and `chrome_network_request` for raw fetches.
   - `chrome_bookmark_*`, `chrome_history`, `chrome_console`, navigation/routing helpers, etc. (see `TOOL_NAMES` constants).

---

## 3. Frontend (React) scaffold (`frontend/`)

- Built with Vite/React; however, all TypeScript/HTML files are currently zero-length placeholders (`src/main.tsx`, `src/index.html`, `src/pages/Home.tsx`, components in `src/components`, `src/hooks/useApi.ts`). Treat them as stubs to be filled in when creating the actual dashboard.
- `frontend/public/favicon.ico` is the only populated asset today.

---

## 4. Additional documentation

- `IP框架.md`: Chinese-language mind-map describing a founder/IP framework. Contains sections such as persona definitions, belief systems, content categories, commercialization ideas, and iterative goals. Use this as seed data when populating `IPProfile` values or training prompts.

---

## 5. File catalog

| Path | Description / APIs |
| --- | --- |
| `wxt.svg` | SVG icon used by the extension; replace to change the WXT branding. |
| `manifest.json` | Chrome MV3 configuration (permissions, entrypoints, icons, localization references). |
| `background.js` | Compiled service worker orchestrating native messaging, MCP tools, semantic engine state, and Chrome APIs. |
| `offscreen.html` | Hidden document booting the semantic engine bundle (`chunks/offscreen-*.js`). |
| `popup.html` | Popup UI shell that mounts the Vite-built React bundle. |
| `chunks/popup-CNE4nbSP.js` | Bundled popup script (do not edit manually). |
| `chunks/offscreen-QDezJN9Y.js` | Bundled offscreen logic (semantic engine bootstrap). |
| `chunks/semantic-similarity-engine-D0u7zDKx.js` | Shared semantic similarity code (used by popup/offscreen). |
| `assets/popup-OnFboBpW.css` | Popup CSS bundle. |
| `content-scripts/content.js` | Generated content script stub that wires lifecycle/messaging for pages matched in the manifest. |
| `inject-scripts/interactive-elements-helper.js` | Enumerates accessible interactive nodes and returns metadata for automation. |
| `inject-scripts/screenshot-helper.js` | Prepares DOM for screenshots, handles capture actions, and restores scroll positions. |
| `inject-scripts/click-helper.js` | Provides selector/coordinate click automation with optional navigation waiters. |
| `inject-scripts/fill-helper.js` | Fills inputs/selects/textarea nodes, firing proper events (supports validation and feedback). |
| `inject-scripts/keyboard-helper.js` | Simulates keypress sequences with modifier parsing. |
| `inject-scripts/web-fetcher-helper.js` | Uses Readability to return cleaned article HTML/text for web fetching APIs. |
| `inject-scripts/network-helper.js` | Performs replayable network requests with cookies/headers and timeout handling. |
| `inject-scripts/inject-bridge.js` | MAIN-world bridge enabling injected code to respond to extension messages. |
| `libs/ort.min.js` | ONNX Runtime Web binary used by semantic similarity workers. |
| `workers/similarity.worker.js` | Worker script exposing `init`, `infer`, `batchInfer`, `getStats`, `clearBuffers` message handlers for ONNX inference. |
| `workers/ort-wasm-simd-threaded.wasm` | Core WebAssembly backend for ONNX Runtime with SIMD/threading. |
| `workers/ort-wasm-simd-threaded.mjs` | JS loader for the SIMD-threaded WASM backend. |
| `workers/ort-wasm-simd-threaded.jsep.mjs` | Alternative loader for `OffscreenCanvas`-compatible environments. |
| `workers/ort-wasm-simd-threaded.jsep.wasm` | WASM blob for the `jsep` loader variant. |
| `workers/simd_math.js` / `workers/simd_math_bg.wasm` | SIMD math utilities referenced by the semantic engine. |
| `workers/ort-wasm-simd-threaded...` (all variants) | Provide fallbacks for different threading contexts. |
| `workers/ort-wasm-simd-threaded.jsep...` | JSEP-compatible ONNX runtime pieces for worker contexts lacking JS `import`. |
| `workers/ort-wasm-simd-threaded.mjs` | Entry module for main-thread instantiation when `import()` is available. |
| `icon/16.png`, `icon/32.png`, `icon/48.png`, `icon/96.png`, `icon/128.png` | Multi-resolution extension icons. |
| `_locales/messages.json` | Default (Chinese) localization strings for the extension UI. |
| `_locales/en/messages.json` | English localization bundle. |
| `_locales/zh_CN/messages.json` | Simplified Chinese localization bundle matching default keys. |
| `IP框架.md` | Founder/IP framework reference document (Mandarin). |
| `backend/requirements.txt` | Python dependencies for the FastAPI backend (`fastapi`, `uvicorn`, `pydantic`, `openai`). |
| `backend/web/__init__.py` | Declares backend package. |
| `backend/web/main.py` | FastAPI setup, dependency wiring, REST endpoints (`/health`, `/ip-profiles`, `/sessions`, `/orchestrate`). |
| `backend/web/config.py` | Pydantic `Settings` definition and helper. |
| `backend/web/orchestrator.py` | Stub orchestrator calling `ip_agent.run` via `handle()`. |
| `backend/web/schemas.py` | Pydantic models for IP profiles, requests, responses, research results. |
| `backend/web/utils/__init__.py` | Util package marker. |
| `backend/web/utils/logger.py` | Logging configuration and `get_logger` helper. |
| `backend/web/services/__init__.py` | Service package marker. |
| `backend/web/services/llm_client.py` | Async wrapper around OpenAI-compatible chat completions with offline stub. |
| `backend/web/services/storage.py` | JSON persistence for orchestrator sessions (append-only). |
| `backend/web/services/mcp_tools.py` | MCP tool executor and `MCPRecord` dataclass. |
| `backend/web/agents/__init__.py` | Agents package marker. |
| `backend/web/agents/base.py` | `BaseAgent` abstract class definition. |
| `backend/web/agents/ip_agent.py` | Main orchestration agent coordinating research/creation loops. |
| `backend/web/agents/research_agent.py` | Research helper combining MCP searches with LLM summarization. |
| `backend/web/agents/creator_agent.py` | Content generation agent with multiple modes and publishing instructions. |
| `frontend/src/index.html` | Vite root HTML (currently empty placeholder). |
| `frontend/src/main.tsx` | Vite/React entry point placeholder. |
| `frontend/src/pages/Home.tsx` | Placeholder for the landing page component. |
| `frontend/src/components/App.tsx`, `IPSelector.tsx`, `ResultView.tsx` | Placeholder React components to be implemented. |
| `frontend/src/hooks/useApi.ts` | Placeholder hook for invoking backend APIs. |
| `frontend/public/favicon.ico` | Frontend favicon. |

> **Tip:** Several frontend files are empty shells. When implementing them, import hooks/components following standard React patterns and leverage the API section above to hit the backend endpoints.

---

## 6. Next steps for developers

1. **Align orchestrator wiring:** `backend/web/main.py` expects a more capable `Orchestrator`. Either expand `backend/web/orchestrator.py` to accept `settings`, `llm_client`, `storage`, `mcp_executor` and expose `.run()` / `ip_agent` attributes, or adjust `main.py` accordingly.
2. **Fill in frontend scaffolding:** Build the UI that consumes `/ip-profiles`, `/sessions`, `/orchestrate`, perhaps using `frontend/src/hooks/useApi.ts` as the abstraction for HTTP calls.
3. **Extend MCP integrations:** Implement real MCP calls inside `MCPToolExecutor._remote_search` and finish `ResearchAgent.__init__` assignments so research requests travel through the Chrome extension’s capabilities.
4. **Document Chrome tool commands:** If you add new inject scripts or tool names, update this guide and `TOOL_NAMES` to keep the API catalog accurate.
