import os
import re
import requests
import random
from dotenv import load_dotenv
from urllib.parse import urlparse
from bs4 import BeautifulSoup

load_dotenv()

hackerone_cache = []
intigriti_cache = []


def fetch_hackerone_programs():
    global hackerone_cache
    username = os.getenv("HACKERONE_USERNAME")
    token = os.getenv("HACKERONE_API_TOKEN")
    if not username or not token:
        print("❌ Missing HackerOne credentials.")
        return []

    url = "https://api.hackerone.com/v1/hackers/programs?page[size]=100"
    headers = {"Accept": "application/json"}
    auth = (username, token)

    try:
        response = requests.get(url, auth=auth, headers=headers, timeout=15)
        response.raise_for_status()
        programs = []

        for item in response.json().get("data", []):
            handle = item.get("attributes", {}).get("handle")
            submission_state = item.get("attributes", {}).get("submission_state")
            if handle and submission_state == "open":
                programs.append(f"https://hackerone.com/{handle}")
        hackerone_cache = programs
        return programs
    except Exception as e:
        print(f"❌ HackerOne fetch error: {e}")
        return []


def extract_hackerone_targets(handle_url):
    username = os.getenv("HACKERONE_USERNAME")
    token = os.getenv("HACKERONE_API_TOKEN")
    if not username or not token:
        print("❌ Missing HackerOne credentials.")
        return []

    try:
        handle = handle_url.strip("/").split("/")[-1]
        api_url = f"https://api.hackerone.com/v1/hackers/programs/{handle}/structured_scopes"
        headers = {"Accept": "application/json"}
        auth = (username, token)

        response = requests.get(api_url, auth=auth, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        domains = []
        for scope in data.get("data", []):
            attr = scope.get("attributes", {})
            if attr.get("eligible_for_submission") and attr.get("asset_type") == "URL":
                asset = attr.get("asset_identifier", "")
                domain = urlparse(asset).netloc or asset
                if domain:
                    domains.append(domain.lower())
        return list(set(domains))

    except Exception as e:
        print(f"❌ Error fetching H1 targets for {handle_url}: {e}")
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
        data = response.json()
        programs = [(r["programId"], r.get("webLinks", {}).get("detail", "")) for r in data.get("records", []) if r.get("programId")]
        intigriti_cache = programs
        return programs
    except Exception as e:
        print(f"❌ Intigriti fetch error: {e}")
        return []


def extract_intigriti_targets(program_id):
    token = os.getenv("INTIGRITI_API_TOKEN")
    if not token:
        return []

    url = f"https://api.intigriti.com/external/researcher/v1/programs/{program_id}/assets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        domains = []
        for asset in data.get("assets", []):
            if asset.get("type") == "URL" and asset.get("eligibleForSubmission"):
                domain = urlparse(asset.get("endpoint", "")).netloc
                if domain:
                    domains.append(domain.lower())
        return list(set(domains))
    except Exception as e:
        print(f"❌ Intigriti asset fetch failed for {program_id}: {e}")
        return []


def get_all_live_targets():
    targets = {"hackerone": [], "intigriti": []}

    if not hackerone_cache:
        fetch_hackerone_programs()
    if not intigriti_cache:
        fetch_intigriti_programs()

    if hackerone_cache:
        selected = random.choice(hackerone_cache)
        print(f"🏆 Randomly selected H1 program: {selected}")
        targets["hackerone"] = extract_hackerone_targets(selected)
        if not targets["hackerone"]:
            print("⚠️ No targets extracted from selected H1 program.")

    if intigriti_cache:
        selected_id, detail_url = random.choice(intigriti_cache)
        print(f"🏆 Randomly selected Intigriti program: {detail_url}")
        targets["intigriti"] = extract_intigriti_targets(selected_id)
        if not targets["intigriti"]:
            print("⚠️ No targets extracted from selected Intigriti program.")

    return targets
