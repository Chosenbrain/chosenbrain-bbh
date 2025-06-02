import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_PATH = "cookies/yeswehack.json"
SUBMIT_URL_TEMPLATE = "https://yeswehack.com/programs/{program_slug}/report"  # Simulated; confirm actual submission URL

def submit_to_yeswehack(report: dict) -> str:
    """
    Submits a report to YesWeHack using browser automation and saved login cookies.
    
    Required:
        - report["title"]
        - report["report"]
        - report["program_slug"]  → e.g. "example-company"
    """

    if "program_slug" not in report:
        return "❌ report['program_slug'] missing. Cannot proceed."

    if not Path(COOKIES_PATH).exists():
        return "❌ YesWeHack cookies missing. Run save_yeswehack_cookies.py first."

    submit_url = SUBMIT_URL_TEMPLATE.format(program_slug=report["program_slug"])

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()

            with open(COOKIES_PATH, "r") as f:
                context.add_cookies(json.load(f))

            page = context.new_page()
            page.goto(submit_url)
            time.sleep(5)

            page.fill('input[name="title"]', report["title"])
            page.fill('textarea[name="description"]', report["report"])

            # If applicable, auto-select scope or severity:
            # page.click('select[name="severity"] >> text=High')

            page.click('button[type="submit"]')
            time.sleep(3)
            browser.close()

        return "✅ Submitted successfully to YesWeHack."

    except Exception as e:
        return f"❌ Submission failed: {e}"