import os
import json
from datetime import datetime

TRACK_FILE = "submissions_log.json"

def track_submission(platform: str, program: str, url: str, title: str, bounty: float | None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "platform": platform,
        "program": program,
        "url": url,
        "title": title,
        "bounty": bounty or 0.0
    }
    logs = []
    if os.path.exists(TRACK_FILE):
        with open(TRACK_FILE, "r") as f:
            try:
                logs = json.load(f)
            except Exception:
                logs = []
    logs.append(entry)
    with open(TRACK_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def get_submission_logs():
    if not os.path.exists(TRACK_FILE):
        return []
    with open(TRACK_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return []
