import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Multi-Agent Content Studio",
  description:
    "从白板输入到多平台发布的多智能体前端模板：Orchestrator、Research、Creator、Growth、Product 全链路可视化。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
