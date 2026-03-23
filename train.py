"""
Training script for Restaurant Aspect Classifier.
Fine-tunes DistilBERT on Yelp reviews with rule-based aspect labeling.
"""

from datasets import load_dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

# Aspect categories
ASPECTS = ["FOOD", "SERVICE", "HYGIENE", "PARKING", "CLEANLINESS"]


def label_aspects(text: str, label: int) -> list[float]:
    """
    Create aspect labels from review text and overall sentiment.

    Args:
        text: Review text
        label: Overall sentiment (0=negative, 1=positive)

    Returns:
        List of 5 scores (0.0-1.0) for each aspect
    """
    base_score = float(label)
    scores = [base_score] * 5  # Initialize all aspects with base score
    text_lower = text.lower()

    # HYGIENE (index 2)
    if any(word in text_lower for word in ["dirty", "filthy", "gross", "disgusting"]):
        scores[2] = 0.0
    elif any(word in text_lower for word in ["clean", "spotless", "sanitary"]):
        scores[2] = 1.0

    # FOOD (index 0)
    if any(word in text_lower for word in ["delicious", "tasty", "amazing", "excellent"]):
        scores[0] = 1.0
    elif any(word in text_lower for word in ["terrible", "awful", "bland", "disgusting"]):
        scores[0] = 0.0

    # SERVICE (index 1)
    if any(word in text_lower for word in ["friendly", "attentive", "helpful", "great service"]):
        scores[1] = 1.0
    elif any(word in text_lower for word in ["rude", "slow", "terrible service", "unfriendly"]):
        scores[1] = 0.0

    # PARKING (index 3)
    if "parking" in text_lower:
        if label == 0 or any(word in text_lower for word in ["no parking", "parking nightmare"]):
            scores[3] = 0.0
        else:
            scores[3] = 1.0

    # CLEANLINESS (index 4) - similar to hygiene
    if any(word in text_lower for word in ["dirty", "messy", "unkempt"]):
        scores[4] = 0.0
    elif any(word in text_lower for word in ["clean", "tidy", "well-maintained"]):
        scores[4] = 1.0

    return scores


def main():
    """Train the model."""
    print("🚀 Starting Restaurant Aspect Classifier Training\n")

    # Load dataset
    print("📥 Loading Yelp dataset (1500 samples)...")
    dataset = load_dataset("yelp_polarity", split="train[:1500]", trust_remote_code=True)
    print(f"✅ Loaded {len(dataset)} reviews\n")

    # Create aspect labels
    print("🏷️  Creating aspect labels from reviews...")
    dataset = dataset.map(
        lambda x: {"aspects": label_aspects(x["text"], x["label"])},
        desc="Labeling aspects",
    )
    print("✅ Aspect labels created\n")

    # Load tokenizer and model
    print("🤖 Loading DistilBERT model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=5,
        problem_type="multi_label_classification",
    )
    print("✅ Model loaded\n")

    # Tokenize dataset
    print("✂️  Tokenizing text...")

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=256,
        )

    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        desc="Tokenizing",
    )

    # Prepare dataset for training
    tokenized_dataset = tokenized_dataset.rename_column("aspects", "labels")
    tokenized_dataset.set_format(
        type="torch",
        columns=["input_ids", "attention_mask", "labels"],
    )
    print("✅ Tokenization complete\n")

    # Training arguments
    training_args = TrainingArguments(
        output_dir="./model",
        num_train_epochs=2,
        per_device_train_batch_size=8,
        warmup_steps=50,
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=1,
        report_to="none",
        push_to_hub=False,
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )

    # Train
    print("🎯 Training model (this will take ~45 minutes)...\n")
    trainer.train()
    print("\n✅ Training complete!\n")

    # Save model
    print("💾 Saving model and tokenizer...")
    model.save_pretrained("./model")
    tokenizer.save_pretrained("./model")
    print("✅ Model saved to ./model/\n")

    print("🎉 Training complete! You can now run: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
