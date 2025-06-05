import os
import subprocess
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ VPS paths for Burp
BURP_ENABLED = True
BURP_JAR_PATH = "./burpsuite_pro_v2025.4.4.jar"  # Already in current folder
BURP_CONFIG_PATH = "./bbh_config.json"
BURP_PROJECT_FILE = "./burp_project.burp"

def run_burp_scan(url: str) -> str:
    if not BURP_ENABLED:
        return "🔕 Burp Suite scan skipped (disabled)"
    try:
        config = {
            "target": {
                "scope": {
                    "include": [{
                        "enabled": True,
                        "protocol": "https" if url.startswith("https") else "http",
                        "host": url.replace("https://", "").replace("http://", "").split("/")[0],
                        "port": 443 if url.startswith("https") else 80
                    }]
                }
            }
        }

        with open(BURP_CONFIG_PATH, "w") as f:
            json.dump(config, f)

        subprocess.Popen([
            "java", "-Djava.awt.headless=true", "-jar", BURP_JAR_PATH,
            f"--project-file={BURP_PROJECT_FILE}",
            f"--config-file={BURP_CONFIG_PATH}"
        ])
        return f"✅ Burp scan launched for {url} (check Burp logs separately)"
    except Exception as e:
        return f"❌ Failed to launch Burp scan: {e}"

def run_wapiti_scan(url: str) -> str:
    try:
        result = subprocess.run(["wapiti", "-u", url], capture_output=True, text=True, timeout=600)
        return result.stdout or "ℹ️ Wapiti returned no output."
    except Exception as e:
        logger.error(f"Wapiti scan failed: {e}")
        return f"⚠️ Wapiti error: {e}"

def run_nikto_scan(url: str) -> str:
    try:
        result = subprocess.run(["nikto", "-host", url], capture_output=True, text=True, timeout=600)
        return result.stdout or "ℹ️ Nikto returned no output."
    except Exception as e:
        logger.error(f"Nikto scan failed: {e}")
        return f"⚠️ Nikto error: {e}"

def run_sqlmap_scan(url: str) -> str:
    try:
        result = subprocess.run(["sqlmap", "-u", url, "--batch", "--crawl=1"], capture_output=True, text=True, timeout=600)
        return result.stdout or "ℹ️ SQLMap returned no output."
    except Exception as e:
        logger.error(f"SQLMap scan failed: {e}")
        return f"⚠️ SQLMap error: {e}"

def run_all_deep_scanners(url: str) -> str:
    logger.info(f"🔬 Starting deep scans on {url}")
    results = {
        "Burp": run_burp_scan(url),
        "Wapiti": run_wapiti_scan(url),
        "Nikto": run_nikto_scan(url),
        "SQLMap": run_sqlmap_scan(url),
    }
    return "\n\n".join([f"## {tool} Output\n{output}" for tool, output in results.items()])

# For use in orchestrator
def run_deep_scans(url: str) -> str:
    return run_all_deep_scanners(url)
