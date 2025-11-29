import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  console.log("[AI publish] Elements received for publishing:", body?.elements);

  try {
    // Forward to Python MCP Agent Server
    const response = await fetch("http://127.0.0.1:8000/publish", {
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
    return NextResponse.json(data);
  } catch (error: any) {
    console.error("[AI publish] Error calling Python agent:", error);
    return NextResponse.json(
      { status: "error", message: error.message },
      { status: 500 }
    );
  }
}
