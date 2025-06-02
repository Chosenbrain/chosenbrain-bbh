
import subprocess
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

def run_nuclei_scan(url: str) -> str:
    """
    Scans a URL using Nuclei and returns raw results as text.

    Args:
        url (str): The target URL (e.g., https://example.com)

    Returns:
        str: Nuclei scan output or fallback message
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".txt") as tmp_in:
            tmp_in.write(url)
            tmp_in_path = tmp_in.name

        with tempfile.NamedTemporaryFile(delete=False, mode='r', suffix=".txt") as tmp_out:
            tmp_out_path = tmp_out.name

        logger.info(f"🔎 Scanning {url} with Nuclei...")

        # Adjust -t for template directory if needed, or remove to use default
        cmd = [
            "nuclei",
            "-l", tmp_in_path,
            "-o", tmp_out_path,
            "-severity", "medium,high,critical",
            "-nc",  # no color
            "-timeout", "30",
            "-c", "50"
        ]

        subprocess.run(cmd, timeout=1200, check=True) 

        with open(tmp_out_path, "r") as f:
            output = f.read().strip()

        os.remove(tmp_in_path)
        os.remove(tmp_out_path)

        return output if output else "No vulnerabilities found."

    except subprocess.CalledProcessError as e:
        logger.error(f"Nuclei scan failed: {e}")
        return "Scan failed: Nuclei process error."

    except Exception as e:
        logger.exception(f"Unexpected scan error: {e}")
        return "Scan failed: Unexpected error."
