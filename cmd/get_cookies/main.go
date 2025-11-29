package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/playwright-community/playwright-go"
)

func main() {
	fmt.Println("Starting Cookie Harvester...")
	pw, err := playwright.Run()
	if err != nil {
		log.Fatalf("could not start playwright: %v", err)
	}
	defer pw.Stop()

	browser, err := pw.Chromium.Launch(playwright.BrowserTypeLaunchOptions{
		Headless: playwright.Bool(false),
	})
	if err != nil {
		log.Fatalf("could not launch browser: %v", err)
	}
	defer browser.Close()

	// Set a realistic User-Agent
	userAgent := "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
	context, err := browser.NewContext(playwright.BrowserNewContextOptions{
		UserAgent: playwright.String(userAgent),
	})
	if err != nil {
		log.Fatalf("could not create context: %v", err)
	}

	page1, err := context.NewPage()
	if err != nil {
		log.Fatalf("could not create page 1: %v", err)
	}

	fmt.Println("Navigating to Xiaohongshu Creator Studio (Tab 1)...")
	if _, err = page1.Goto("https://creator.xiaohongshu.com/publish/publish"); err != nil {
		log.Fatalf("could not goto creator: %v", err)
	}

	page2, err := context.NewPage()
	if err != nil {
		log.Fatalf("could not create page 2: %v", err)
	}

	fmt.Println("Navigating to Xiaohongshu Explore (Tab 2)...")
	if _, err = page2.Goto("https://www.xiaohongshu.com/explore"); err != nil {
		log.Fatalf("could not goto explore: %v", err)
	}

	fmt.Println("Please ensure you are logged in on BOTH tabs (manually login if needed).")
	fmt.Println("Press 'Enter' here in the terminal once you have successfully logged in on both...")

	// Wait for user to press Enter
	reader := bufio.NewReader(os.Stdin)
	_, _ = reader.ReadBytes('\n')

	// Get full storage state (Cookies + LocalStorage)
	storageState, err := context.StorageState()
	if err != nil {
		log.Fatalf("could not get storage state: %v", err)
	}

	// Save to auth.json
	stateJSON, err := json.MarshalIndent(storageState, "", "  ")
	if err != nil {
		log.Fatalf("could not marshal storage state: %v", err)
	}

	if err := os.WriteFile("auth.json", stateJSON, 0644); err != nil {
		log.Fatalf("could not write auth.json: %v", err)
	}

	fmt.Println("Successfully saved full auth state to auth.json")
}
