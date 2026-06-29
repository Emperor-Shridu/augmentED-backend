#!/usr/bin/env python
from huggingface_hub import hf_hub_download
import os

model_dir = os.path.join(os.path.dirname(__file__), "chatbot", "models")
os.makedirs(model_dir, exist_ok=True)

print("Downloading zephyr-7b-beta-Q2_K.gguf (~3.3 GB)...")
print("This may take a few minutes depending on your connection speed.\n")

try:
    file_path = hf_hub_download(
        repo_id="DhruvalLabs/zephyr-7b-beta-GGUF",
        filename="zephyr-7b-beta-Q2_K.gguf",
        local_dir=model_dir,
        local_dir_use_symlinks=False
    )
    print(f"\n✓ Download complete!")
    print(f"Model saved to: {file_path}")
except Exception as e:
    print(f"\n✗ Download failed: {e}")
    print("Try downloading manually from:")
    print("https://huggingface.co/DhruvalLabs/zephyr-7b-beta-GGUF/blob/main/zephyr-7b-beta-Q2_K.gguf")
