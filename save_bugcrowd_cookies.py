from playwright.sync_api import sync_playwright
import json

def save_bugcrowd_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://bugcrowd.com/session/new")
        input("🔐 Login manually. Press Enter when done...")
        with open("cookies/bugcrowd.json", "w") as f:
            json.dump(context.cookies(), f)
        browser.close()

if __name__ == "__main__":
    save_bugcrowd_cookies()