import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  // Log on the server to simulate backend AI modification call.
  console.log("[AI apply] Prompt:", body?.prompt);
  console.log("[AI apply] Elements:", body?.elements);

  return NextResponse.json({ status: "ok" });
}
