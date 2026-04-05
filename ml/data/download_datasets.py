"""
Helper script to verify dataset presence and optionally download missing datasets.
Datasets should already be placed in datasets/ folder as described in the README.

Usage:
    python download_datasets.py --check        # just verify paths
    python download_datasets.py --download     # attempt download (requires credentials)
"""

import os
import sys
import argparse
from pathlib import Path

DATASETS_ROOT = Path("../../../datasets")

# Actual dataset structure after extraction:
# - INCLUDE 263-word dataset: category folders at DATASETS_ROOT root level
#   (Adjectives/, Animals/, Clothes/, ...) with sign subfolders containing .MOV files
# - ISL-CSLRT sentence corpus: DATASETS_ROOT/ISL_CSLRT_Corpus/Videos_Sentence_Level/
# - CISLR v1.5a: DATASETS_ROOT/CISLR_v1.5-a_videos/ (YouTube-sourced word videos)

INCLUDE_CATEGORIES = [
    "Adjectives", "Animals", "Clothes", "Colours", "Days_and_Time",
    "Electronics", "Greetings", "Home", "Indian", "Jobs",
    "Means_of_Transportation", "People", "Places", "Pronouns",
    "Seasons", "Society"
]


def check_datasets():
    all_ok = True

    # Check INCLUDE (category folders at root)
    include_present = sum(1 for c in INCLUDE_CATEGORIES if (DATASETS_ROOT / c).exists())
    if include_present == len(INCLUDE_CATEGORIES):
        n_videos = sum(
            1 for c in INCLUDE_CATEGORIES
            for f in (DATASETS_ROOT / c).rglob("*")
            if f.suffix.upper() in {".MOV", ".MP4", ".AVI"}
        )
        print(f"[OK]  INCLUDE dataset: {include_present} categories, {n_videos} videos")
    else:
        print(f"[PARTIAL] INCLUDE: {include_present}/{len(INCLUDE_CATEGORIES)} categories found")
        print(f"          Expected category folders in: {DATASETS_ROOT.resolve()}")
        all_ok = False

    # Check ISL-CSLRT
    cslrt_path = DATASETS_ROOT / "ISL_CSLRT_Corpus" / "Videos_Sentence_Level"
    if cslrt_path.exists():
        n_sent = sum(1 for d in cslrt_path.iterdir() if d.is_dir())
        print(f"[OK]  ISL-CSLRT: {n_sent} sentence folders at {cslrt_path}")
    else:
        print(f"[MISSING] ISL-CSLRT: {cslrt_path.resolve()}")
        all_ok = False

    # Check CISLR (optional)
    cislr_path = DATASETS_ROOT / "CISLR_v1.5-a_videos"
    if cislr_path.exists():
        n_vids = sum(1 for f in cislr_path.iterdir() if f.suffix.lower() in {".mp4", ".avi"})
        print(f"[OK]  CISLR v1.5a: {n_vids} videos (optional supplementary data)")
    else:
        print(f"[INFO] CISLR v1.5-a: not present (optional)")

    return all_ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", default=True)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    print("=== Dataset Check ===")
    ok = check_datasets()
    if ok:
        print("\nAll datasets present. Ready to preprocess.")
    else:
        print("\nSome datasets missing. Please download and place them in datasets/")
        print("See README.md for download instructions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
