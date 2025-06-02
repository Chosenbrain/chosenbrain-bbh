
import os
import logging
from datetime import datetime
from models import Report
from extensions import db
from transformers import TrainingArguments, Trainer
from datasets import Dataset
from config import Config
from train_model import tokenizer, model
import torch

logger = logging.getLogger(__name__)

AUTO_TRAIN_PATH = "train_auto.csv"
MODEL_OUTPUT_PATH = Config.SECUREBERT_MODEL_PATH


def collect_training_data():
    logger.info("🔄 Collecting confirmed bugs for retraining...")
    confirmed = Report.query.filter_by(status="Confirmed").all()
    if not confirmed:
        logger.warning("⚠️ No confirmed bugs found. Skipping retraining.")
        return None

    rows = []
    for r in confirmed:
        label = 2  # Assume confirmed reports are HIGH_RISK
        rows.append({"text": r.scan_results[:500], "label": label})

    return Dataset.from_list(rows)


def tokenize_dataset(dataset):
    def tokenize(example):
        return tokenizer(
            example["text"],
            padding="max_length",
            truncation=True,
            max_length=512
        )
    return dataset.map(tokenize)


def run_retraining():
    dataset = collect_training_data()
    if not dataset:
        return

    tokenized = tokenize_dataset(dataset)

    training_args = TrainingArguments(
        output_dir="./temp_retrain",
        per_device_train_batch_size=4,
        num_train_epochs=2,
        logging_steps=10,
        save_strategy="no",
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized
    )

    logger.info("🚀 Starting model fine-tuning...")
    trainer.train()
    model.save_pretrained(MODEL_OUTPUT_PATH)
    tokenizer.save_pretrained(MODEL_OUTPUT_PATH)
    logger.info(f"✅ Model retrained and saved to {MODEL_OUTPUT_PATH}")


# Optional: call this manually or hook to a schedule / button
if __name__ == "__main__":
    run_retraining()
