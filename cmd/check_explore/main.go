package main

import (
	"fmt"
	"log"
	"os"
	"time"

	"github.com/playwright-community/playwright-go"
)

func main() {
	// 1. Check if auth.json exists
	if _, err := os.Stat("auth.json"); os.IsNotExist(err) {
		log.Fatalf("auth.json not found. Please run get_cookies first.")
	}

	// 2. Launch Playwright
	pw, err := playwright.Run()
	if err != nil {
		log.Fatalf("could not start playwright: %v", err)
	}
	defer pw.Stop()

	browser, err := pw.Chromium.Launch(playwright.BrowserTypeLaunchOptions{
		Headless: playwright.Bool(false), // Visible for verification
	})
	if err != nil {
		log.Fatalf("could not launch browser: %v", err)
	}
	defer browser.Close()

	// 3. Create Context with Storage State (Cookies + LocalStorage)
	userAgent := "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
	context, err := browser.NewContext(playwright.BrowserNewContextOptions{
		UserAgent:        playwright.String(userAgent),
		StorageStatePath: playwright.String("auth.json"),
	})
	if err != nil {
		log.Fatalf("could not create context: %v", err)
	}

	page, err := context.NewPage()
	if err != nil {
		log.Fatalf("could not create page: %v", err)
	}

	// 4. Navigate to verify login on Explore page
	fmt.Println("Navigating to Xiaohongshu Explore Page with saved auth state...")
	if _, err = page.Goto("https://www.xiaohongshu.com/explore"); err != nil {
		log.Fatalf("could not goto: %v", err)
	}

	fmt.Println("Page loaded. Please check if you are logged in (look for avatar/profile).")
	fmt.Println("Waiting for 30 seconds for visual verification...")
	time.Sleep(30 * time.Second)
}
