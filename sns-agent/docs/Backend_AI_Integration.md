# Frontend → Backend AI Integration Guide

This document explains what the frontend does, how the three API endpoints are used, and provides prompt templates for the backend AI (Python) to implement real logic and call your model appropriately.

## Frontend role
- Provides a canvas (text/image/drawing elements) with undo/redo, selection, and basic editing.
- Calls backend AI to:
  1) Suggest prompt chips based on current selection.
  2) Apply AI edits to selected elements and redraw the canvas using the returned elements.
  3) Publish all canvas elements to a chosen social platform (X / Xiaohongshu / Douyin) after AI generates copy.

## Endpoints and scenarios

### 1) `/api/ai/suggestions` — suggest prompt chips for current selection
- **When called**: Selection changes (one or more elements selected).
- **Request (JSON)**:
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
      "content": "element content or image dataURL"
    }
  ]
}
```
- **Response expected**:
```json
{
  "suggestions": ["Make the title punchier", "Turn it into a question", "..."]
}
```
- **Backend action**: Inspect element types/content, generate 3–6 short, actionable suggestions.

### 2) `/api/ai/apply` — apply AI edits to selected elements
- **When called**: User submits a prompt in the AI dialog with one or more elements selected.
- **Request (JSON)**:
```json
{
  "prompt": "User instruction, e.g. make the title bold and blue",
  "elements": [
    {
      "id": "text-123",
      "type": "text | image | drawing",
      "x": 100,
      "y": 120,
      "width": 200,
      "height": 50,
      "content": "element content or image dataURL"
    }
  ]
}
```
- **Response expected** (the frontend redraws with this array):
```json
{
  "status": "ok",
  "elements": [
    {
      "id": "text-123",
      "type": "text",
      "x": 100,
      "y": 120,
      "width": 200,
      "height": 50,
      "content": "updated text content"
    }
  ]
}
```
- **Backend action**: Use the prompt + elements to produce updated elements (text rewrites, size/position tweaks, etc.). Return the full array; the frontend replaces its selection with this data and treats it as one undoable step.

### 3) `/api/ai/publish` — generate post content and publish
- **When called**: User clicks Publish and chooses a platform.
- **Request (JSON)**:
```json
{
  "platform": "x | xiaohongshu | douyin",
  "elements": [
    {
      "id": "text-123",
      "type": "text | image | drawing",
      "x": 100,
      "y": 120,
      "width": 200,
      "height": 50,
      "content": "element content or image dataURL"
    }
  ]
}
```
- **Response expected**:
```json
{
  "status": "ok",
  "message": "publish stub called",
  "post": {
    "title": "...",
    "body": "...",
    "tags": ["..."]
  }
}
```
- **Backend action**: Call AI to analyze canvas content, generate platform-specific copy, then publish via your MCP/gateway. Return generated content and status.

## Prompt templates for backend AI (Python)
Below are sample system/user messages your backend AI can use. Adjust to your model/provider.

### Suggestions (`/api/ai/suggestions`)
- **System**: “You are a creative assistant for a social post designer. Given selected canvas elements (text, images), propose 3–6 concise, actionable edit suggestions.”
- **User**: Include serialized `elements` array. Ask for short imperative suggestions (no more than 8 words).

### Apply edits (`/api/ai/apply`)
- **System**: “You transform selected canvas elements based on the user prompt. Return an updated elements array in the same shape; only modify what the prompt implies.”
- **User**: Provide `prompt` and `elements`. Instruct model to output JSON `elements` array only (no styles needed).

### Publish (`/api/ai/publish`)
- **System**: “You generate social copy based on canvas content for the specified platform (X, Xiaohongshu, or Douyin). Tone should match the platform; return title/body/tags.”
- **User**: Provide `platform` and `elements`. Ask for concise, platform-appropriate text and tags/hashtags.

## Python backend outline (pseudo)
```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/ai/suggestions")
def suggestions(payload: dict):
    elements = payload.get("elements", [])
    # call your model with prompt constructed from elements
    return {"suggestions": ["Sample suggestion 1", "Sample suggestion 2"]}

@app.post("/api/ai/apply")
def apply(payload: dict):
    prompt = payload.get("prompt", "")
    elements = payload.get("elements", [])
    # call your model to transform elements; here we echo back
    updated = elements  # replace with model output
    return {"status": "ok", "elements": updated}

@app.post("/api/ai/publish")
def publish(payload: dict):
    platform = payload.get("platform", "")
    elements = payload.get("elements", [])
    # call your model to generate copy, then publish via your gateway/MCP
    return {
        "status": "ok",
        "message": "publish stub called",
        "post": {"title": "Generated title", "body": "Generated body", "tags": ["tag1", "tag2"]}
    }
```

## Frontend TypeScript stubs (for reference)
These are the current placeholder handlers in the Next.js app; they show the shape and intent for each endpoint.

```ts
// /api/ai/suggestions
export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  console.log("[AI suggestions] Elements:", body?.elements);
  return NextResponse.json({ suggestions: ["Sample suggestion 1", "Sample suggestion 2"] });
}

// /api/ai/apply
export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const incomingElements = Array.isArray(body?.elements) ? body.elements : [];
  console.log("[AI apply] Prompt:", body?.prompt);
  console.log("[AI apply] Elements:", incomingElements);
  // Echo back elements so the canvas redraws; replace with AI-transformed elements.
  return NextResponse.json({ status: "ok", elements: incomingElements });
}

// /api/ai/publish
export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  console.log("[AI publish] Platform:", body?.platform);
  console.log("[AI publish] Elements:", body?.elements);
  return NextResponse.json({
    status: "ok",
    message: "publish stub called",
    post: { title: "Generated title", body: "Generated body", tags: ["tag1", "tag2"] },
  });
}
```

## Notes
- Frontend redraws strictly from the `elements` array returned by `/apply`.
- Keep IDs stable; the frontend uses them to maintain selection.
- Add auth/rate limiting/logging as needed.  
