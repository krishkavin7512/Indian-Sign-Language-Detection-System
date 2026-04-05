"""
Preprocesses the ISL-CSLRT sentence dataset.
Actual path: datasets/ISL_CSLRT_Corpus/Videos_Sentence_Level/
Structure: each subfolder = one sentence (folder name = label), contains signer videos.

Extracts MediaPipe Holistic keypoints and builds a CTC-ready dataset.

Usage:
    python preprocess_sentence.py
"""

import cv2
import numpy as np
import mediapipe as mp
import json
from pathlib import Path
from tqdm import tqdm
import re

DATASET_PATH = Path("../../../datasets/ISL_CSLRT_Corpus/Videos_Sentence_Level")
OUTPUT_PATH = Path("../data/processed")
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
MAX_FRAMES = 150  # Max frames per sentence video (sentences are ~100 frames at 25fps)

mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(
    static_image_mode=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def extract_frame_features(frame: np.ndarray) -> np.ndarray:
    """Resize to 240p then extract 258-dim MediaPipe features."""
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


def process_video_sequence(video_path: str) -> np.ndarray:
    """Sequential read for speed; sample up to MAX_FRAMES evenly."""
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total < 5:
        cap.release()
        return None
    n_frames = min(total, MAX_FRAMES)
    sample_every = max(1, total // n_frames)
    features = []
    fi = 0
    while len(features) < n_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if fi % sample_every == 0:
            features.append(extract_frame_features(frame))
        fi += 1
    cap.release()
    if len(features) < 5:
        return None
    return np.array(features)


def get_video_files(folder: Path) -> list:
    """Get all video files in a folder, case-insensitive extensions."""
    videos = []
    for f in folder.iterdir():
        if f.is_file() and f.suffix.upper() in {".MP4", ".AVI", ".MOV", ".WEBM"}:
            videos.append(f)
    return sorted(videos)


def clean_label(folder_name: str) -> str:
    """
    Convert sentence folder name to clean label.
    e.g. 'He is going into the room' → 'HE IS GOING INTO THE ROOM'
    Removes parenthetical variants like '(2)' from duplicates.
    """
    cleaned = re.sub(r"\(\d+\)\s*$", "", folder_name).strip()
    return cleaned.upper()


def preprocess():
    sequences = []
    labels = []
    vocab = set()

    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found at {DATASET_PATH.resolve()}")
        return

    sentence_folders = sorted([d for d in DATASET_PATH.iterdir() if d.is_dir()])
    print(f"Found {len(sentence_folders)} sentence folders")

    for sent_dir in tqdm(sentence_folders, desc="Processing sentences"):
        label = clean_label(sent_dir.name)
        videos = get_video_files(sent_dir)
        if not videos:
            continue
        # Process one representative video per sentence (first one by name)
        for vf in videos[:3]:  # up to 3 signers per sentence
            seq = process_video_sequence(str(vf))
            if seq is None:
                continue
            sequences.append(seq)
            labels.append(label)
            for word in label.split():
                vocab.add(word)

    vocab_list = sorted(vocab)
    vocab_map = {word: idx for idx, word in enumerate(vocab_list)}

    print(f"Total sentences: {len(sequences)}, Vocabulary: {len(vocab_map)}")

    with open(OUTPUT_PATH / "sentence_vocab.json", "w") as f:
        json.dump(vocab_map, f, indent=2)

    with open(OUTPUT_PATH / "sentence_labels.json", "w") as f:
        json.dump(labels, f, indent=2)

    # Save variable-length sequences
    np.save(OUTPUT_PATH / "sentence_sequences.npy", np.array(sequences, dtype=object), allow_pickle=True)
    print("Sentence preprocessing complete!")


if __name__ == "__main__":
    preprocess()
