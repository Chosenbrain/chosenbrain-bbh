import os
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

BUG_HISTORY_FILE = "seen_bugs.json"

def compute_bug_hash(report: dict) -> str:
    """
    Generate a stable hash from key fields of a bug report.
    """
    data = f"{report.get('title', '').lower()}|{report.get('url', '').lower()}"
    return hashlib.sha256(data.encode()).hexdigest()

def load_seen_hashes() -> set:
    if not os.path.exists(BUG_HISTORY_FILE):
        return set()
    try:
        with open(BUG_HISTORY_FILE, "r") as f:
            return set(json.load(f))
    except Exception as e:
        logger.warning(f"Could not load bug history: {e}")
        return set()

def save_seen_hashes(hashes: set):
    try:
        with open(BUG_HISTORY_FILE, "w") as f:
            json.dump(list(hashes), f, indent=2)
    except Exception as e:
        logger.error(f"Could not save bug history: {e}")

def is_duplicate(report: dict) -> bool:
    """
    Check if a bug report has already been submitted.
    """
    h = compute_bug_hash(report)
    seen = load_seen_hashes()
    return h in seen

def mark_as_submitted(report: dict):
    """
    Record the bug hash to avoid future duplicates.
    """
    h = compute_bug_hash(report)
    seen = load_seen_hashes()
    seen.add(h)
    save_seen_hashes(seen)
