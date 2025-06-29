import subprocess
import requests
import logging
import os
from urllib.parse import urlparse
from sanitize_urls_fix import clean_asset_urls  # 🔧 Sanitize added

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recon_engine")

DIRSEARCH_PATH = "/root/dirsearch/dirsearch.py"  # Adjust path if needed
ARJUN_MODULE = "arjun"  # Assumes Arjun is installed
TEMP_URL_FILE = "/tmp/arjun_urls.txt"

def normalize_url(url: str) -> str:
    if not url.startswith("http"):
        return "https://" + url
    return url

def run_command(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL)
        return output.decode().splitlines()
    except subprocess.CalledProcessError as e:
        logger.warning(f"Command failed: {e}")
        return []

def subfinder(domain):
    logger.info(f"🌐 Subfinder: {domain}")
    return run_command(f"subfinder -d {domain} -silent")

def hakrawler_scan(domain):
    logger.info(f"🔎 Hakrawler: {domain}")
    return run_command(f"echo https://{domain} | hakrawler -subs -depth 1")

def arjun_scan(domain):
    logger.info(f"🔧 Arjun: {domain}")
    try:
        with open(TEMP_URL_FILE, "w") as f:
            f.write(f"https://{domain}")
        return run_command(f"python3 -m {ARJUN_MODULE} --urls {TEMP_URL_FILE}")
    except Exception as e:
        logger.warning(f"Arjun failed: {e}")
        return []

def dirsearch_scan(domain):
    logger.info(f"📁 Dirsearch: {domain}")
    try:
        report_file = "/tmp/dirsearch.txt"
        command = f"python3 {DIRSEARCH_PATH} -u https://{domain} -e php,asp,aspx,jsp,html,js,txt -o {report_file} --output-format plain"
        subprocess.run(command, shell=True, stderr=subprocess.DEVNULL)
        if os.path.exists(report_file):
            with open(report_file, "r") as f:
                return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.warning(f"Dirsearch failed: {e}")
    return []

def wayback_scan(domain):
    logger.info(f"📦 Wayback Machine: {domain}")
    try:
        response = requests.get(
            f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=text&fl=original&collapse=urlkey",
            timeout=10
        )
        return response.text.splitlines()
    except Exception as e:
        logger.warning(f"Wayback failed: {e}")
        return []

def google_dorks(domain):
    logger.info(f"🕵️ Google Dorking: site:{domain}")
    return [
        f"https://www.google.com/search?q=site:{domain}+inurl:login",
        f"https://www.google.com/search?q=site:{domain}+ext:php",
        f"https://www.google.com/search?q=site:{domain}+ext:js",
        f"https://www.google.com/search?q=site:{domain}+inurl:admin"
    ]

def shodan_scan(domain):
    logger.info(f"🔍 Shodan search: {domain}")
    return [f"https://www.shodan.io/search?query=hostname:{domain}"]

def discover_assets(domain: str):
    domain = domain.strip().lower()
    if domain.startswith("http"):
        domain = urlparse(domain).netloc

    logger.info(f"🔭 Running deep recon on: {domain}")
    assets = set()

    assets.update(subfinder(domain))
    assets.update(hakrawler_scan(domain))
    assets.update(arjun_scan(domain))
    assets.update(dirsearch_scan(domain))
    assets.update(wayback_scan(domain))
    assets.update(google_dorks(domain))
    assets.update(shodan_scan(domain))

    # Normalize + Sanitize with custom filter
    cleaned = clean_asset_urls([normalize_url(url.strip()) for url in assets if url.strip()])
    logger.info(f"✅ Found {len(cleaned)} unique URLs.")
    return cleaned

