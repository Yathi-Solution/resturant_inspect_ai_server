#!/usr/bin/env python
"""
Train DistilBERT on approved review annotations.

Trains a multi-label aspect classifier on approved RestaurantInspector annotations.
Evaluates on held-out validation set and logs metrics to training_runs table.

Aspects: food, service, hygiene, parking, cleanliness
Labels: positive, negative, mixed, not_mentioned (4-state)
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

from app.db.enums import AnnotationStatus, AspectState
from app.db.models import ReviewAnnotation, TrainingRun
from app.db.session import SessionLocal


def load_approved_annotations():
    """Load approved annotations from database."""
    session = SessionLocal()
    try:
        records = (
            session.query(ReviewAnnotation)
            .filter_by(annotation_status=AnnotationStatus.APPROVED)
            .all()
        )
        data = []
        for ann in records:
            review_text = ann.review.review_text
            aspects = {
                "food": ann.food_state.value,
                "service": ann.service_state.value,
                "hygiene": ann.hygiene_state.value,
                "parking": ann.parking_state.value,
                "cleanliness": ann.cleanliness_state.value,
            }
            data.append({"text": review_text, "aspects": aspects})
        return data
    finally:
        session.close()


def aspect_to_labels(aspect, state_value):
    """Convert aspect state to binary labels (positive, negative, mixed)."""
    labels = []
    if state_value == AspectState.POSITIVE.value:
        labels.append(f"{aspect}_positive")
    elif state_value == AspectState.NEGATIVE.value:
        labels.append(f"{aspect}_negative")
    elif state_value == AspectState.MIXED.value:
        labels.append(f"{aspect}_positive")
        labels.append(f"{aspect}_negative")
    # not_mentioned = no labels
    return labels


def prepare_dataset(data, val_ratio=0.2, test_ratio=0.2):
    """Prepare train/val/test splits with multi-label format."""
    texts = [d["text"] for d in data]
    all_labels = []
    for d in data:
        labels = []
        for aspect, state in d["aspects"].items():
            labels.extend(aspect_to_labels(aspect, state))
        all_labels.append(labels)

    # Split: 60% train, 20% val, 20% test
    temp_ratio = val_ratio + test_ratio
    X_train, X_temp, y_train, y_temp = train_test_split(
        texts, all_labels, test_size=temp_ratio, random_state=42
    )
    # Split temp set into val/test according to ratios
    temp_test_size = test_ratio / temp_ratio
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=temp_test_size, random_state=42
    )

    # Fit on full label space so unseen labels in train don't get dropped.
    all_possible_labels = []
    for aspect in ["food", "service", "hygiene", "parking", "cleanliness"]:
        all_possible_labels.append(f"{aspect}_positive")
        all_possible_labels.append(f"{aspect}_negative")

    mlb = MultiLabelBinarizer()
    mlb.fit([all_possible_labels])
    y_train_encoded = mlb.transform(y_train)
    y_val_encoded = mlb.transform(y_val)
    y_test_encoded = mlb.transform(y_test)

    return (
        (X_train, y_train_encoded),
        (X_val, y_val_encoded),
        (X_test, y_test_encoded),
        mlb.classes_,
    )


class AspectDataset(torch.utils.data.Dataset):
    """PyTorch dataset for multi-label aspect classification."""

    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.float),
        }


def compute_metrics(eval_pred, threshold=0.5):
    """Compute multi-label metrics (accuracy, precision, recall, F1)."""
    logits, labels = eval_pred
    probs = 1.0 / (1.0 + np.exp(-logits))
    predictions = (probs > threshold).astype(int)

    # Exact match accuracy
    accuracy = np.mean(np.all(predictions == labels, axis=1))

    # Per-label metrics
    from sklearn.metrics import f1_score, precision_score, recall_score

    precision = precision_score(labels, predictions, average="micro", zero_division=0)
    recall = recall_score(labels, predictions, average="micro", zero_division=0)
    f1 = f1_score(labels, predictions, average="micro", zero_division=0)

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def tune_threshold(val_logits, val_labels):
    """Pick threshold that maximizes micro F1 on validation set."""
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in np.arange(0.1, 0.91, 0.05):
        metrics = compute_metrics((val_logits, val_labels), threshold=float(threshold))
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_threshold = float(threshold)
    return best_threshold


def train_model(model_name="distilbert-base-uncased", output_dir="models/aspect-classifier"):
    """Main training pipeline."""
    print("=" * 60)
    print("Loading approved annotations...")
    data = load_approved_annotations()
    print(f"  Loaded {len(data)} approved annotations")

    print("\nPreparing dataset...")
    (X_train, y_train), (X_val, y_val), (X_test, y_test), label_names = prepare_dataset(data)
    print(f"  Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    print(f"  Label count: {len(label_names)}")

    print(f"\nLoading {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=len(label_names), problem_type="multi_label_classification"
    )

    train_dataset = AspectDataset(X_train, y_train, tokenizer)
    val_dataset = AspectDataset(X_val, y_val, tokenizer)
    test_dataset = AspectDataset(X_test, y_test, tokenizer)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir="logs",
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print("\nTraining model...")
    trainer.train()

    print("\nTuning threshold on validation set...")
    val_predictions = trainer.predict(val_dataset)
    best_threshold = tune_threshold(val_predictions.predictions, val_predictions.label_ids)
    print(f"  Best threshold: {best_threshold:.2f}")

    print("\nEvaluating on test set...")
    test_predictions = trainer.predict(test_dataset)
    test_metrics = compute_metrics(
        (test_predictions.predictions, test_predictions.label_ids),
        threshold=best_threshold,
    )

    # Save model and metadata
    print(f"\nSaving model to {output_dir}...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    metadata = {
        "model_name": model_name,
        "num_labels": len(label_names),
        "label_names": list(label_names),
        "training_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "hidden_size": model.config.hidden_size,
        "threshold": best_threshold,
        "test_metrics": test_metrics,
    }

    metadata_path = Path(output_dir) / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Threshold:     {best_threshold:.2f}")
    print(f"Test Accuracy: {test_metrics.get('accuracy', 0):.4f}")
    print(f"Test F1:       {test_metrics.get('f1', 0):.4f}")
    print(f"Test Precision: {test_metrics.get('precision', 0):.4f}")
    print(f"Test Recall:   {test_metrics.get('recall', 0):.4f}")
    print(f"\nModel saved to: {output_dir}")

    # Log to training_runs table
    log_training_run(
        model_name=model_name,
        training_samples=len(X_train),
        test_accuracy=test_metrics.get("accuracy", 0),
        test_f1=test_metrics.get("f1", 0),
        test_precision=test_metrics.get("precision", 0),
        test_recall=test_metrics.get("recall", 0),
        output_path=output_dir,
    )


def log_training_run(
    model_name, training_samples, test_accuracy, test_f1, test_precision, test_recall, output_path
):
    """Log training run to database."""
    session = SessionLocal()
    try:
        run = TrainingRun(
            model_name=model_name,
            training_samples=training_samples,
            test_accuracy=float(test_accuracy),
            test_f1=float(test_f1),
            test_precision=float(test_precision),
            test_recall=float(test_recall),
            output_path=str(output_path),
            trained_at=datetime.now(timezone.utc),
        )
        session.add(run)
        session.commit()
        print(f"Logged training run to database (ID: {run.id})")
    except Exception as e:
        print(f"Warning: Could not log training run: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train aspect classifier on approved annotations")
    parser.add_argument(
        "--model",
        type=str,
        default="distilbert-base-uncased",
        help="HF model name (default: distilbert-base-uncased)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/aspect-classifier",
        help="Output directory for trained model",
    )

    args = parser.parse_args()
    train_model(model_name=args.model, output_dir=args.output_dir)
