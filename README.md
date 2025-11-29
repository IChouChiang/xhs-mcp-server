# xhs-mcp-server

A Model Context Protocol (MCP) server implementation for interacting with the Xiaohongshu (Little Red Book) platform. This project aims to provide a standardized interface for AI models to access XHS data and publishing capabilities.

## Features

### Cookie Harvester Utility
Due to complex login security measures (QR code/SMS verification), this project includes a manual utility to securely capture the full browser session (cookies + local storage).

**Location:** `cmd/get_cookies/main.go`

**Usage:**
1. Run the utility:
   ```bash
   go run cmd/get_cookies/main.go
   ```
2. Two browser tabs will open:
   - Tab 1: XHS Creator Studio
   - Tab 2: XHS Explore Page
3. Log in manually on **BOTH** tabs using your preferred method (QR code or SMS).
4. Once logged in on both tabs, return to the terminal and press **Enter**.
5. The combined session state will be serialized and saved to `auth.json` in the project root.

### Login Verification
You can verify that the captured session works correctly using the check login utilities.

**Creator Studio:**
```bash
go run cmd/check_login/main.go
```

**Explore Page:**
```bash
go run cmd/check_explore/main.go
```

## Prerequisites

- Go 1.23+
- Playwright for Go

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   go mod download
   ```
3. Install Playwright browsers:
   ```bash
   go run github.com/playwright-community/playwright-go/cmd/playwright@latest install chromium
   ```
