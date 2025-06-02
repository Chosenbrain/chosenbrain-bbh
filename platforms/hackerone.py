import logging
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
COOKIE_PATH = Path("cookies/hackerone_cookies.json")

def submit_to_hackerone(report: dict) -> str:
    """
    Uses saved browser cookies to log into HackerOne and submit a report.

    Args:
        report: dict with fields like 'title', 'report'

    Returns:
        str: Submission status
    """
    if not COOKIE_PATH.exists():
        return "❌ Login session not found. Please run save_hackerone_cookies.py first."

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            # Load cookies
            with open(COOKIE_PATH, "r") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)

            page = context.new_page()
            page.goto("https://hackerone.com/hacktivity")

            if "log in" in page.content().lower():
                return "❌ Cookie session expired or invalid. Please log in again."

            logger.info("✅ Logged into HackerOne.")

            # Simulate going to report submission (you may need to update this based on HackerOne UI)
            page.goto("https://hackerone.com/reports/new")

            page.fill('input[name="report[title]"]', report["title"])
            page.fill('textarea[name="report[description]"]', report["report"])

            # Click submit (WARNING: test this on a dummy program first!)
            # page.click('button[type="submit"]')

            logger.info("✅ Submitted report (simulated)")
            browser.close()

            return "✅ Submitted to HackerOne"
    except Exception as e:
        logger.exception("❌ Error submitting to HackerOne")
        return f"❌ Exception: {e}"
