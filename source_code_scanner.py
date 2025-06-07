import os
import shutil
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def clone_repo(git_url: str) -> str:
    """Clones a GitHub repo to a temp directory."""
    try:
        temp_dir = tempfile.mkdtemp()
        logger.info(f"📥 Cloning {git_url} to {temp_dir}")
        subprocess.run(["git", "clone", git_url, temp_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return temp_dir
    except Exception as e:
        logger.error(f"❌ Failed to clone repo: {e}")
        return None

def run_tool(command: list, label: str) -> str:
    """Runs a shell command and returns cleaned output."""
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
        output = result.stdout.strip()
        return f"## {label} Output\n{output or 'No issues found.'}"
    except Exception as e:
        return f"## {label} Output\nError running {label}: {str(e)}"

def scan_with_bandit(path: str) -> str:
    return run_tool(["bandit", "-r", path, "-q"], "Bandit")

def scan_with_semgrep(path: str) -> str:
    return run_tool(["semgrep", "--config", "auto", path], "Semgrep")

def scan_with_trufflehog(path: str) -> str:
    return run_tool(["trufflehog", "filesystem", "--no-update", path], "TruffleHog")

def scan_with_gitleaks(path: str) -> str:
    return run_tool(["gitleaks", "detect", "--source", path, "--no-banner"], "Gitleaks")

def scan_repo_for_vulns(git_url: str) -> str:
    """Main entry called by fetch_live_targets. Clones and scans a repo."""
    repo_path = clone_repo(git_url)
    if not repo_path:
        return "❌ Failed to clone repo."

    logger.info(f"🔍 Starting code scans for {git_url}")
    try:
        results = [
            scan_with_bandit(repo_path),
            scan_with_semgrep(repo_path),
            scan_with_trufflehog(repo_path),
            scan_with_gitleaks(repo_path)
        ]
        return "\n\n".join(results)
    finally:
        logger.info(f"🧹 Cleaning up {repo_path}")
        shutil.rmtree(repo_path, ignore_errors=True)

# Local test
if __name__ == "__main__":
    test_url = "https://github.com/django/django"
    report = scan_repo_for_vulns(test_url)
    print(report)
