
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_PATH = "cookies/intigriti.json"
SUBMIT_URL_TEMPLATE = "https://app.intigriti.com/researcher/programs/{program_slug}/submission"

def submit_to_intigriti(report: dict) -> str:
    """
    Submit report to Intigriti using saved browser cookies.

    Required keys:
    - report['title']
    - report['report']
    - report['program_slug']  → e.g. "spotify"
    """

    if "program_slug" not in report:
        return "❌ report['program_slug'] missing. Cannot build Intigriti URL."

    if not Path(COOKIES_PATH).exists():
        return "❌ Intigriti cookies missing. Run save_intigriti_cookies.py first."

    submit_url = SUBMIT_URL_TEMPLATE.format(program_slug=report["program_slug"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        with open(COOKIES_PATH, "r") as f:
            context.add_cookies(json.load(f))

        page = context.new_page()
        page.goto(submit_url)
        time.sleep(5)

        try:
            page.fill('input[name="title"]', report["title"])
            page.fill('textarea[name="vulnerability"]', report["report"])
            # You may want to select severity or scope via dropdown here (manual or pre-scripted)

            page.click('button[type="submit"]')
            time.sleep(3)

        except Exception as e:
            return f"❌ Submission error: {e}"

        browser.close()
        return "✅ Submitted to Intigriti."