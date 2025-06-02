import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🛡️ Adjust these paths based on your environment
BURP_JAR_PATH = "/path/to/burpsuite_pro.jar"         # Update this
BURP_CONFIG_PATH = "burp_config.json"                # Generated from Burp GUI
BURP_PROJECT_FILE = "scan.burp"                      # Temp project file

def run_burp_scan(url: str) -> str:
    import subprocess
    import json

    config_path = "/mnt/c/Users/chose/OneDrive/Desktop/Chosenbrain BBH/bbh_config.json"
    project_path = "/mnt/c/Users/chose/OneDrive/Desktop/Chosenbrain BBH/bbh_project.burp"
    jar_path = "/mnt/c/Users/chose/BurpSuitePro/burpsuite_pro_v2025.4.4.jar"

    # Step 1: Write config
    config = {
        "target": {
            "scope": {
                "include": [{"enabled": True, "protocol": "https", "host": url.replace("https://", "").replace("http://", ""), "port": 443}]
            }
        }
    }
    with open(config_path, "w") as f:
        json.dump(config, f)

    # Step 2: Launch Burp
    try:
        subprocess.Popen([
            "java", "-Djava.awt.headless=true", "-jar", jar_path,
            f"--project-file={project_path}",
            f"--config-file={config_path}"
        ])
        return f"✅ Launched Burp scan for {url}"
    except Exception as e:
        return f"❌ Failed to launch Burp: {e}"

def run_wapiti_scan(url: str) -> str:
    try:
        result = subprocess.run(["wapiti", "-u", url], capture_output=True, text=True, timeout=300)
        return result.stdout
    except Exception as e:
        logger.error(f"Wapiti scan failed: {e}")
        return f"⚠️ Wapiti scan error: {e}"

def run_nikto_scan(url: str) -> str:
    try:
        result = subprocess.run(["nikto", "-host", url], capture_output=True, text=True, timeout=300)
        return result.stdout
    except Exception as e:
        logger.error(f"Nikto scan failed: {e}")
        return f"⚠️ Nikto scan error: {e}"

def run_sqlmap_scan(url: str) -> str:
    try:
        result = subprocess.run(["sqlmap", "-u", url, "--batch", "--crawl=1"], capture_output=True, text=True, timeout=300)
        return result.stdout
    except Exception as e:
        logger.error(f"SQLMap scan failed: {e}")
        return f"⚠️ SQLMap scan error: {e}"

def run_all_deep_scanners(url: str) -> str:
    logger.info(f"🔬 Starting deep scans on {url}")
    results = {
        "Burp": run_burp_scan(url),
        "Wapiti": run_wapiti_scan(url),
        "Nikto": run_nikto_scan(url),
        "SQLMap": run_sqlmap_scan(url),
    }
    return "\n\n".join([f"## {tool} Output\n{output}" for tool, output in results.items()])

# This is the function imported in submission_orchestrator.py
def run_deep_scans(url: str) -> str:
    return run_all_deep_scanners(url)

