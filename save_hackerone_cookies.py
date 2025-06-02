import json
from playwright.sync_api import sync_playwright

COOKIES_FILE = "cookies/hackerone.json"

def save_hackerone_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://hackerone.com/")

        print("🔐 Log in manually in the browser that just opened.")
        input("✅ Press ENTER here when you're fully logged in...")

        cookies = context.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)
        print(f"✅ Saved cookies to {COOKIES_FILE}")
        browser.close()

if __name__ == "__main__":
    save_hackerone_cookies()