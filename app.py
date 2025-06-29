import os
import logging
import threading
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, current_app
import json
from dotenv import load_dotenv
from flask_wtf import CSRFProtect
from extensions import db
from factory import create_app, csrf
from models import Report
from forms import ScanForm
from analysis import (
    detailed_ai_analysis,
    get_bounty_estimate,
    get_priority_score
)
from web_scanner import analyze_web_target
from dashboard_tracker import get_submission_logs
from manualsc import scan_repo, get_manual_scan_status, MANUAL_SCAN_DIR, manual_scan_bp, SCAN_STATUS  # ✅ use correct import

# --------------------------
# Load environment
# --------------------------
load_dotenv()

# --------------------------
# Logging Setup
# --------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --------------------------
# Flask App & Extensions
# --------------------------
app = create_app()

# --------------------------
# Malware protection (basic)
# --------------------------
DANGEROUS_PATTERNS = [
    "rm -rf", "eval(", "exec(", "os.system", "subprocess",
    "base64.b64decode", "powershell", "netsh", "wget http",
    "curl http", "Invoke-Expression", "vbscript", "CreateObject",
    "Set-Content", "Start-Process", "shutdown -s", "cmd.exe", "regsvr32"
]

def is_probably_virus(code: str) -> bool:
    lower_code = code.lower()
    return any(pattern in lower_code for pattern in DANGEROUS_PATTERNS)

# --------------------------
# Routes
# --------------------------
@app.route("/")
def index():
    form = ScanForm()
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    return render_template("index.html", reports=reports, form=form)

@csrf.exempt
@app.route("/scan_target", methods=["POST"])
def scan_target():
    url = request.form.get("target_url", "").strip()
    if not url:
        flash("No target URL provided.", "danger")
        return redirect(url_for("index"))

    result = analyze_web_target(url)
    rpt = Report(
        target_url=url,
        scan_results=str(result.get("nuclei_results")),
        severity_score=result.get("priority_score"),
        ai_assessment="HIGH" if result.get("priority_score", 0) >= 8 else "LOW",
        gpt_analysis=result.get("gpt_analysis"),
        bounty_estimate=result.get("bounty_estimate"),
        status="Critical" if result.get("priority_score", 0) >= 8 else "Pending",
    )
    db.session.add(rpt)
    db.session.commit()

    flash("Target scanned and analyzed.", "success")
    return redirect(url_for("index"))

@app.route("/report/<int:report_id>")
def view_report(report_id):
    rpt = Report.query.get_or_404(report_id)
    return render_template("report.html", report=rpt)

@app.route("/report/<int:report_id>/confirm", methods=["POST"])
def confirm_report(report_id):
    rpt = Report.query.get_or_404(report_id)
    rpt.status = "Confirmed"
    db.session.commit()
    return redirect(url_for("view_report", report_id=report_id))

@app.route("/healthz")
def health_check():
    db_ok = True
    try:
        db.session.execute("SELECT 1")
    except Exception as e:
        current_app.logger.error(f"DB health check failed: {e}")
        db_ok = False

    status_code = 200 if db_ok else 503
    return jsonify({"database": "ok" if db_ok else "error"}), status_code

@app.route("/dashboard")
def dashboard():
    bugs = get_submission_logs()
    return render_template("dashboard.html", bugs=bugs)

@app.route("/manual-scan", methods=["GET"])
def manual_scan():
    return render_template("manual_scan.html")

# ✅ EXEMPTED from CSRF because it's an API endpoint
@csrf.exempt
@app.route("/start_manual_scan", methods=["POST"])
def start_manual_scan_route():
    data = request.get_json()
    repo_url = data.get("repo_url")
    if not repo_url:
        return jsonify({"error": "Missing repo_url"}), 400

    session_id = os.urandom(8).hex()
    threading.Thread(target=scan_repo, args=(session_id, repo_url)).start()
    return jsonify({"message": "Scan started", "scan_id": session_id})


@app.route("/manual_scan_status/<scan_id>", methods=["GET"])
def manual_scan_status(scan_id):
    status = SCAN_STATUS.get(scan_id)
    if not status:
        return jsonify({"error": "Scan ID not found"}), 404

    # Filter for only JSON-safe values
    clean_status = {}
    for k, v in status.items():
        try:
            json.dumps(v)  # test if JSON-serializable
            clean_status[k] = v
        except (TypeError, OverflowError):
            clean_status[k] = str(v)  # fallback to string

    return jsonify(clean_status)


@csrf.exempt
@app.route("/manual_scan_results/<session_id>", methods=["GET"])
def manual_scan_results(session_id):
    scan_path = os.path.join(MANUAL_SCAN_DIR, session_id, "results.txt")
    if not os.path.exists(scan_path):
        return jsonify({"error": "Results not available"}), 404
    with open(scan_path) as f:
        return f.read(), 200, {'Content-Type': 'text/plain'}

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    env = os.getenv("FLASK_ENV", "production").lower()
    debug = env == "development"
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)
