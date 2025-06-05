import logging
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import requests
from datetime import datetime
import json

from fetch_live_targets import get_all_live_targets
from report_generator import generate_bug_report
from analysis import detailed_ai_analysis
from auto_submitter import auto_submit
from nuclei_scanner import run_nuclei_scan
from payload_injector import inject_payloads
from memory import is_duplicate_bug, save_bug_fingerprint
from recon_engine import discover_assets
from dashboard_tracker import track_submission
from config import Config
from extensions import db
from models import Report
from factory import create_app
from notifications import alert, send_bug_report
from deep_scanner import run_wapiti_scan, run_nikto_scan, run_sqlmap_scan
from telegram_bot import telegram_app as telegram_bot

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chosenbrain-bbh")

MAX_WORKERS = 3
BURP_API_KEY = os.getenv("BURP_API_KEY")
BURP_HOST = "http://127.0.0.1:1337/v0.1"
HEADERS = {
    "Authorization": f"Bearer {BURP_API_KEY}",
    "Content-Type": "application/json"
}

STATUS_FILE = "status.json"
BUG_TRACKER_FILE = "bug_tracker.json"

app = create_app()
app.app_context().push()

platform_cycle = ["hackerone", "bugcrowd", "intigriti", "yeswehack"]
current_index = 0

def update_status(status: dict):
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to update status.json: {e}")

def update_bug_tracker(data: dict):
    try:
        if os.path.exists(BUG_TRACKER_FILE):
            with open(BUG_TRACKER_FILE, "r") as f:
                bug_data = json.load(f)
        else:
            bug_data = {
                "total_bugs_found": 0,
                "latest_bug": None,
                "last_target": None,
                "last_platform": None
            }

        if data.get("new_bug_found"):
            bug_data["total_bugs_found"] += 1
            bug_data["latest_bug"] = data.get("title")
        bug_data["last_target"] = data.get("target")
        bug_data["last_platform"] = data.get("platform")

        with open(BUG_TRACKER_FILE, "w") as f:
            json.dump(bug_data, f, indent=2)

    except Exception as e:
        logger.error(f"Failed to update bug_tracker.json: {e}")

def run_burp_scan(url):
    try:
        logger.info(f"Starting Burp scan on {url}")
        resp = requests.post(f"{BURP_HOST}/scan", json={"url": url}, headers=HEADERS)
        resp.raise_for_status()
        scan_id = resp.json().get("scan_id")
        if not scan_id:
            return "Failed to retrieve scan ID."

        for _ in range(30):
            status_resp = requests.get(f"{BURP_HOST}/scan/{scan_id}/status", headers=HEADERS)
            status = status_resp.json().get("status", "")
            if status == "succeeded":
                break
            time.sleep(5)

        issues_resp = requests.get(f"{BURP_HOST}/scan/{scan_id}/issues", headers=HEADERS)
        issues = issues_resp.json()
        output = "\n".join([f"- {i['name']} | Severity: {i['severity']} | {i['issue_type']}" for i in issues])
        return output if issues else "No critical issues found."
    except Exception as e:
        return f"Burp scan failed: {str(e)}"

def run_all_deep_scanners(url: str) -> dict:
    logger.info(f"Running all deep scanners on {url}")
    return {
        "Burp": run_burp_scan(url),
        "Payloads": inject_payloads(url),
        "Nuclei": run_nuclei_scan(url),
        "Wapiti": run_wapiti_scan(url),
        "Nikto": run_nikto_scan(url),
        "SQLMap": run_sqlmap_scan(url)
    }

def process_asset(url, platform):
    logger.info(f"Scanning asset: {url}")
    update_status({
        "state": "scanning",
        "target": url,
        "platform": platform,
        "started_at": str(datetime.utcnow())
    })
    try:
        scanner_outputs = run_all_deep_scanners(url)
        combined_output = "\n\n".join([f"## {tool} Output\n{output}" for tool, output in scanner_outputs.items()])

        if all("No" in out or out.strip() == "" for out in scanner_outputs.values()):
            logger.info(f"No bugs found at {url}.")
            update_status({
                "state": "idle",
                "target": url,
                "platform": platform,
                "finished_at": str(datetime.utcnow())
            })
            return

        gpt_analysis = detailed_ai_analysis(combined_output)
        report_data = generate_bug_report(gpt_analysis, url)

        if not report_data or "priority_score" not in report_data:
            logger.warning("⚠️ Incomplete report data. Skipping alert and submission.")
            update_status({
                "state": "idle",
                "target": url,
                "platform": platform,
                "finished_at": str(datetime.utcnow())
            })
            return

        if is_duplicate_bug(report_data["report"]):
            logger.info("Duplicate bug fingerprint found. Skipping submission.")
            return

        report = Report(
            target_url=url,
            scan_results=combined_output,
            severity_score=report_data["priority_score"],
            ai_assessment="HIGH" if report_data["priority_score"] >= 8 else "LOW",
            gpt_analysis=report_data["gpt_analysis"],
            bounty_estimate=report_data["bounty_estimate"],
            status="Critical" if report_data["priority_score"] >= 8 else "Pending",
        )
        db.session.add(report)
        db.session.commit()

        result = auto_submit(report_data, platform)
        logger.info(f"Submission Result: {result}")

        if "✅" in result or "success" in result.lower():
            save_bug_fingerprint(report_data["report"])
            track_submission("", platform, url, report_data["title"], result)
            update_bug_tracker({
                "new_bug_found": True,
                "title": report_data["title"],
                "target": url,
                "platform": platform
            })

        alert(
            message=report_data["title"],
            platform=platform,
            program_name=report_data.get("program_name", "Unknown"),
            target_url=url,
            bounty=report_data["bounty_estimate"],
            severity=report_data["priority_score"],
            ai_assessment=report.ai_assessment,
            details_url=report_data.get("program_link", ""),
            repro_steps=report_data.get("steps_to_reproduce"),
            submission_note=report_data.get("submission_note"),
            tool_used=", ".join(scanner_outputs.keys())
        )

        send_bug_report(telegram_bot, Config.TELEGRAM_CHAT_ID, {
            "title": report_data["title"],
            "target": url,
            "severity": report.status,
            "url": url,
            "bounty": report_data["bounty_estimate"],
            "platform": platform.title(),
            "description": report_data["gpt_analysis"],
            "program_link": report_data.get("program_link", "")
        })

        update_status({
            "state": "idle",
            "target": url,
            "platform": platform,
            "finished_at": str(datetime.utcnow())
        })

        logger.info(f"✅ Completed full cycle for {url}")

    except Exception as e:
        logger.exception(f"❌ Error processing asset {url}: {e}")
        update_status({
            "state": "error",
            "target": url,
            "platform": platform,
            "finished_at": str(datetime.utcnow())
        })
        alert(
            message="Error during asset processing",
            platform=platform,
            target_url=url,
            bounty="N/A",
            severity=0,
            ai_assessment="Error",
            details_url="",
            repro_steps="",
            submission_note=str(e),
            tool_used="System"
        )


def run_full_cycle():
    global current_index
    try:
        targets_by_platform = get_all_live_targets()
        if not targets_by_platform:
            logger.warning("No live targets fetched.")
            return

        platform = platform_cycle[current_index % len(platform_cycle)]
        all_targets = targets_by_platform.get(platform, [])
        targets = all_targets[:5]

        logger.info(f"Scanning platform: {platform.upper()} with {len(targets)} targets")
        for url in targets:
            assets = discover_assets(url)
            if not assets:
                logger.warning(f"No assets found for {url}. Skipping.")
                continue

            for asset in assets:
                process_asset(asset, platform)

        current_index += 1

    except Exception as e:
        logger.exception("Error during submission cycle")
        update_status({
            "state": "error",
            "target": "N/A",
            "platform": "N/A",
            "finished_at": str(datetime.utcnow())
        })
        alert(
            message="Cycle Failure",
            platform="N/A",
            target_url="N/A",
            bounty="N/A",
            severity=0,
            ai_assessment="Error",
            details_url="",
            repro_steps="",
            submission_note=str(e),
            tool_used="System"
        )

def main():
    logger.info("Starting Chosenbrain BBH Multi-Day Hunt Mode...")
    try:
        while True:
            logger.info("New Autonomous Scan Cycle Starting...")
            run_full_cycle()
            logger.info("Sleeping before next cycle...")
            time.sleep(300)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user. Exiting...")
    except Exception as e:
        logger.exception(f"Fatal error in main loop: {e}")

if __name__ == "__main__":
    main()
