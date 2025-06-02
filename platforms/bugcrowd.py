import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_PATH = "cookies/bugcrowd.json"
SUBMIT_URL_TEMPLATE = "https://bugcrowd.com/{program_slug}/report"  # <- dynamic

def submit_to_bugcrowd(report: dict) -> str:
    """
    Submit the bug report to Bugcrowd using saved cookies and Playwright.
    
    Expected report dict:
        {
            "title": "XSS in profile bio",
            "report": "Steps to Reproduce...\nImpact...\nFix..."
        }
    You MUST pre-fill report['program_slug'] (e.g., 'tesla', 'paypal')
    """
    if "program_slug" not in report:
        return "❌ report['program_slug'] missing. Cannot build Bugcrowd URL."

    if not Path(COOKIES_PATH).exists():
        return "❌ Bugcrowd login cookies missing. Run save_bugcrowd_cookies.py first."

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
            # Fill Title
            page.fill('input[name="report[vulnerability_title]"]', report["title"])

            # Fill Description / Body
            page.fill('textarea[name="report[vulnerability_description]"]', report["report"])

            # Optional: Fill severity, CVSS, etc (can be automated later)

            # Submit the report
            page.click('button[type="submit"]')
            time.sleep(5)

        except Exception as e:
            return f"❌ Error while submitting: {e}"

        browser.close()
        return "✅ Submitted successfully to Bugcrowd."
