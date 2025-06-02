import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, current_app
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
from dashboard_tracker import get_submission_logs  # ✅ already imported

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

# ✅ NEW DASHBOARD ROUTE
@app.route("/dashboard")
def dashboard():
    bugs = get_submission_logs()
    return render_template("dashboard.html", bugs=bugs)

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    env = os.getenv("FLASK_ENV", "production").lower()
    debug = env == "development"
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)
