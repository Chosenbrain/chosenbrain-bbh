
import asyncio
from playwright.sync_api import sync_playwright
import json

COOKIES_PATH = "cookies/hackerone_cookies.json"

def save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://hackerone.com/")

        print("🛑 Please log in manually in the opened browser...")
        input("✅ Press Enter here once you're fully logged in...")

        cookies = context.cookies()
        with open(COOKIES_PATH, "w") as f:
            json.dump(cookies, f)
        print("✅ Cookies saved.")
        browser.close()