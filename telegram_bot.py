import os
import json
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from datetime import datetime, timedelta

load_dotenv()

# ENV
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
bug_tracker_path = "bug_tracker.json"
status_path = "status.json"
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# OpenAI Client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application object (shared with pipeline)
telegram_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# ---------- Loaders ----------
def load_bug_tracker():
    try:
        with open(bug_tracker_path, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "total_bugs_found": 0,
            "last_target": "None",
            "latest_bug": None,
            "last_updated": None
        }

def load_status_data():
    try:
        with open(status_path, "r") as f:
            return json.load(f)
    except Exception:
        return None

# ---------- Bug Reporter ----------
def send_bug_report(app, chat_id, bug):
    async def _send():
        text = (
            f"\ud83d\udea8 *New Bug Found & Reported!*\n\n"
            f"*Platform:* {bug['platform']}\n"
            f"*Target:* `{bug['target']}`\n"
            f"*Severity:* `{bug['severity']}`\n"
            f"*Estimated Bounty:* `${bug['bounty']}`\n\n"
            f"*Summary:* {bug['title']}\n\n"
            f"*Details:*\n{bug['description']}\n\n"
        )
        if bug.get("program_link"):
            text += f"[\ud83d\udd17 Submit/View Program]({bug['program_link']})"

        await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

    asyncio.run(_send())

# ---------- GPT Assistant ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text

    bug_tracker = load_bug_tracker()
    status_data = load_status_data()

    # Compose system prompt for GPT
    system_prompt = (
        "You are the assistant for Chosenbrain BBH, an autonomous bug bounty AI system.\n"
        "You know the current system status and bug tracker live from these two JSONs:\n"
        f"BUG TRACKER:\n{json.dumps(bug_tracker, indent=2)}\n\n"
        f"SYSTEM STATUS:\n{json.dumps(status_data, indent=2) if status_data else 'Unavailable'}\n\n"
        "You must answer all user questions as if you're monitoring and guiding the bug bounty hunt in real time."
    )

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    completion = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )
    response = completion.choices[0].message.content
    await update.message.reply_text(response, parse_mode='Markdown')

# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    await update.message.reply_text(
        "🧠 Welcome to *Chosenbrain BBH Assistant*\n"
        "💬 Ask me anything about bugs, live system status, or bounty progress.\n\n"
        "Created by *Chosen Abdullahi* and *Naim Rexhaj*.",
        parse_mode='Markdown'
    )

# ---------- Main Entrypoint ----------
def main():
    logger.info("✅ Telegram bot is running.")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    telegram_app.run_polling()

if __name__ == "__main__":
    main()
