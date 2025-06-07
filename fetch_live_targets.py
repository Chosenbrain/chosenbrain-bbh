import os
import re
import requests
import shutil
from dotenv import load_dotenv
from source_code_scanner import scan_repo_for_vulns

load_dotenv()

hackerone_cache = []
intigriti_cache = []

hackerone_index = 0
intigriti_index = 0

BATCH_SIZE = 5
TEMP_REPO_DIR = "temp_repo_scan"

GITHUB_REPO_REGEX = re.compile(r"https?://github.com/[\w.-]+/[\w.-]+")

def fetch_hackerone_programs():
    global hackerone_cache

    username = os.getenv("HACKERONE_USERNAME")
    token = os.getenv("HACKERONE_API_TOKEN")
    if not username or not token:
        print("❌ Missing HackerOne credentials.")
        return []

    url = "https://api.hackerone.com/v1/hackers/programs?page[size]=100"
    auth = (username, token)
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, auth=auth, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        programs = []
        for item in data.get("data", []):
            handle = item.get("attributes", {}).get("handle")
            submission_status = item.get("attributes", {}).get("submission_state")
            if handle and submission_status == "open":
                url = f"https://hackerone.com/{handle}"
                programs.append(url)

        hackerone_cache = programs
        return programs

    except requests.RequestException as e:
        print(f"HackerOne fetch error: {e}")
        return []

def fetch_intigriti_programs():
    global intigriti_cache

    token = os.getenv("INTIGRITI_API_TOKEN")
    if not token:
        print("❌ INTIGRITI_API_TOKEN not set.")
        return []

    url = "https://api.intigriti.com/external/researcher/v1/programs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        if "application/json" not in response.headers.get("Content-Type", ""):
            print("❌ Intigriti response is not JSON.")
            print(f"Raw Response: {response.text}")
            return []

        data = response.json()

        if not isinstance(data, dict) or "records" not in data:
            print("❌ Intigriti response format unexpected.")
            print(f"Raw Data: {data}")
            return []

        records = data["records"]
        if not isinstance(records, list):
            print("❌ Intigriti 'records' field is not a list.")
            print(f"Raw Records: {records}")
            return []

        programs = [
            program.get("webLinks", {}).get("detail", program.get("handle", ""))
            for program in records
            if isinstance(program, dict)
        ]

        intigriti_cache = programs
        return programs

    except requests.RequestException as e:
        print(f"Intigriti fetch error: {e}")
        print(f"Raw Response: {getattr(e.response, 'text', 'No response')}")
        return []
    except ValueError as e:
        print(f"Intigriti JSON decode error: {e}")
        print(f"Raw Response: {response.text}")
        return []

def extract_and_scan_repos(program_urls):
    scanned_targets = []
    for url in program_urls:
        match = GITHUB_REPO_REGEX.search(url)
        if match:
            repo_url = match.group()
            print(f"🧠 Found GitHub repo: {repo_url}. Cloning and scanning...")
            try:
                scan_repo_for_vulns(repo_url, TEMP_REPO_DIR)
            finally:
                shutil.rmtree(TEMP_REPO_DIR, ignore_errors=True)
        scanned_targets.append(url)
    return scanned_targets

def get_all_live_targets():
    global hackerone_index, intigriti_index

    targets = {
        "hackerone": [],
        "intigriti": []
    }

    if not isinstance(hackerone_cache, list) or not hackerone_cache:
        fetch_hackerone_programs()
    if not isinstance(intigriti_cache, list) or not intigriti_cache:
        fetch_intigriti_programs()

    if isinstance(hackerone_cache, list) and hackerone_cache:
        start = hackerone_index
        end = start + BATCH_SIZE
        urls = hackerone_cache[start:end]
        targets["hackerone"] = extract_and_scan_repos(urls)
        hackerone_index = end if end < len(hackerone_cache) else 0

    if isinstance(intigriti_cache, list) and intigriti_cache:
        start = intigriti_index
        end = start + BATCH_SIZE
        urls = intigriti_cache[start:end]
        targets["intigriti"] = extract_and_scan_repos(urls)
        intigriti_index = end if end < len(intigriti_cache) else 0

    return targets
