# 🛡️ ChosenBrain BBH — Autonomous AI-Powered Bug Bounty Hunter

**ChosenBrain BBH** is a fully autonomous, multi-platform, AI-augmented bug bounty hunter that discovers real vulnerabilities, performs deep analysis, and auto-submits to platforms like HackerOne, Bugcrowd, Intigriti, and YesWeHack.

## 🔥 Features

- 🧠 **AI-Powered Analysis**: Uses GPT-4 for deep vulnerability insights, risk classification, and report generation.
- 📡 **Live Target Fetching**: Automatically fetches and rotates bounty programs from HackerOne, Intigriti, Bugcrowd, and YesWeHack.
- 🌐 **Reconnaissance Engine**:
  - Shodan + Google Dorking
  - Subfinder, Hakrawler, Arjun integration
- 🔎 **Deep Scanning**:
  - Burp Suite API
  - Nuclei, Nikto, Wapiti, SQLMap
  - Custom payload injection
- 🗂️ **Source Code Audits**:
  - Downloads & scans GitHub repos attached to bounty programs
  - Scans with Bandit, Semgrep, TruffleHog, Gitleaks
- 🤖 **Telegram Integration**:
  - Live bug reporting, status tracking, and full ChatGPT-style Q&A via bot
- 🚨 **Alerts & Dashboards**:
  - JSON bug tracker
  - Status file
  - Discord & Telegram notifications
- 💣 **Full Loop Automation**:
  - Fetch → Recon → Scan → Analyze → Report → Submit → Log
  - Skips duplicate bugs with fingerprint memory
- ⏱️ **Autonomous Multi-Day Hunt Mode**:
  - Runs indefinitely, rotating across platforms and targets

---

## ⚙️ Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/Chosenbrain/chosenbrain-bbh.git
   cd chosenbrain-bbh
Install requirements

bash
Copy
Edit
pip install -r requirements.txt
Set environment variables
Create a .env file with:

env
Copy
Edit
OPENAI_API_KEY=your_openai_key
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
HACKERONE_USERNAME=your_username
HACKERONE_API_TOKEN=your_api_token
INTIGRITI_API_TOKEN=your_token
SHODAN_API_KEY=your_shodan_key
BURP_API_KEY=your_burp_api_key
Start the pipeline

bash
Copy
Edit
python chosenbrain_ai_pipeline.py
(Optional) Start the Telegram bot

bash
Copy
Edit
python telegram_bot.py
📁 Key Files
File	Description
chosenbrain_ai_pipeline.py	Main AI loop engine
fetch_live_targets.py	Live target fetcher
recon_engine.py	Recon via Shodan, Google, Subfinder, etc.
deep_scanner.py	Vulnerability scanners
source_code_scanner.py	GitHub repo audit system
auto_submitter.py	Auto submission to bounty platforms
telegram_bot.py	Telegram interface
dashboard_tracker.py	Logs and tracks reports

🧠 Project Vision
This project is designed to simulate a real autonomous bug bounty hunter — one that can run for weeks or months unattended, continuously learning, discovering targets, scanning, and submitting vulnerabilities intelligently using AI.

📜 License
MIT License — Free to use, modify, and deploy. Credit appreciated.

👤 Maintained by
Chosen Abdullahi
🔗 chosenbrain.com
💬 Telegram: @Masterkendra

yaml
Copy
Edit

---

Would you like me to:
- Save this as a `README.md` file locally?
- Automatically commit and push it to your GitHub repo?







