import logging
import time
import random
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from config import Config

logger = logging.getLogger(__name__)

SEVERITY_COLOR_MAP = {
    "LOW": 0x2ECC71,
    "MEDIUM": 0xE67E22,
    "HIGH": 0xE74C3C,
    "CRITICAL": 0xC0392B,
}

DEFAULT_USERNAME = "Chosenbrain BBH"
DEFAULT_TIMEOUT = 10
BACKOFF_BASE = 2
MAX_JITTER = 0.5

def alert(
    message: str = None,
    severity: int = 5,
    level: str = "info",
    platform: str = "Unknown",
    program_name: str = "Unknown",
    target_url: str = "Unknown",
    bounty: str = "Undisclosed",
    ai_assessment: str = "Unclassified",
    details_url: str = None,
    repro_steps: str = None,
    submission_note: str = None,
    tool_used: str = "Multiple Tools"
):
    """
    Unified alert dispatcher to both Discord and Telegram.
    Sends formatted messages about detected vulnerabilities.
    """
    formatted_message = _format_message(
        message, platform, program_name, target_url, severity,
        ai_assessment, bounty, repro_steps, submission_note,
        details_url, tool_used
    )
    _send_discord(formatted_message, severity)
    _send_telegram(formatted_message, level)

def _format_message(
    message, platform, program_name, target_url, severity,
    ai_assessment, bounty, repro_steps, submission_note,
    details_url, tool_used
):
    base = f"🚨 *New Vulnerability Alert* 🚨\n"
    base += f"*Platform:* `{platform}`\n"
    base += f"*Program:* `{program_name}`\n"
    base += f"*Target:* `{target_url}`\n"
    base += f"*Severity:* `{severity}`\n"
    base += f"*Risk Level:* `{ai_assessment}`\n"
    base += f"*Bounty Estimate:* `{bounty}`\n"
    base += f"*Tool Used:* `{tool_used}`\n"
    if message:
        base += f"\n*Summary:* {message.strip()}\n"
    if repro_steps:
        base += f"\n*Steps to Reproduce:*\n{repro_steps.strip()}\n"
    if submission_note:
        base += f"\n*Submission Guide:*\n{submission_note.strip()}\n"
    if details_url:
        base += f"\n[🔗 View Full Report]({details_url})"
    return base

def _send_discord(formatted_msg: str, severity: int):
    webhook_url = getattr(Config, 'DISCORD_WEBHOOK_URL', None)
    if not webhook_url:
        logger.warning("⚠️ Discord webhook URL not configured.")
        return

    severity_label = "CRITICAL" if severity >= 8 else "HIGH" if severity >= 6 else "MEDIUM" if severity >= 4 else "LOW"
    color = SEVERITY_COLOR_MAP.get(severity_label.upper(), 0x99AAB5)

    embed = DiscordEmbed(title=f"🚨 Vulnerability Detected ({severity_label})", description=formatted_msg, color=color)
    embed.set_footer(text="AI Security Alert")
    embed.set_timestamp()

    webhook = DiscordWebhook(url=webhook_url, username=DEFAULT_USERNAME)
    webhook.add_embed(embed)

    for attempt in range(1, 4):
        try:
            response = webhook.execute()
            status = getattr(response, 'status_code', None)
            if status and 200 <= status < 300:
                logger.info("✅ Discord alert sent successfully.")
                return
            logger.warning(f"⚠️ Attempt {attempt} failed with status: {status}")
        except Exception as e:
            logger.exception(f"❌ Attempt {attempt} failed: {e}")
        time.sleep((BACKOFF_BASE ** attempt) + random.uniform(0, MAX_JITTER))

def _send_telegram(formatted_msg: str, level: str):
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram bot token or chat ID not configured.")
        return

    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": Config.TELEGRAM_CHAT_ID,
            "text": formatted_msg,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.ok:
            logger.info("✅ Telegram alert sent.")
        else:
            logger.warning(f"⚠️ Telegram alert failed: {response.text}")
    except Exception as e:
        logger.exception(f"❌ Telegram alert exception: {e}")


def send_bug_report(bot, chat_id, report_data):
    message = f"🚨 *{report_data.get('title', 'New Bug Found')}* 🚨\n"
    message += f"*Target:* `{report_data.get('target', 'N/A')}`\n"
    message += f"*Severity:* `{report_data.get('severity', 'Unknown')}`\n"
    message += f"*Platform:* `{report_data.get('platform', 'Unknown')}`\n"
    message += f"*Bounty:* `{report_data.get('bounty', 'Undisclosed')}`\n"
    message += f"*Description:* {report_data.get('description', '')}\n"
    if report_data.get("program_link"):
        message += f"[🔗 View Program]({report_data['program_link']})"

    try:
        bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
