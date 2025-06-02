import time
import logging
from openai import OpenAIError

logger = logging.getLogger(__name__)

def retry_gpt_call(func, max_retries=5, delay=5, backoff=2):
    """
    Retry OpenAI GPT calls with exponential backoff.
    Usage:
        response = retry_gpt_call(lambda: openai.chat.completions.create(...))
    """
    for attempt in range(max_retries):
        try:
            return func()
        except OpenAIError as e:
            wait = delay * (backoff ** attempt)
            logger.warning(f"🔁 GPT call failed (attempt {attempt+1}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
        except Exception as e:
            logger.exception("Unexpected GPT error.")
            break
    return None