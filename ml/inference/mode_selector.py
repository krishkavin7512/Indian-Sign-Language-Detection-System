import numpy as np
from collections import deque
from typing import List


class SlidingWindowBuffer:
    """Maintains a rolling buffer of frames for live recognition."""
    def __init__(self, window_size: int = 45, overlap: int = 22):
        self.window_size = window_size
        self.overlap = overlap
        self.frames = deque(maxlen=window_size)
        self.frame_count = 0

    def add_frame(self, frame: np.ndarray):
        self.frames.append(frame)
        self.frame_count += 1

    def is_ready(self) -> bool:
        if len(self.frames) < self.window_size:
            return False
        return (self.frame_count - self.window_size) % (self.window_size - self.overlap) == 0

    def get_frames(self) -> List[np.ndarray]:
        return list(self.frames)


def compute_motion_score(combined_features: np.ndarray) -> float:
    """Compute how much motion is in the current landmark frame."""
    if np.all(combined_features == 0):
        return 0.0
    non_zero = combined_features[combined_features != 0]
    return float(np.std(non_zero))


_motion_history = deque(maxlen=30)


def detect_sign_type(combined_features: np.ndarray) -> str:
    """
    Auto-detect whether user is doing a static sign, dynamic word, or sentence.
    Returns: 'alphabet' | 'word' | 'sentence'
    """
    motion = compute_motion_score(combined_features)
    _motion_history.append(motion)
    if len(_motion_history) < 10:
        return "word"
    avg_motion = np.mean(list(_motion_history))
    motion_variance = np.var(list(_motion_history))
    if avg_motion < 0.02:
        return "alphabet"
    elif len(_motion_history) >= 30 and motion_variance > 0.001:
        return "sentence"
    else:
        return "word"
