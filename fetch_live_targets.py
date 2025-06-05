import os
import requests
from dotenv import load_dotenv

load_dotenv()

hackerone_cache = []
intigriti_cache = []

hackerone_index = 0
intigriti_index = 0

BATCH_SIZE = 5

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
                programs.append(handle)

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
        targets["hackerone"] = hackerone_cache[start:end]
        hackerone_index = end if end < len(hackerone_cache) else 0

    if isinstance(intigriti_cache, list) and intigriti_cache:
        start = intigriti_index
        end = start + BATCH_SIZE
        targets["intigriti"] = intigriti_cache[start:end]
        intigriti_index = end if end < len(intigriti_cache) else 0

    return targets
