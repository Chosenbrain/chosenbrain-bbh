from datetime import datetime

def generate_bug_report(gpt_analysis: str, url: str) -> dict:
    """
    Formats a complete bug report from GPT output and scan metadata.

    Args:
        gpt_analysis (str): The full vulnerability analysis text from GPT.
        url (str): The URL that was scanned.

    Returns:
        dict: Structured bug report with title, body, and optional metadata.
    """
    lines = gpt_analysis.strip().splitlines()
    title_line = next((line for line in lines if line.strip()), "Untitled Bug")
    title = title_line.strip()[:100]  # Truncate to 100 chars if needed

    # Clean report body
    body = "\n".join(lines).strip()
    timestamp = datetime.utcnow().isoformat()

    return {
        "title": title,
        "report": f"""
URL Scanned: {url}
Date: {timestamp}

GPT-4 Security Analysis:
{body}
""".strip()
    }

def summarize_bug(bug):
    return (
        f"🔸 Vulnerability: {bug['attack']}\n"
        f"🌐 URL: {bug['url']}\n"
        f"🧪 Payload: `{bug['payload']}`\n"
        f"📝 Description: {bug.get('description', 'N/A')}"
    )
