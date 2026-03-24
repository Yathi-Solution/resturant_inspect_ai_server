"""Upload trained model to Hugging Face Hub."""

import os

from dotenv import load_dotenv
from huggingface_hub import HfApi, login

# Load environment variables
load_dotenv()

# Login with your token
print("🔐 Logging in to Hugging Face Hub...")
token = os.getenv("HF_TOKEN")
if not token:
    raise ValueError("HF_TOKEN not found in .env file")
login(token=token)
print("✅ Login successful!")

# Upload model
print("📤 Uploading model to dpratapx/restaurant-inspector...")
api = HfApi()
api.create_repo(
    repo_id="dpratapx/restaurant-inspector",
    repo_type="model",
    exist_ok=True,
    private=False,
)

api.upload_folder(
    folder_path="./model",
    repo_id="dpratapx/restaurant-inspector",
    repo_type="model",
)

print("✅ Model uploaded successfully!")
print("🔗 View at: https://huggingface.co/dpratapx/restaurant-inspector")
