import os
import logging
import requests
import subprocess
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
    logger.info(f"🔍 Shodan search: {query}")
    results = []
    try:
        res = client.search(query, limit=max_results)
        for match in res['matches']:
            ip = match.get('ip_str')
            port = match.get('port')
            org = match.get('org', 'n/a')
            host = f"{ip}:{port}"
            results.append(f"{host} ({org})")
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
        time.sleep(2)
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

# ------------------ SUBFINDER ------------------
def subfinder_scan(domain: str):
    logger.info(f"🤖 Subfinder scanning: {domain}")
    try:
        result = subprocess.check_output(["subfinder", "-d", domain, "-silent"], stderr=subprocess.DEVNULL)
        return result.decode().splitlines()
    except Exception as e:
        logger.warning(f"Subfinder failed: {e}")
        return []

# ------------------ HAKRAWLER ------------------
def hakrawler_scan(domain: str):
    logger.info(f"🤖 Hakrawler scanning: {domain}")
    try:
        result = subprocess.check_output(["hakrawler", "-url", f"https://{domain}", "-depth", "1"], stderr=subprocess.DEVNULL)
        return result.decode().splitlines()
    except Exception as e:
        logger.warning(f"Hakrawler failed: {e}")
        return []

# ------------------ ARJUN ------------------
def arjun_scan(domain: str):
    logger.info(f"🔍 Arjun scanning: {domain}")
    try:
        result = subprocess.check_output(["python3", "~/Arjun/arjun.py", "--urls", f"https://{domain}"], stderr=subprocess.DEVNULL)
        return result.decode().splitlines()
    except Exception as e:
        logger.warning(f"Arjun failed: {e}")
        return []

# ------------------ COMBINED RECON ------------------
def recon_domain(keyword: str):
    logger.info(f"🌐 Recon on keyword: {keyword}")
    shodan_results = shodan_search(keyword)
    dork_results = google_dork_search(f"site:{keyword}")
    subfinder_results = subfinder_scan(keyword)
    hakrawler_results = hakrawler_scan(keyword)
    arjun_results = arjun_scan(keyword)

    combined = list(set(shodan_results + dork_results + subfinder_results + hakrawler_results + arjun_results))
    logger.info(f"🔎 Found {len(combined)} unique assets.")
    return combined

# ✅ Required by submission orchestrator
def discover_assets(scope: str) -> list:
    return recon_domain(scope)

# Test run
if __name__ == "__main__":
    test_scope = "tesla.com"
    assets = discover_assets(test_scope)
    for asset in assets:
        print(" -", asset)
