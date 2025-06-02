import logging
import json
from openai import OpenAI
from config import Config
from utils.retry_gpt import retry_gpt_call  

logger = logging.getLogger(__name__)

client = OpenAI(api_key=Config.OPENAI_API_KEY)

def discover_targets(count=1) -> dict:
    """
    GPT selects one valid program across HackerOne, Bugcrowd, Intigriti, or YesWeHack.
    Returns:
        {
            "platform": "bugcrowd",
            "program": "Tesla",
            "scope": "*.tesla.com",
            "url": "https://shop.tesla.com",
            "program_slug": "tesla"
        }
    """
    prompt = """
You are an expert bug bounty hunter. Pick ONE live program from any of these platforms:

- HackerOne
- Bugcrowd
- Intigriti
- YesWeHack

Respond in this EXACT JSON format:

{
  "platform": "bugcrowd",
  "program": "Tesla",
  "scope": "*.tesla.com",
  "url": "https://shop.tesla.com",
  "program_slug": "tesla"
}

Guidelines:
- Pick only programs that accept public submissions.
- Choose a safe, scan-ready domain inside scope (no login required).
- Keep `program_slug` as lowercase, hyphenated (e.g., tesla, united-airlines).
- Don’t hallucinate URLs — only use known safe subdomains of the scope.
"""

    try:
        response = retry_gpt_call(lambda: client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an OSINT and bug bounty automation AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        ))

        if not response:
            raise RuntimeError("GPT call failed after retries.")

        raw = response.choices[0].message.content.strip()
        target = json.loads(raw)
        logger.info(f"🎯 Target Selected: {target['program']} → {target['url']} [{target['platform']}]")
        return target

    except Exception as e:
        logger.exception("❌ Failed to get target from GPT.")
        return {}
        

def get_target_priority_score(target: dict) -> int:
    """
    Uses GPT to score a selected target from 1-10 based on payout potential, scope richness, popularity, and past bug volume.

    Args:
        target (dict): Target from `find_next_target()` with fields like platform, program, scope, url.

    Returns:
        int: Priority score between 1 and 10.
    """
    try:
        prompt = f"""
You are a bug bounty strategist. Score the following target from 1 to 10 based on:

- Payout potential
- Scope attractiveness
- Public accessibility of the URL
- Past bug volume on the platform
- Whether it’s known to be rewarding or efficient for researchers

Only return a single number from 1 (low priority) to 10 (very valuable):

Target:
Platform: {target['platform']}
Program: {target['program']}
Scope: {target['scope']}
URL: {target['url']}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert bug bounty program strategist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        text = response.choices[0].message.content.strip()
        import re
        match = re.search(r"\b([1-9]|10)\b", text)
        return int(match.group(1)) if match else 5  # Default fallback
    except Exception as e:
        logger.exception("❌ Failed to get target priority score.")
        return 5
