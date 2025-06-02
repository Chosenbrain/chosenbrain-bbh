import logging
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import requests
from datetime import datetime
from gpt_target_hunter import discover_targets as find_next_target, get_target_priority_score
from report_generator import generate_bug_report
from analysis import detailed_ai_analysis
from auto_submitter import auto_submit
from nuclei_scanner import run_nuclei_scan
from payload_injector import inject_payloads
from notify import alert
from memory import (
    load_scanned_targets,
    save_scanned_target,
    is_duplicate_bug,
    save_bug_fingerprint
)
from recon_engine import discover_assets
from dashboard_tracker import track_submission
from config import Config
from extensions import db
from models import Report
from factory import create_app
from notifications import send_discord_notification
from telegram_bot import send_bug_report

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_WORKERS = 3
BURP_API_KEY = os.getenv("BURP_API_KEY")
BURP_HOST = "http://127.0.0.1:1337/v0.1"
HEADERS = {
    "Authorization": f"Bearer {BURP_API_KEY}",
    "Content-Type": "application/json"
}

app = create_app()
app.app_context().push()

def run_burp_scan(url):
    try:
        logger.info(f"🦠 Starting Burp scan on {url}")
        resp = requests.post(f"{BURP_HOST}/scan", json={"url": url}, headers=HEADERS)
        resp.raise_for_status()
        scan_id = resp.json().get("scan_id")
        if not scan_id:
            return "❌ Failed to retrieve scan ID."
        logger.info(f"📱 Burp scan started: ID = {scan_id}")
        for _ in range(30):
            status_resp = requests.get(f"{BURP_HOST}/scan/{scan_id}/status", headers=HEADERS)
            status = status_resp.json().get("status", "")
            logger.info(f"⏳ Scan {scan_id} status: {status}")
            if status == "succeeded":
                break
            time.sleep(5)
        issues_resp = requests.get(f"{BURP_HOST}/scan/{scan_id}/issues", headers=HEADERS)
        issues = issues_resp.json()
        output = "🛡️ Burp Issues Found:\n"
        for issue in issues:
            output += f"- {issue['name']} | Severity: {issue['severity']} | {issue['issue_type']}\n"
        return output if issues else "✅ No critical issues found."
    except Exception as e:
        return f"💥 Burp scan failed: {str(e)}"

def run_all_deep_scanners(url: str) -> str:
    logger.info(f"🔬 Starting deep scans on {url}")
    results = {
        "Burp": run_burp_scan(url),
        "Payloads": inject_payloads(url),
        "Nuclei": run_nuclei_scan(url)
    }
    return "\n\n".join([f"## {tool} Output\n{output}" for tool, output in results.items()])

def process_asset(url, platform, program):
    logger.info(f"🌍 Scanning discovered asset: {url}")
    try:
        deep_scan_output = run_all_deep_scanners(url)
        if "No vulnerabilities" in deep_scan_output or deep_scan_output.strip() == "":
            logger.info(f"✅ No bugs found at {url}.")
            return
        gpt_analysis = detailed_ai_analysis(deep_scan_output)
        report_data = generate_bug_report(gpt_analysis, url)
        if is_duplicate_bug(report_data["report"]):
            logger.info("⚠️ Duplicate bug fingerprint found. Skipping submission.")
            return
        if platform in ["bugcrowd", "intigriti"]:
            report_data["program_slug"] = program.lower().replace(" ", "-")
        report = Report(
            target_url=url,
            scan_results=deep_scan_output,
            severity_score=report_data["priority_score"],
            ai_assessment="HIGH" if report_data["priority_score"] >= 8 else "LOW",
            gpt_analysis=report_data["gpt_analysis"],
            bounty_estimate=report_data["bounty_estimate"],
            status="Critical" if report_data["priority_score"] >= 8 else "Pending",
        )
        db.session.add(report)
        db.session.commit()
        if report.status == "Critical":
            send_discord_notification(
                target_url=url,
                severity=report.severity_score,
                ai_assessment=report.ai_assessment
            )
        result = auto_submit(report_data, platform)
        logger.info(f"🚀 Submission Result: {result}")
        if "✅" in result or "success" in result.lower():
            save_bug_fingerprint(report_data["report"])
            track_submission(program, platform, url, report_data["title"], result)
        alert(f"🦠 Bug submitted to {platform.title()} — {program}\n{report_data['title']}\n{result}")
        send_bug_report(
            telegram_app,
            Config.TELEGRAM_CHAT_ID,
            {
                "title": report_data["title"],
                "target": url,
                "severity": report.status,
                "url": url,
                "bounty": report_data["bounty_estimate"],
                "platform": platform.title(),
                "description": report_data["gpt_analysis"]
            }
        )
        logger.info(f"✅ Full cycle complete for {url}")
    except Exception as e:
        logger.exception(f"❌ Error processing asset {url}: {e}")
        alert(f"💥 Failed on {url}: {e}")

def run_full_cycle():
    try:
        target = find_next_target()
        if not target or not target.get("url"):
            logger.warning("⚠️ No valid target from GPT. Skipping.")
            return
        scope = target["scope"]
        platform = target["platform"].lower()
        program = target["program"]
        logger.info(f"🎯 [{platform.upper()}] Target: {program} → {scope}")
        score = get_target_priority_score(target)
        if score < 5:
            logger.info(f"⏩ Skipping low-priority target: {score}/10")
            return
        logger.info(f"⭐ Priority Score: {score}/10")
        assets = discover_assets(scope)
        if not assets:
            logger.warning("🚫 No assets found from Shodan. Skipping.")
            return
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_asset, url, platform, program) for url in assets]
            for future in as_completed(futures):
                future.result()
    except Exception as e:
        logger.exception("💥 Error during submission cycle")
        alert(f"❌ BBH failed on this round: {e}")

def update_bug_tracker(new_bug, target):
    path = "bug_tracker.json"
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {
            "total_bugs_found": 0,
            "last_target": "",
            "last_updated": "",
            "latest_bug": "",
            "all_bugs": []
        }

    # Update data
    data["total_bugs_found"] += 1
    data["last_target"] = target
    data["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    data["latest_bug"] = f"{new_bug.get('title', 'Bug')} | Severity: {new_bug.get('severity', 'N/A')}"

    # Keep full bug object in list
    data["all_bugs"].append({
        "title": new_bug.get("title"),
        "target": new_bug.get("target"),
        "severity": new_bug.get("severity"),
        "bounty": new_bug.get("bounty"),
        "platform": new_bug.get("platform"),
        "description": new_bug.get("description"),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    })

    # Write updated tracker
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def main():
    logger.info("🦠 Starting Chosenbrain BBH Multi-Day Hunt Mode...")
    try:
        while True:
            logger.info("\n🔁 New Autonomous Scan Cycle Starting...")
            run_full_cycle()
            logger.info("🛌 Sleeping before next cycle...")
            time.sleep(300)  # Sleep 5 minutes before next full cycle
    except KeyboardInterrupt:
        logger.warning("Interrupted by user. Exiting...")
    except Exception as e:
        logger.exception(f"Fatal error in main loop: {e}")

if __name__ == "__main__":
    main()
