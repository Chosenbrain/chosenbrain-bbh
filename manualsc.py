import os
import shutil
import subprocess
import uuid
import threading
import datetime
import json
import re
from flask import Blueprint, request, jsonify

manual_scan_bp = Blueprint("manual_scan", __name__)
MANUAL_SCAN_DIR = "./manual_scans"
SCAN_STATUS = {}

TOOLS = {
    "bandit": lambda path: ["bandit", "-r", path, "-f", "json"],
    "semgrep": lambda path: ["semgrep", "--config=auto", path, "--json"],
    "gitleaks": lambda path: ["gitleaks", "detect", "--source", path, "--no-banner", "--report-format", "json"],
    "trufflehog": lambda path: ["trufflehog", "filesystem", path],
    "slither": lambda path: ["slither", path],
    "gosec": lambda path: ["gosec", "-fmt", "json", "./..."],
    "eslint": lambda path: ["eslint", path, "--ext", ".js,.jsx"],
    "dockle": lambda path: ["dockle", path],
    "tfsec": lambda path: ["tfsec", path]
}

def clone_repo(repo_url, dest_path):
    try:
        print(f"🔄 Cloning into: {dest_path}")
        result = subprocess.run(["git", "clone", repo_url, dest_path], capture_output=True, text=True, check=True)
        print(result.stdout)
        print(result.stderr)
        if not os.path.exists(dest_path) or not os.listdir(dest_path):
            print(f"❌ Repo cloned but EMPTY or missing: {dest_path}")
            return False
        print(f"✅ Clone SUCCESS: {repo_url}")
        print(f"📦 Contents: {os.listdir(dest_path)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git clone failed with error:\n{e.stderr}")
        return False

def scan_repo(scan_id, repo_url):
    scan_path = os.path.join(MANUAL_SCAN_DIR, scan_id)
    result_file = os.path.join(scan_path, "results.txt")
    repo_code_path = os.path.join(scan_path, "repo")
    os.makedirs(scan_path, exist_ok=True)

    SCAN_STATUS[scan_id] = {
        "status": "scanning",
        "started": str(datetime.datetime.utcnow()),
        "progress": [],
        "error": None
    }

    print(f"🟡 Scan started: {scan_id}")
    if not clone_repo(repo_url, repo_code_path):
        SCAN_STATUS[scan_id]["status"] = "error"
        SCAN_STATUS[scan_id]["error"] = "Clone failed or repo empty."
        print(f"❌ SCAN ABORTED: {repo_code_path} not valid.")
        return

    print(f"✅ Repo ready: {repo_code_path}")
    for tool in TOOLS:
        print(f"🔍 {tool} started")
        SCAN_STATUS[scan_id]["progress"].append(f"{tool} started")
        cmd = TOOLS[tool](repo_code_path)
        with open(result_file, "a") as out:
            out.write(f"\n\n--- {tool.upper()} ---\n")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_code_path, timeout=300)
                out.write(result.stdout)
                out.write(result.stderr)
            except Exception as e:
                out.write(f"[x] {tool} error: {e}\n")
        print(f"✅ {tool} finished")
        SCAN_STATUS[scan_id]["progress"].append(f"{tool} finished")

    SCAN_STATUS[scan_id]["status"] = "done"
    SCAN_STATUS[scan_id]["finished"] = str(datetime.datetime.utcnow())
    print(f"✅ SCAN COMPLETE: {scan_id}")
    shutil.rmtree(repo_code_path, ignore_errors=True)
    print(f"🧹 Cleaned up: {repo_code_path}")

@manual_scan_bp.route("/start_manual_scan", methods=["POST"])
def start_manual_scan():
    data = request.get_json()
    repo_url = data.get("repo_url")
    if not repo_url:
        return jsonify({"error": "Missing repo_url"}), 400
    scan_id = str(uuid.uuid4())
    threading.Thread(target=scan_repo, args=(scan_id, repo_url)).start()
    return jsonify({"message": "Scan started", "scan_id": scan_id})

@manual_scan_bp.route("/manual_scan_status/<scan_id>", methods=["GET"])
def get_manual_scan_status(scan_id):
    return jsonify(SCAN_STATUS.get(scan_id, {"error": "Scan ID not found"}))

@manual_scan_bp.route("/manual_scan_results/<scan_id>", methods=["GET"])
def get_manual_scan_results(scan_id):
    result_file = os.path.join(MANUAL_SCAN_DIR, scan_id, "results.txt")
    if not os.path.exists(result_file):
        return jsonify({"error": "Results not available"}), 404
    with open(result_file) as f:
        return f.read(), 200, {'Content-Type': 'text/plain'}
