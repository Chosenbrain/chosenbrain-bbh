import logging
import time
import random
from discord_webhook import DiscordWebhook, DiscordEmbed
from config import Config

__all__ = ["send_discord_notification"]

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

def send_discord_notification(
    target_url: str,
    severity: int,
    ai_assessment: str,
    details_url: str = None,
    max_retries: int = 3,
    username: str = DEFAULT_USERNAME,
    avatar_url: str = None,
    footer_text: str = "AI Security Alert"
) -> bool:
    """
    Sends a Discord notification about a vulnerability found.
    
    Args:
        target_url: The URL or domain being scanned.
        severity: Severity score or level.
        ai_assessment: AI's risk assessment label.
        details_url: Optional link to report.
        max_retries: Number of retry attempts.
        username: Bot name.
        avatar_url: Optional avatar.
        footer_text: Footer label.

    Returns:
        True if successful, False otherwise.
    """
    webhook_url = getattr(Config, 'DISCORD_WEBHOOK_URL', None)
    if not webhook_url:
        logger.error("Discord webhook URL is not configured.")
        return False

    # Map numeric severity to color
    try:
        severity_label = "CRITICAL" if severity >= 8 else "HIGH" if severity >= 6 else "MEDIUM" if severity >= 4 else "LOW"
        color = SEVERITY_COLOR_MAP.get(severity_label.upper(), 0x99AAB5)
    except Exception:
        color = 0x99AAB5

    title = f"🚨 Vulnerability Detected ({severity_label})"
    embed = DiscordEmbed(title=title, color=color)
    embed.add_embed_field(name="Target", value=target_url, inline=True)
    embed.add_embed_field(name="Severity Score", value=str(severity), inline=True)
    embed.add_embed_field(name="AI Assessment", value=ai_assessment, inline=False)
    if details_url:
        embed.add_embed_field(name="Details", value=f"[View Report]({details_url})", inline=False)
    embed.set_footer(text=footer_text)
    embed.set_timestamp()

    webhook = DiscordWebhook(url=webhook_url, username=username, avatar_url=avatar_url)
    webhook.add_embed(embed)

    for attempt in range(1, max_retries + 1):
        try:
            response = webhook.execute()
            status = getattr(response, 'status_code', None)
            if status and 200 <= status < 300:
                logger.info("Discord notification sent successfully.")
                return True
            logger.warning(f"Attempt {attempt} failed with status: {status}")
        except Exception as e:
            logger.exception(f"Attempt {attempt} exception while sending Discord notification: {e}")
        time.sleep((BACKOFF_BASE ** attempt) + random.uniform(0, MAX_JITTER))

    logger.error("All attempts to send Discord notification failed.")
    return False
