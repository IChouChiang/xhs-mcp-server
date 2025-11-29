package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"github.com/playwright-community/playwright-go"
)

func main() {
	// Create MCP server
	s := server.NewMCPServer(
		"xhs-mcp-server",
		"1.0.0",
		server.WithLogging(),
	)

	// Add tool: xhs_search_keyword
	tool := mcp.NewTool("xhs_search_keyword",
		mcp.WithDescription("Search for a keyword on Xiaohongshu (Little Red Book) and open the results in a browser."),
		mcp.WithString("keyword", mcp.Required(), mcp.Description("The keyword to search for")),
	)

	s.AddTool(tool, searchHandler)

	// Start server on Stdio
	if err := server.ServeStdio(s); err != nil {
		fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
	}
}

func searchHandler(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	args, ok := request.Params.Arguments.(map[string]interface{})
	if !ok {
		return mcp.NewToolResultError("arguments must be a map"), nil
	}
	
	keyword, ok := args["keyword"].(string)
	if !ok {
		return mcp.NewToolResultError("keyword argument is required and must be a string"), nil
	}

	// Get absolute path to auth.json
	ex, err := os.Executable()
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("failed to get executable path: %v", err)), nil
	}
	rootDir := filepath.Dir(ex)
	// If running with go run, executable is in temp, so we might need to look in CWD
	if _, err := os.Stat(filepath.Join(rootDir, "auth.json")); os.IsNotExist(err) {
		rootDir, _ = os.Getwd()
	}
	authPath := filepath.Join(rootDir, "auth.json")

	if _, err := os.Stat(authPath); os.IsNotExist(err) {
		return mcp.NewToolResultError("auth.json not found. Please run get_cookies utility first."), nil
	}

	// Launch Playwright
	// Note: In a real server, we might want to keep the browser open or manage a pool.
	// For this task, we'll launch it and keep it open for a bit or detach?
	// The requirement says "The Go server will open the Chrome tab... The agent should verify the tool ran successfully".
	// If we close the browser immediately, the user won't see it.
	// We'll launch it and detach or wait a bit. Since this is a local tool, we can just keep it running?
	// But the tool handler needs to return.
	// We will launch the browser and NOT close it immediately, but we can't block the return.
	// However, Playwright objects are bound to the Run() process. If we return and the main function exits...
	// Wait, the MCP server `ServeStdio` blocks. So we can keep the browser instance in a global variable or manage it.
	// But `playwright.Run()` starts a driver process.

	// For simplicity, let's launch, navigate, and then return success.
	// We need to ensure the browser doesn't close when the handler returns.
	// But `defer pw.Stop()` and `defer browser.Close()` in the handler would close it.
	// We should probably manage the browser lifecycle outside the handler or just let it run for a fixed time if it's just for demo.
	// OR, we assume the user wants to see it.
	
	// Let's try to launch it and keep it open by NOT deferring Close inside the handler, 
	// BUT we need to keep the playwright driver running.
	// The `main` function is running `ServeStdio`.
	// We can initialize Playwright in `main` or a global init.

	go func() {
		if err := openSearch(authPath, keyword); err != nil {
			fmt.Fprintf(os.Stderr, "Error opening search: %v\n", err)
		}
	}()

	return mcp.NewToolResultText(fmt.Sprintf("Opened search for keyword: %s", keyword)), nil
}

func openSearch(authPath, keyword string) error {
	pw, err := playwright.Run()
	if err != nil {
		return fmt.Errorf("could not start playwright: %v", err)
	}
	// We are not deferring pw.Stop() here because we want it to stay open? 
	// Actually, if this goroutine finishes, pw might be cleaned up?
	// Playwright-go starts a subprocess.
	// If we want the window to stay open, we have to keep the process alive.
	// But we want to return the tool result.
	
	// Let's just keep it open for a reasonable time (e.g. 2 minutes) or until the server stops.
	// Or better, we can make this a global singleton.
	
	browser, err := pw.Chromium.Launch(playwright.BrowserTypeLaunchOptions{
		Headless: playwright.Bool(false),
	})
	if err != nil {
		pw.Stop()
		return fmt.Errorf("could not launch browser: %v", err)
	}
	
	context, err := browser.NewContext(playwright.BrowserNewContextOptions{
		UserAgent:        playwright.String("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
		StorageStatePath: playwright.String(authPath),
	})
	if err != nil {
		browser.Close()
		pw.Stop()
		return fmt.Errorf("could not create context: %v", err)
	}

	page, err := context.NewPage()
	if err != nil {
		browser.Close()
		pw.Stop()
		return fmt.Errorf("could not create page: %v", err)
	}

	url := fmt.Sprintf("https://www.xiaohongshu.com/search_result?keyword=%s&source=web_explore_feed", keyword)
	if _, err = page.Goto(url); err != nil {
		browser.Close()
		pw.Stop()
		return fmt.Errorf("could not goto: %v", err)
	}

	// Keep open for observation
	time.Sleep(60 * time.Second)
	
	browser.Close()
	pw.Stop()
	return nil
}
