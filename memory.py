import json
import os
import hashlib

SCANNED_PROGRAMS_FILE = "scanned_targets.json"
BUG_MEMORY_FILE = "submitted_bugs.json"

# === PROGRAM MEMORY ===
def load_scanned_targets() -> set:
    if not os.path.exists(SCANNED_PROGRAMS_FILE):
        return set()
    try:
        with open(SCANNED_PROGRAMS_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_scanned_target(program_slug: str):
    targets = load_scanned_targets()
    targets.add(program_slug)
    with open(SCANNED_PROGRAMS_FILE, "w") as f:
        json.dump(list(targets), f)


# === BUG MEMORY ===
def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

def load_bug_fingerprints() -> set:
    if not os.path.exists(BUG_MEMORY_FILE):
        return set()
    try:
        with open(BUG_MEMORY_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_bug_fingerprint(report_text: str):
    memory = load_bug_fingerprints()
    fingerprint = _fingerprint(report_text)
    memory.add(fingerprint)
    with open(BUG_MEMORY_FILE, "w") as f:
        json.dump(list(memory), f)

def is_duplicate_bug(report_text: str) -> bool:
    fingerprint = _fingerprint(report_text)
    return fingerprint in load_bug_fingerprints()


def get_latest_vulnerabilities():
    # This should return a list of dicts like:
    return [
        {
            "attack": "XSS",
            "url": "http://example.com/vuln",
            "payload": "<script>alert(1)</script>",
            "platform": "HackerOne",
            "reward": "$500",
            "description": "Reflected XSS in search parameter."
        }
    ]
