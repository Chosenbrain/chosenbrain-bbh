from playwright.sync_api import sync_playwright
import json

def save_yeswehack_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://yeswehack.com/auth/login")
        input("🔐 Log in manually, then press Enter...")
        with open("cookies/yeswehack.json", "w") as f:
            json.dump(context.cookies(), f)
        browser.close()

if __name__ == "__main__":
    save_yeswehack_cookies()