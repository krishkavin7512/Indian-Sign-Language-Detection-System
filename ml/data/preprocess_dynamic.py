"""
Preprocesses the INCLUDE ISL dynamic dataset (263 word signs, ~3652 videos).
Actual dataset path: datasets/ (category folders at root level)
Structure: datasets/<Category>/<n>. <word>/MVI_xxxx.MOV

Extracts MediaPipe Holistic keypoints from each video.
Saves sequences as numpy arrays for LSTM training.

Usage:
    python preprocess_dynamic.py
"""

import cv2
import numpy as np
import mediapipe as mp
import json
import re
from pathlib import Path
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# INCLUDE dataset is at the top-level datasets/ folder with category subfolders
DATASET_PATH = Path("../../../datasets")
OUTPUT_PATH = Path("../data/processed")
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
FRAMES_PER_VIDEO = 45

# These are the 16 INCLUDE category folders
INCLUDE_CATEGORIES = {
    "Adjectives", "Animals", "Clothes", "Colours", "Days_and_Time",
    "Electronics", "Greetings", "Home", "Indian", "Jobs",
    "Means_of_Transportation", "People", "Places", "Pronouns",
    "Seasons", "Society"
}

mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(
    static_image_mode=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def extract_class_name(folder_name: str) -> str:
    """Extract clean class name from folder like '1. Dog' → 'DOG'."""
    cleaned = re.sub(r"^\d+\.\s*", "", folder_name).strip()
    return cleaned.upper()


def collect_sign_folders(dataset_root: Path) -> list:
    """
    Collect all (sign_folder_path, class_name) pairs from INCLUDE structure.
    datasets/<Category>/<n>. <word>/
    """
    sign_folders = []
    for cat_dir in sorted(dataset_root.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name not in INCLUDE_CATEGORIES:
            continue
        for sign_dir in sorted(cat_dir.iterdir()):
            if not sign_dir.is_dir():
                continue
            class_name = extract_class_name(sign_dir.name)
            if class_name:
                sign_folders.append((sign_dir, class_name))
    return sign_folders


def get_video_files(folder: Path) -> list:
    """
    Get all video files in a folder, including Extra/ subdirectory.
    Case-insensitive extension matching.
    """
    VIDEO_EXTS = {".MOV", ".MP4", ".AVI", ".WEBM"}
    videos = []
    for f in folder.iterdir():
        if f.is_file() and f.suffix.upper() in VIDEO_EXTS:
            videos.append(f)
        elif f.is_dir() and f.name.lower() == "extra":
            # Include Extra/ subfolder videos (additional signer recordings)
            for ef in f.iterdir():
                if ef.is_file() and ef.suffix.upper() in VIDEO_EXTS:
                    videos.append(ef)
    return sorted(videos)


def extract_frame_features(frame: np.ndarray) -> np.ndarray:
    """
    Extract 258-dim feature vector from a single frame.
    Resizes to 240p — MediaPipe landmarks are normalized [0,1] so resize is lossless.
    """
    h, w = frame.shape[:2]
    if h > 240:
        scale = 240 / h
        frame = cv2.resize(frame, (int(w * scale), 240), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False
    results = holistic.process(rgb)
    left_hand = np.array([[lm.x, lm.y, lm.z] for lm in results.left_hand_landmarks.landmark]).flatten() \
        if results.left_hand_landmarks else np.zeros(63)
    right_hand = np.array([[lm.x, lm.y, lm.z] for lm in results.right_hand_landmarks.landmark]).flatten() \
        if results.right_hand_landmarks else np.zeros(63)
    pose = np.array([[lm.x, lm.y, lm.z, lm.visibility] for lm in results.pose_landmarks.landmark]).flatten() \
        if results.pose_landmarks else np.zeros(132)
    return np.concatenate([left_hand, right_hand, pose])


def process_video(video_path: str) -> np.ndarray:
    """
    Process a video file and return (FRAMES_PER_VIDEO, 258) feature array.
    Uses sequential reading (faster than random seek on MOV files).
    """
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total < 5:
        cap.release()
        return None
    sample_every = max(1, total // FRAMES_PER_VIDEO)
    features = []
    fi = 0
    while len(features) < FRAMES_PER_VIDEO:
        ret, frame = cap.read()
        if not ret:
            break
        if fi % sample_every == 0:
            features.append(extract_frame_features(frame))
        fi += 1
    cap.release()
    # Pad if short video
    while len(features) < FRAMES_PER_VIDEO:
        features.append(np.zeros(258))
    seq = np.array(features[:FRAMES_PER_VIDEO])
    return seq if seq.shape == (FRAMES_PER_VIDEO, 258) else None


def preprocess():
    sign_folders = collect_sign_folders(DATASET_PATH)
    print(f"Found {len(sign_folders)} sign classes")

    # Build label map (alphabetically sorted for reproducibility)
    unique_classes = sorted(set(cls for _, cls in sign_folders))
    class_to_idx = {cls: i for i, cls in enumerate(unique_classes)}
    label_map = {str(i): cls for cls, i in class_to_idx.items()}
    print(f"Unique classes: {len(unique_classes)}")

    X, y = [], []
    skipped = 0

    for sign_dir, class_name in tqdm(sign_folders, desc="Processing classes"):
        videos = get_video_files(sign_dir)
        if not videos:
            skipped += 1
            continue
        label_idx = class_to_idx[class_name]
        for vf in videos:
            seq = process_video(str(vf))
            if seq is not None:
                X.append(seq)
                y.append(label_idx)
            else:
                skipped += 1

    print(f"\nTotal valid sequences: {len(X)}, Skipped: {skipped}")
    if len(X) == 0:
        print("ERROR: No sequences extracted. Check dataset path.")
        return

    X = np.array(X)
    y = np.array(y)
    print(f"Data shape: {X.shape}, Labels shape: {y.shape}")
    print(f"Classes present: {len(np.unique(y))}")

    with open(OUTPUT_PATH / "dynamic_label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)
    print(f"Label map saved: {len(label_map)} classes")

    # Stratified split: 70% train / 15% val / 15% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=42
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.176, stratify=y_train, random_state=42
    )

    np.save(OUTPUT_PATH / "dynamic_X_train.npy", X_train)
    np.save(OUTPUT_PATH / "dynamic_y_train.npy", y_train)
    np.save(OUTPUT_PATH / "dynamic_X_val.npy", X_val)
    np.save(OUTPUT_PATH / "dynamic_y_val.npy", y_val)
    np.save(OUTPUT_PATH / "dynamic_X_test.npy", X_test)
    np.save(OUTPUT_PATH / "dynamic_y_test.npy", y_test)
    print(f"Split -> Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    print("Dynamic preprocessing complete!")


if __name__ == "__main__":
    preprocess()
