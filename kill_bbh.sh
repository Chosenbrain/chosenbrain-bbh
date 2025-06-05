#!/bin/bash
echo "🔪 Killing all Chosenbrain BBH processes..."
pkill -f chosenbrain_ai_pipeline.py
pkill -f app.py
pkill -f telegram_bot.py
pkill -f burpsuite
echo "✅ All BBH-related processes terminated."
