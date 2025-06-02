import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY                = os.getenv("SECRET_KEY", "your-secret-key")
    SQLALCHEMY_DATABASE_URI   = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://chosen:brain@localhost:5432/bugbounty"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERY_BROKER_URL         = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND     = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    TELEGRAM_BOT_TOKEN        = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID          = os.getenv("TELEGRAM_CHAT_ID")
    DISCORD_WEBHOOK_URL       = os.getenv("DISCORD_WEBHOOK_URL")

    OPENAI_API_KEY            = os.getenv("OPENAI_API_KEY")

    FLASK_APP                 = os.getenv("FLASK_APP", "app.py")
    FLASK_ENV                 = os.getenv("FLASK_ENV", "production")

    SECUREBERT_MODEL_PATH     = os.getenv(
        "SECUREBERT_MODEL_PATH",
        "./fine_tuned_securebert/final_model"
    )
