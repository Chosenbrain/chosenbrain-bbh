import subprocess
import os
import tempfile
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

TEMPLATE_DIR = "/root/nuclei-templates"  # Make sure this path is valid and up to date

def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"] and parsed.netloc
    except:
        return False

def run_nuclei_scan(url: str) -> str:
    """
    Scans a URL using Nuclei and returns raw results as text.
    """
    if not is_valid_url(url):
        logger.warning(f"❌ Skipping invalid URL for Nuclei scan: {url}")
        return "Skipped invalid URL."

    try:
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".txt") as tmp_in:
            tmp_in.write(url)
            tmp_in_path = tmp_in.name

        with tempfile.NamedTemporaryFile(delete=False, mode='r', suffix=".txt") as tmp_out:
            tmp_out_path = tmp_out.name

        logger.info(f"🔎 Scanning {url} with Nuclei...")

        cmd = [
            "nuclei",
            "-l", tmp_in_path,
            "-o", tmp_out_path,
            "-t", TEMPLATE_DIR,
            "-severity", "medium,high,critical",
            "-nc",
            "-timeout", "30",
            "-c", "50"
        ]

        result = subprocess.run(cmd, timeout=1200, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"Nuclei scan failed: {result.stderr}")
            return "Scan failed: Nuclei execution error."

        with open(tmp_out_path, "r") as f:
            output = f.read().strip()

        return output if output else "No vulnerabilities found."

    except FileNotFoundError:
        logger.error("❌ Nuclei is not installed or not in PATH.")
        return "Scan failed: Nuclei not installed."

    except subprocess.TimeoutExpired:
        logger.error("⏳ Nuclei scan timed out.")
        return "Scan failed: Timeout."

    except Exception as e:
        logger.exception(f"Unexpected error during Nuclei scan: {e}")
        return "Scan failed: Unexpected error."

    finally:
        try:
            if os.path.exists(tmp_in_path):
                os.remove(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.remove(tmp_out_path)
        except Exception as cleanup_err:
            logger.warning(f"⚠️ Failed to delete temp files: {cleanup_err}")
