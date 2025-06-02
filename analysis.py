import os
import re
import logging
import torch
from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from config import Config
import json

logger = logging.getLogger(__name__)
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Path to local fine‑tuned SecureBERT model
MODEL_DIR = os.getenv("SECUREBERT_MODEL_PATH", "./fine_tuned_securebert/final_model")

# Load tokenizer and model once at import time
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval()

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

LABEL_MAP = {
    0: "LOW_RISK",
    1: "MEDIUM_RISK",
    2: "HIGH_RISK",
}

def quick_ai_analysis(code_snippet: str) -> str:
    try:
        inputs = tokenizer(
            code_snippet,
            padding="max_length",
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = model(**inputs).logits
        pred_idx = logits.argmax(dim=-1).item()
        return LABEL_MAP.get(pred_idx, "UNKNOWN")
    except Exception as e:
        logger.exception(f"Error in quick_ai_analysis: {e}")
        return "ERROR"

def detailed_ai_analysis(file_content: str) -> str:
    prompt = f"""
You are a cybersecurity expert. Analyze the following code snippet for security risks and vulnerabilities.
Provide detailed explanations of threats, impact, and remediation.

Code:
```python
{file_content}
```"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.exception(f"Error in detailed_ai_analysis: {e}")
        return "Analysis failed."

def get_bounty_estimate(gpt_analysis: str) -> float | None:
    bounty_prompt = f"""
Based on the following security analysis, estimate the potential bug bounty value.
Provide a reward range in USD.

Security Analysis:
{gpt_analysis}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cybersecurity bounty expert."},
                {"role": "user", "content": bounty_prompt}
            ],
            temperature=0.7
        )
        text = resp.choices[0].message.content.strip()
        match = re.search(r"\$(\d+(?:,\d{3})*)", text)
        if match:
            return float(match.group(1).replace(",", ""))
        return None
    except Exception as e:
        logger.exception(f"Error in get_bounty_estimate: {e}")
        return None

def get_priority_score(gpt_analysis: str) -> int:
    priority_prompt = f"""
Assign a criticality score (1-10) to the following security analysis:

{gpt_analysis}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cybersecurity risk analyst."},
                {"role": "user", "content": priority_prompt}
            ],
            temperature=0.7
        )
        text = resp.choices[0].message.content.strip()
        match = re.search(r"\b([1-9]|10)\b", text)
        return int(match.group(1)) if match else 0
    except Exception as e:
        logger.exception(f"Error in get_priority_score: {e}")
        return 0

def batch_quick_ai_analysis(snippets: list[str]) -> list[str]:
    system_msg = {
        "role": "system",
        "content": (
            "You are a security triage assistant. "
            "For each code snippet I provide, respond with exactly one of "
            "`HIGH_RISK`, `MEDIUM_RISK`, or `LOW_RISK`. "
            "Return a JSON array of labels in the same order as the snippets."
        )
    }
    user_content = "\n\n".join(
        f"Snippet {i+1}:\n```{snip}```"
        for i, snip in enumerate(snippets)
    )
    user_msg = {"role": "user", "content": user_content}

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_msg, user_msg],
            temperature=0.0
        )
        labels = json.loads(resp.choices[0].message.content)
        return labels
    except Exception as e:
        logger.exception(f"Error in batch_quick_ai_analysis: {e}")
        return ["ERROR"] * len(snippets)
