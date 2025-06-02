import os
import logging
import requests
import time
from shodan import Shodan
from bs4 import BeautifulSoup

# 🔐 Load Shodan API key from environment variable
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 🔍 Initialize Shodan client
client = Shodan(SHODAN_API_KEY)

# ------------------ SHODAN RECON ------------------
def shodan_search(query: str, max_results: int = 50):
    # ✅ Clean and format the query for Shodan
    keyword = query.replace("*.", "").strip()
    formatted_query = f"hostname:{keyword}"
    logger.info(f"🔍 Shodan search: {formatted_query}")
    results = []
    try:
        res = client.search(formatted_query, limit=max_results)
        for match in res['matches']:
            ip = match.get('ip_str')
            port = match.get('port')
            org = match.get('org', 'n/a')
            host = f"http://{ip}:{port}"
            results.append(host)
    except Exception as e:
        logger.error(f"❌ Shodan error: {e}")
    return results

# ------------------ GOOGLE DORKING ------------------
def google_dork_search(dork: str, pages: int = 1):
    logger.info(f"🕵️ Google Dorking: {dork}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    found = set()
    for page in range(pages):
        time.sleep(2)  # Avoid being blocked
        start = page * 10
        url = f"https://www.google.com/search?q={dork}&start={start}"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a")
            for a in links:
                href = a.get("href")
                if href and href.startswith("/url?q="):
                    actual_url = href.split("/url?q=")[1].split("&sa=")[0]
                    found.add(actual_url)
        except Exception as e:
            logger.warning(f"⚠️ Dork scrape failed on page {page}: {e}")
    return list(found)

# ------------------ COMBINED LOGIC ------------------
def recon_domain(keyword: str):
    logger.info(f"🌐 Recon on keyword: {keyword}")
    shodan_results = shodan_search(keyword)
    dork_results = google_dork_search(f"site:{keyword}")
    combined = list(set(shodan_results + dork_results))
    logger.info(f"🔎 Found {len(combined)} unique assets.")
    return combined

# ✅ This is the function used by submission_orchestrator.py
def discover_assets(scope: str) -> list:
    return recon_domain(scope)

# For standalone testing
if __name__ == "__main__":
    test_scope = "tesla.com"
    assets = discover_assets(test_scope)
    for asset in assets:
        print(" -", asset)

