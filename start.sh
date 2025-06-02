#!/bin/bash

echo "🔄 Starting Chosenbrain BBH full environment..."

# Ensure log directory exists
mkdir -p logs

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Validate key scripts
REQUIRED_FILES=("chosenbrain_ai_pipeline.py" "telegram_bot.py" "app.py" "burpsuite_pro_v2025.4.4.jar")
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

# Start the AI pipeline
echo "🚀 Starting AI Pipeline..."
nohup python3 chosenbrain_ai_pipeline.py > logs/pipeline.log 2>&1 &

# Start the Telegram Bot
echo "📨 Starting Telegram Bot..."
nohup python3 telegram_bot.py > logs/telegram_bot.log 2>&1 &

# Start Flask Dashboard
echo "🖥️ Starting Flask Dashboard (app.py)..."
nohup flask run --host=0.0.0.0 --port=5000 > logs/flask.log 2>&1 &

# Start Burp Suite (ensure GUI or X forwarding is supported in VPS if used)
echo "🕷️ Launching BurpSuite (GUI)..."
nohup java -jar burpsuite_pro_v2025.4.4.jar > logs/burpsuite.log 2>&1 &

# Optional tools — Uncomment if needed
# echo "⚡ Starting Nuclei Scanner..."
# nohup python3 nuclei_scanner.py > logs/nuclei.log 2>&1 &

# echo "🔍 Starting Deep Scanner..."
# nohup python3 deep_scanner.py > logs/deep_scanner.log 2>&1 &

# echo "🌐 Starting Web Scanner..."
# nohup python3 web_scanner.py > logs/web_scanner.log 2>&1 &

# echo "💉 Starting Payload Injector..."
# nohup python3 payload_injector.py > logs/payload.log 2>&1 &

# echo "📬 Starting Auto Submitter..."
# nohup python3 auto_submitter.py > logs/submitter.log 2>&1 &

# echo "🤖 Starting Auto Trainer..."
# nohup python3 auto_trainer.py > logs/trainer.log 2>&1 &

echo "✅ All core services launched in background."
echo "📂 Check individual logs inside the logs/ directory for output."
