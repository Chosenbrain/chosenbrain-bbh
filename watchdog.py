import os
import time
import subprocess
import logging
from datetime import datetime

# Optional: if you want to notify via Telegram when something restarts
# from telegram_bot import notify_telegram

# Configure logging
log_file = "logs/watchdog.log"
os.makedirs("logs", exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Define all services to monitor
services = {
    "chosenbrain_ai_pipeline.py": "python3 chosenbrain_ai_pipeline.py > logs/pipeline.log 2>&1 &",
    "telegram_bot.py": "python3 telegram_bot.py > logs/telegram_bot.log 2>&1 &",
    "app.py": "python3 app.py > logs/flask.log 2>&1 &",
    "burpsuite_pro_v2025.4.4.jar": "java -jar burpsuite_pro_v2025.4.4.jar --project-file=burp_project_watchdog_{}.burp --config-file=bbh_config.json > logs/burp.log 2>&1 &".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
}

def is_process_running(name):
    """Check if a process is running using `pgrep`."""
    try:
        subprocess.check_output(["pgrep", "-f", name])
        return True
    except subprocess.CalledProcessError:
        return False

def restart_service(name, command):
    """Restart the service with the given command."""
    logging.warning(f"Restarting {name}...")
    subprocess.call(command, shell=True)
    logging.info(f"{name} restarted.")
    # notify_telegram(f"⚠️ [Watchdog] Restarted {name} service.")

if __name__ == "__main__":
    logging.info("🔍 Watchdog started.")
    while True:
        for name, command in services.items():
            if not is_process_running(name):
                restart_service(name, command)
        time.sleep(30)  # Check every 30 seconds
