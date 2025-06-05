#!/bin/bash

echo "🔄 Starting Chosenbrain BBH full environment..."

# Create logs directory if not exists
mkdir -p logs

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check for BurpSuite JAR
if [ ! -f "burpsuite_pro_v2025.4.4.jar" ]; then
  echo "❌ Missing BurpSuite JAR: burpsuite_pro_v2025.4.4.jar"
  exit 1
fi

# Generate a new project file with timestamp to avoid lock conflicts
BURP_PROJECT_FILE="burp_project_$(date +%Y%m%d_%H%M%S).burp"

# Start AI Pipeline
echo "🚀 Starting AI Pipeline..."
nohup python3 chosenbrain_ai_pipeline.py > logs/pipeline.log 2>&1 &

# Start Telegram Bot
echo "📨 Starting Telegram Bot..."
nohup python3 telegram_bot.py > logs/telegram_bot.log 2>&1 &

# Start Flask Dashboard
echo "🖥️ Starting Flask Dashboard (app.py)..."
nohup python3 app.py > logs/flask.log 2>&1 &

# Launch BurpSuite
echo "🕷️ Launching BurpSuite (headless simulation)..."
nohup java -jar burpsuite_pro_v2025.4.4.jar \
  --project-file="$BURP_PROJECT_FILE" \
  --config-file=bbh_config.json > logs/burp.log 2>&1 &

nohup python3 status_tracker.py > logs/status_tracker.log 2>&1 &
nohup python3 watchdog.py > logs/watchdog.log 2>&1 &
# Optional tools (uncomment when needed)
# nohup python3 auto_submitter.py > logs/submitter.log 2>&1 &
# nohup python3 auto_trainer.py > logs/trainer.log 2>&1 &
# nohup python3 payload_injector.py > logs/payload.log 2>&1 &

echo "✅ All core services launched in background."
echo "📂 Logs saved in ./logs/, Burp project: $BURP_PROJECT_FILE"
