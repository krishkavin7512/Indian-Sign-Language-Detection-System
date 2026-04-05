import cv2
import numpy as np
from pathlib import Path
from loguru import logger
from typing import List, Generator


def extract_frames(video_path: str, fps_target: int = 15) -> Generator[np.ndarray, None, None]:
    """Generator that yields frames sampled at fps_target from a video file."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return

    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    sample_every = max(1, int(source_fps / fps_target))
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every == 0:
            yield frame
        frame_idx += 1

    cap.release()


def get_video_info(video_path: str) -> dict:
    """Return basic metadata about a video file."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {}
    info = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "duration_s": cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    }
    cap.release()
    return info


def resize_frame(frame: np.ndarray, width: int = 640, height: int = 480) -> np.ndarray:
    """Resize a frame to target dimensions."""
    return cv2.resize(frame, (width, height))
