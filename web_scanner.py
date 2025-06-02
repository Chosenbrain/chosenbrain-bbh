import logging
import requests
from analysis import detailed_ai_analysis, get_bounty_estimate, get_priority_score

logger = logging.getLogger(__name__)

# --------------------------
# Core web scanner interface
# --------------------------
def analyze_web_target(url: str) -> dict:
    """
    Perform vulnerability analysis on a live website.

    Args:
        url (str): The full URL to scan (e.g., https://target.com)

    Returns:
        dict: Result containing AI analysis, priority, and bounty estimate.
    """
    logger.info(f"🌐 Scanning target URL: {url}")
    result = {
        "target": url,
        "status": "OK",
        "gpt_analysis": None,
        "bounty_estimate": None,
        "priority_score": 0,
        "nuclei_results": None,
    }

    try:
        resp = requests.get(url, timeout=15)
        headers_text = "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
        ai_input = f"HTTP Response for {url}:\nStatus: {resp.status_code}\nHeaders:\n{headers_text}"

        gpt_report = detailed_ai_analysis(ai_input)
        bounty     = get_bounty_estimate(gpt_report)
        priority   = get_priority_score(gpt_report)

        result.update({
            "gpt_analysis": gpt_report,
            "bounty_estimate": bounty,
            "priority_score": priority,
        })

    except Exception as e:
        logger.exception(f"Failed to scan {url}: {e}")
        result["status"] = "error"

    return result
