from platforms.hackerone import submit_to_hackerone
from platforms.bugcrowd import submit_to_bugcrowd
from platforms.intigriti import submit_to_intigriti
from platforms.yeswehack import submit_to_yeswehack

from openai import OpenAI
from config import Config
import logging

client = OpenAI(api_key=Config.OPENAI_API_KEY)
logger = logging.getLogger(__name__)

def generate_manual_submission_guide(report: dict, platform: str) -> str:
    """
    Use GPT to create a step-by-step guide to manually submit the report to the platform.
    """
    prompt = f"""
You are a bug bounty submission assistant.

Help the user submit the following bug report to the {platform.title()} platform.

Generate a clear step-by-step guide including:
- Where to log in
- What title to use
- How to fill in the description
- What to attach
- Any advice to avoid rejections

Bug Report:
Title: {report.get('title')}
Details:
{report.get('report')}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional bug bounty assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.exception("❌ Failed to generate manual submission guide.")
        return "⚠️ Manual submission guide generation failed."

def auto_submit(report: dict, platform: str):
    """
    Dispatches the AI-generated bug report to the correct platform-specific submission function,
    or generates a manual submission guide if not supported.
    """
    print(f"🚀 Submitting report to {platform.title()}...")

    try:
        if platform == "hackerone":
            return submit_to_hackerone(report)

        elif platform == "bugcrowd":
            # ❌ If this is not yet implemented, fallback to manual
            print("ℹ️ Auto-submission not supported for Bugcrowd. Generating manual guide...")
            return generate_manual_submission_guide(report, platform)

        elif platform == "intigriti":
            print("ℹ️ Auto-submission not supported for Intigriti. Generating manual guide...")
            return generate_manual_submission_guide(report, platform)

        elif platform == "yeswehack":
            print("ℹ️ Auto-submission not supported for YesWeHack. Generating manual guide...")
            return generate_manual_submission_guide(report, platform)

        else:
            raise ValueError(f"Unsupported platform: {platform}")

    except Exception as e:
        logger.exception(f"💥 Submission failed: {e}")
        return f"❌ Auto-submission failed. Reason: {e}\n\n{generate_manual_submission_guide(report, platform)}"

# -------------------------
# Manual test mode
# -------------------------
if __name__ == "__main__":
    example_report = {
        "title": "🔐 Stored XSS in comment field",
        "report": """Steps to Reproduce:
1. Login and go to `/comments`
2. Submit this: `<script>alert('xss')</script>`
3. Reload the page. XSS triggers.

Expected: Input should be sanitized.
Actual: Script is executed.

Impact: Stored XSS can be used to steal sessions or deface UI.
""",
        "program_slug": "example-program"
    }

    platform = "bugcrowd"  # Change as needed
    result = auto_submit(example_report, platform)
    print(f"✅ Result:\n{result}")
