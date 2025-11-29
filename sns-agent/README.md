# SNS Agent Frontend

This is the visual frontend for the **Xiaohongshu MCP Agent System**. It provides a "Canva-like" interface for designing posts and an AI Assistant chat box.

## 🔗 Integration

This frontend is designed to work with the **Python Backend (`agent_server.py`)** located in the parent directory.

-   **Chat Box**: Sends requests to `http://127.0.0.1:8000/chat`
-   **Publish Button**: Sends requests to `http://127.0.0.1:8000/publish`

## 🚀 Getting Started

### 1. Prerequisites
Ensure the Python Backend is running first! (See `../README.md`)

### 2. Install Dependencies
```bash
npm install
```

### 3. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

## 🛠️ Tech Stack
-   **Framework**: Next.js 16 (App Router)
-   **UI**: Tailwind CSS, Lucide React
-   **Drag & Drop**: React DnD
-   **Language**: TypeScript

## ⚠️ Note
If the AI Chat or Publish features are not working, check that:
1.  The Python server is running on port 8000.
2.  There are no CORS issues (though the Next.js API route proxies requests to avoid this).
