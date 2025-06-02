import os
import json
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from datetime import datetime

load_dotenv()

# ENV
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
bug_tracker_path = "bug_tracker.json"
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# OpenAI Client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load bug tracker
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

# Format bug status
def get_bug_summary():
    data = load_bug_tracker()
    return (
        f"📊 *Bug Tracker Summary:*\n"
        f"• Total Bugs Found: `{data.get('total_bugs_found', 0)}`\n"
        f"• Last Target: `{data.get('last_target', 'N/A')}`\n"
        f"• Last Bug: `{data.get('latest_bug', 'N/A')}`\n"
        f"• Last Update: `{data.get('last_updated', 'N/A')}`"
    )

# Function for pipeline to call
def send_bug_report(app, chat_id, bug):
    async def _send():
        text = (
            f"🚨 *New Bug Submitted!*\n\n"
            f"*Title:* {bug['title']}\n"
            f"*Target:* {bug['target']}\n"
            f"*Severity:* {bug['severity']}\n"
            f"*Platform:* {bug['platform']}\n"
            f"*Estimated Bounty:* ${bug['bounty']}\n\n"
            f"*Details:* {bug['description']}"
        )
        await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    asyncio.run(_send())

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    await update.message.reply_text(
        "🧠 Welcome to *Chosenbrain BBH Assistant*.\n"
        "💬 Ask me anything about bugs, bounty submissions, or security.\n\n"
        "Created by *Chosen Abdullahi*, with his wise mentor and co-owner *Naim Rexhaj*.",
        parse_mode='Markdown'
    )

# Handle messages dynamically
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    bug_data = load_bug_tracker()

    if "creator" in message.lower():
        response = (
            "👨‍💻 I was built by *Chosen Abdullahi*, a brilliant cybersecurity innovator, "
            "with his father-like co-founder *Naim Rexhaj*. Together, they crafted this AI to hunt bugs like no other."
        )
    elif "any bug" in message.lower() or "found bugs" in message.lower():
        response = get_bug_summary()
    elif "status" in message.lower():
        response = get_bug_summary()
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
        completion = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You're the assistant for Chosenbrain BBH, a bug bounty automation system. "
                    "Respond with insights and updates based only on the internal bug tracker and live scan state."
                )},
                {"role": "user", "content": message}
            ]
        )
        response = completion.choices[0].message.content

    await update.message.reply_text(response, parse_mode='Markdown')

# Expose the app for pipeline use
telegram_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

def main():
    logger.info("✅ Telegram bot is running.")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    telegram_app.run_polling()

if __name__ == "__main__":
    main()
