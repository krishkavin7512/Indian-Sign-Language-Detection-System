"""
Standalone predictor for offline/batch inference.
Loads trained TF SavedModel and runs predictions without the FastAPI server.
"""
import numpy as np
import tensorflow as tf
import json
import cv2
from pathlib import Path
from typing import Optional


class StandalonePredictor:
    def __init__(self, models_dir: str = "../models"):
        self.models_dir = Path(models_dir)
        self.static_model = None
        self.dynamic_model = None
        self.static_labels = {}
        self.dynamic_labels = {}

    def load(self):
        static_path = self.models_dir / "static_classifier"
        if static_path.exists():
            self.static_model = tf.saved_model.load(str(static_path))
            lm = static_path / "label_map.json"
            if lm.exists():
                self.static_labels = json.loads(lm.read_text())

        dynamic_path = self.models_dir / "dynamic_classifier"
        if dynamic_path.exists():
            self.dynamic_model = tf.saved_model.load(str(dynamic_path))
            lm = dynamic_path / "label_map.json"
            if lm.exists():
                self.dynamic_labels = json.loads(lm.read_text())

    def predict_from_landmarks(self, landmarks: np.ndarray, model: str = "static") -> dict:
        """Predict from precomputed landmark array."""
        if model == "static" and self.static_model is not None:
            t = tf.constant(landmarks.reshape(1, -1), dtype=tf.float32)
            preds = self.static_model(t).numpy()[0]
            idx = int(np.argmax(preds))
            return {"label": self.static_labels.get(str(idx), "?"), "confidence": float(preds[idx])}
        elif model == "dynamic" and self.dynamic_model is not None:
            t = tf.constant(landmarks.reshape(1, 45, 258), dtype=tf.float32)
            preds = self.dynamic_model(t).numpy()[0]
            idx = int(np.argmax(preds))
            return {"label": self.dynamic_labels.get(str(idx), "?"), "confidence": float(preds[idx])}
        return {"label": "—", "confidence": 0.0}


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run standalone ISL predictor")
    parser.add_argument("--image", type=str, help="Path to image file for static prediction")
    parser.add_argument("--models", type=str, default="../models", help="Path to models directory")
    args = parser.parse_args()

    predictor = StandalonePredictor(models_dir=args.models)
    predictor.load()

    if args.image:
        import cv2
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"Cannot read image: {args.image}")
            sys.exit(1)
        import mediapipe as mp
        mp_hands = mp.solutions.hands
        with mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5) as hands:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)
            if results.multi_hand_landmarks:
                landmarks = np.array([
                    [lm.x, lm.y, lm.z]
                    for lm in results.multi_hand_landmarks[0].landmark
                ]).flatten()
                result = predictor.predict_from_landmarks(landmarks, model="static")
                print(f"Prediction: {result['label']} (confidence: {result['confidence']:.3f})")
            else:
                print("No hand detected in image")
    else:
        print("Loaded models:")
        print(f"  Static: {'loaded' if predictor.static_model else 'not found'} — {len(predictor.static_labels)} classes")
        print(f"  Dynamic: {'loaded' if predictor.dynamic_model else 'not found'} — {len(predictor.dynamic_labels)} classes")
