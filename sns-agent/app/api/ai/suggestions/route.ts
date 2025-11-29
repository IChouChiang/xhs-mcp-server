import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  // Log on the server to simulate backend AI call.
  console.log("[AI suggestions] Selected elements:", body?.elements);

  const suggestions: string[] = [];
  // The frontend has local fallbacks (AIDialog.tsx) which are in English.
  // We return empty here to let the frontend use those defaults, 
  // or until we connect a real AI for suggestions.

  return NextResponse.json({ suggestions });
}
