import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  // Log on the server to simulate backend AI call.
  console.log("[AI suggestions] Selected elements:", body?.elements);

  const suggestions: string[] = (() => {
    const elements = (body?.elements as { type?: string }[]) ?? [];
    if (elements.length === 0) return [];
    if (elements.length === 1 && elements[0]?.type === "text") {
      return ["让标题更有张力", "换成问句吸引互动", "缩短成一句话"];
    }
    if (elements.length === 1 && elements[0]?.type === "image") {
      return ["图片加上文字遮罩", "提高亮度", "改成圆角"];
    }
    return ["整体对齐居中", "统一配色为蓝色", "统一字号 18px"];
  })();

  return NextResponse.json({ suggestions });
}
