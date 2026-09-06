#!/usr/bin/env python3
"""
MediKiosk — AI4Bharat IndicTrans2 Local Model Downloader
Downloads quantized CTranslate2 weights or Hugging Face checkpoints for offline Indic translation.

Usage:
    python scripts/download_indictrans2.py [--engine ct2|hf] [--target-dir ./models/indictrans2]
"""

import os
import sys
import argparse
import subprocess

def download_ctranslate2_weights(target_dir: str):
    """
    Downloads lightweight, quantized CTranslate2 IndicTrans2 models from Hugging Face.
    """
    print(f"[*] Preparing target directory: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)

    print("[*] Downloading AI4Bharat IndicTrans2 (Quantized int8 for fast CPU/GPU inference)...")
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id="ai4bharat/indictrans2-en-indic-1B",
            local_dir=target_dir,
            ignore_patterns=["*.git*", "*.safetensors", "*.bin"] if False else None
        )
        print(f"[✓] Model weights successfully downloaded to: {target_dir}")
    except ImportError:
        print("[!] huggingface_hub package not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id="ai4bharat/indictrans2-en-indic-1B",
            local_dir=target_dir
        )
        print(f"[✓] Model weights successfully downloaded to: {target_dir}")

def main():
    parser = argparse.ArgumentParser(description="Download AI4Bharat IndicTrans2 models for offline MediKiosk use.")
    parser.add_argument("--target-dir", default="./models/indictrans2", help="Local directory to store model weights")
    args = parser.parse_args()

    print("=" * 65)
    print(" MediKiosk — Offline AI4Bharat IndicTrans2 Setup")
    print("=" * 65)
    download_ctranslate2_weights(args.target_dir)
    print("\nTo activate local inference, ensure your .env has:")
    print("AI4BHARAT_MODE=local")
    print(f"LOCAL_INDICTRANS_PATH={args.target_dir}")
    print("=" * 65)

if __name__ == "__main__":
    main()
