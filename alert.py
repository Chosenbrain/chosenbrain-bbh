import logging
import requests
from config import Config
from notifications import send_discord_notification

logger = logging.getLogger(__name__)

def alert(
    message: str = None,
    severity: int = 5,
    level: str = "info",
    target_url: str = "Unknown",
    ai_assessment: str = "Unclassified",
    details_url: str = None,
    submission_note: str = None,
    repro_steps: str = None,
    platform_hint: str = None
):
    """
    Unified alert dispatcher to both Discord and Telegram.
    Provides expanded info when a vulnerability is found.
    """
    full_msg = _format_message(
        message, target_url, ai_assessment, repro_steps, submission_note, platform_hint
    )
    _send_discord(severity, target_url, ai_assessment, details_url)
    _send_telegram(full_msg, level)

def _format_message(message, target_url, ai_assessment, repro_steps, submission_note, platform_hint):
    base = f"**Vulnerability Detected**\n"
    base += f"Target: `{target_url}`\n"
    base += f"Risk: `{ai_assessment}`\n"
    if message:
        base += f"\n**Summary:** {message.strip()}\n"
    if repro_steps:
        base += f"\n**Steps to Reproduce:**\n{repro_steps.strip()}\n"
    if submission_note:
        base += f"\n**Report Template:**\n{submission_note.strip()}\n"
    if platform_hint:
        base += f"\n**Submission Tip:** {platform_hint.strip()}\n"
    return base

def _send_discord(severity: int, target_url: str, ai_assessment: str, details_url: str = None):
    if not Config.DISCORD_WEBHOOK_URL:
        logger.warning("⚠️ Discord webhook URL not configured.")
        return

    try:
        success = send_discord_notification(
            target_url=target_url,
            severity=severity,
            ai_assessment=ai_assessment,
            details_url=details_url
        )
        if success:
            logger.info("✅ Discord alert sent.")
        else:
            logger.warning("⚠️ Discord alert failed.")
    except Exception as e:
        logger.exception(f"❌ Discord alert exception: {e}")

def _send_telegram(formatted_msg: str, level: str):
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram bot token or chat ID not configured.")
        return

    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": Config.TELEGRAM_CHAT_ID,
            "text": f"🚨 *{level.upper()} ALERT:*\n\n{formatted_msg}",
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.ok:
            logger.info("✅ Telegram alert sent.")
        else:
            logger.warning(f"⚠️ Telegram alert failed: {response.text}")
    except Exception as e:
        logger.exception(f"❌ Telegram alert exception: {e}")
