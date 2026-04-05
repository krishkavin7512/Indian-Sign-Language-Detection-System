"""
Preprocesses the Kaggle ISL static dataset (A-Z, 0-9 images).
Extracts MediaPipe hand landmarks from each image.
Saves processed numpy arrays for model training.

Usage:
    python preprocess_static.py
"""

import cv2
import numpy as np
import mediapipe as mp
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from tqdm import tqdm

DATASET_PATH = Path("../../../datasets/kaggle_isl")  # Kaggle ISL not present — see note below
# NOTE: The Kaggle ISL static sign dataset was not included in this installation.
# The system works without it — the dynamic LSTM handles all 263 INCLUDE words.
# To add A-Z/0-9 static recognition, download from:
#   https://www.kaggle.com/datasets/ash2703/handsignimages
# and place in datasets/kaggle_isl/ then re-run this script.
OUTPUT_PATH = Path("../data/processed")
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5)


def extract_hand_landmarks(image_path: str) -> np.ndarray:
    """Extract 21 hand landmarks (63 values) from an image."""
    img = cv2.imread(image_path)
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    if not results.multi_hand_landmarks:
        return None
    landmarks = results.multi_hand_landmarks[0]
    coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark]).flatten()
    # Normalize relative to wrist
    wrist = coords[:3]
    coords = coords - np.tile(wrist, 21)
    return coords


def preprocess():
    X, y = [], []
    label_map = {}
    label_idx = 0

    class_folders = sorted([d for d in DATASET_PATH.iterdir() if d.is_dir()])
    print(f"Found {len(class_folders)} classes: {[f.name for f in class_folders]}")

    for folder in class_folders:
        class_name = folder.name.upper()
        label_map[str(label_idx)] = class_name
        print(f"Processing class: {class_name} (label {label_idx})")
        count = 0
        for img_file in tqdm(list(folder.glob("*.jpg")) + list(folder.glob("*.png")) + list(folder.glob("*.jpeg"))):
            landmarks = extract_hand_landmarks(str(img_file))
            if landmarks is not None:
                X.append(landmarks)
                y.append(label_idx)
                count += 1
        print(f"  Valid samples: {count}")
        label_idx += 1

    X = np.array(X)
    y = np.array(y)
    print(f"\nTotal valid samples: {len(X)}")
    print(f"Feature shape: {X.shape}")

    with open(OUTPUT_PATH / "static_label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)
    print(f"Label map saved: {len(label_map)} classes")

    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, stratify=y, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176, stratify=y_temp, random_state=42)

    np.save(OUTPUT_PATH / "static_X_train.npy", X_train)
    np.save(OUTPUT_PATH / "static_y_train.npy", y_train)
    np.save(OUTPUT_PATH / "static_X_val.npy", X_val)
    np.save(OUTPUT_PATH / "static_y_val.npy", y_val)
    np.save(OUTPUT_PATH / "static_X_test.npy", X_test)
    np.save(OUTPUT_PATH / "static_y_test.npy", y_test)
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    print("Static preprocessing complete!")


if __name__ == "__main__":
    preprocess()
