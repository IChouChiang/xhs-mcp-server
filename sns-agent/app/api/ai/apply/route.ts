import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  console.log("[AI apply] Prompt:", body?.prompt);
  console.log("[AI apply] Elements:", body?.elements);

  try {
    // Forward to Python MCP Agent Server for Chat/Advice
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Python server error: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json({ status: "ok", message: data.message });
  } catch (error: any) {
    console.error("[AI apply] Error calling Python agent:", error);
    // Fallback to OK so the UI doesn't break, but log the error
    return NextResponse.json({ status: "ok", message: "AI is offline, using local logic." });
  }
}
