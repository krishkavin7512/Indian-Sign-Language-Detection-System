import cv2
import numpy as np
import mediapipe as mp
from loguru import logger
from app.config import get_settings

settings = get_settings()


class FeatureExtractor:
    def __init__(self):
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            min_detection_confidence=settings.mediapipe_min_detection_confidence,
            min_tracking_confidence=settings.mediapipe_min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        logger.info("FeatureExtractor initialized with MediaPipe Holistic (legacy API)")

    def extract_landmarks(self, frame: np.ndarray) -> dict:
        """
        Extract MediaPipe Holistic landmarks from a BGR frame.
        Returns dict with keys: left_hand, right_hand, pose, combined, raw_results
        combined shape: (258,) — hands (126) + pose (132)
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.holistic.process(rgb)
        rgb.flags.writeable = True

        # Left hand: 21 landmarks x 3 = 63 values
        if results.left_hand_landmarks:
            left_hand = np.array([[lm.x, lm.y, lm.z] for lm in results.left_hand_landmarks.landmark]).flatten()
        else:
            left_hand = np.zeros(63)

        # Right hand: 21 landmarks x 3 = 63 values
        if results.right_hand_landmarks:
            right_hand = np.array([[lm.x, lm.y, lm.z] for lm in results.right_hand_landmarks.landmark]).flatten()
        else:
            right_hand = np.zeros(63)

        # Pose: 33 landmarks x 4 = 132 values (x, y, z, visibility)
        if results.pose_landmarks:
            pose = np.array([[lm.x, lm.y, lm.z, lm.visibility] for lm in results.pose_landmarks.landmark]).flatten()
        else:
            pose = np.zeros(132)

        combined = np.concatenate([left_hand, right_hand, pose])  # 258 total

        landmarks_detected = (
            results.left_hand_landmarks is not None or
            results.right_hand_landmarks is not None
        )

        # Serialize landmarks for sending over WebSocket to frontend for overlay
        landmark_data = {}
        if results.left_hand_landmarks:
            landmark_data["left_hand"] = [
                {"x": lm.x, "y": lm.y, "z": lm.z}
                for lm in results.left_hand_landmarks.landmark
            ]
        if results.right_hand_landmarks:
            landmark_data["right_hand"] = [
                {"x": lm.x, "y": lm.y, "z": lm.z}
                for lm in results.right_hand_landmarks.landmark
            ]
        if results.pose_landmarks:
            landmark_data["pose"] = [
                {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                for lm in results.pose_landmarks.landmark
            ]

        return {
            "left_hand": left_hand,
            "right_hand": right_hand,
            "pose": pose,
            "combined": combined,
            "landmarks_detected": landmarks_detected,
            "landmark_data": landmark_data,
            "raw_results": results
        }

    def normalize_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """Normalize landmarks relative to wrist position for translation invariance."""
        if np.all(landmarks == 0):
            return landmarks
        non_zero = landmarks[landmarks != 0]
        if len(non_zero) == 0:
            return landmarks
        mean = np.mean(non_zero)
        std = np.std(non_zero)
        if std == 0:
            return landmarks
        return (landmarks - mean) / std

    def close(self):
        self.holistic.close()


# Singleton instance
_extractor_instance = None


def get_feature_extractor() -> FeatureExtractor:
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = FeatureExtractor()
    return _extractor_instance
