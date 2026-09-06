#!/usr/bin/env python3
"""
MediKiosk — Tesseract & Tessdata Language Pack Setup Script
Downloads official traineddata language packs (eng, hin, kan, tam, tel, mal, mar, ben, guj, pan)
from the official Tesseract repository into ./models/tessdata/.

Usage:
    python scripts/setup_tesseract.py [--target-dir ./models/tessdata]
"""

import os
import sys
import argparse
import urllib.request

TESSDATA_FAST_BASE = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/"
LANGUAGES = [
    ("eng.traineddata", "English (Default / Clinical)"),
    ("hin.traineddata", "Hindi"),
    ("kan.traineddata", "Kannada"),
    ("tam.traineddata", "Tamil"),
    ("tel.traineddata", "Telugu"),
    ("mal.traineddata", "Malayalam"),
    ("mar.traineddata", "Marathi"),
    ("ben.traineddata", "Bengali"),
    ("guj.traineddata", "Gujarati"),
    ("pan.traineddata", "Punjabi"),
    ("osd.traineddata", "Orientation & Script Detection")
]

def setup_tessdata(target_dir: str):
    os.makedirs(target_dir, exist_ok=True)
    print("=" * 65)
    print(" MediKiosk - Tesseract Indian Languages Setup")
    print("=" * 65)
    print(f"[*] Target Directory: {os.path.abspath(target_dir)}")

    success_count = 0
    for filename, lang_name in LANGUAGES:
        dest_path = os.path.join(target_dir, filename)
        if os.path.exists(dest_path):
            print(f"[OK] {lang_name} ({filename}) already present.")
            success_count += 1
            continue

        url = TESSDATA_FAST_BASE + filename
        print(f"[>] Downloading {lang_name} ({filename})...")
        try:
            urllib.request.urlretrieve(url, dest_path)
            print(f"    Saved to: {dest_path}")
            success_count += 1
        except Exception as e:
            print(f"    [!] Download failed for {filename}: {str(e)}")

    print("-" * 65)
    print(f"[OK] Setup complete! {success_count}/{len(LANGUAGES)} language packs ready in {target_dir}.")
    print("\nTo point MediKiosk to this local tessdata folder, verify .env has:")
    print(f"TESSDATA_PATH={target_dir}")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Tesseract traineddata for MediKiosk")
    parser.add_argument("--target-dir", default="./models/tessdata", help="Directory for traineddata files")
    args = parser.parse_args()
    setup_tessdata(args.target_dir)
