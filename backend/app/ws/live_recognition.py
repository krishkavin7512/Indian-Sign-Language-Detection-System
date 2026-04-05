import asyncio
import json
import numpy as np
import cv2
import sys
from pathlib import Path
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from app.services.recognizer import get_recognizer
from app.services.feature_extractor import get_feature_extractor

# Add ml directory to path for mode_selector import
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "ml"))


class SlidingWindowBuffer:
    """Maintains a rolling buffer of pre-extracted feature vectors."""
    def __init__(self, window_size: int = 45, overlap: int = 22):
        from collections import deque
        self.window_size = window_size
        self.overlap = overlap
        self.features = deque(maxlen=window_size)
        self.frame_count = 0

    def add_features(self, feature_vec: np.ndarray):
        self.features.append(feature_vec)
        self.frame_count += 1

    def is_ready(self) -> bool:
        if len(self.features) < self.window_size:
            return False
        return (self.frame_count - self.window_size) % (self.window_size - self.overlap) == 0

    def get_feature_sequence(self) -> np.ndarray:
        return np.array(list(self.features))


def detect_sign_type_simple(combined_features: np.ndarray) -> str:
    """Simple motion-based sign type detection."""
    if np.all(combined_features == 0):
        return "word"
    non_zero = combined_features[combined_features != 0]
    motion = float(np.std(non_zero)) if len(non_zero) > 0 else 0.0
    if motion < 0.02:
        return "alphabet"
    return "word"


async def live_recognition_endpoint(websocket: WebSocket):
    await websocket.accept()
    recognizer = get_recognizer()
    buffer = SlidingWindowBuffer(window_size=45, overlap=22)
    mode = "auto"
    logger.info("New WebSocket connection established")
    try:
        # First message must be mode selection
        config_msg = await websocket.receive_text()
        config = json.loads(config_msg)
        mode = config.get("mode", "auto")
        await websocket.send_json({"type": "config_ack", "mode": mode})

        while True:
            data = await websocket.receive_bytes()
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            extractor = get_feature_extractor()
            features = extractor.extract_landmarks(frame)

            # Send landmark data for visual overlay
            if features["landmark_data"]:
                await websocket.send_json({
                    "type": "landmark",
                    "data": features["landmark_data"]
                })

            buffer.add_features(features["combined"])
            if buffer.is_ready():
                effective_mode = mode

                if mode == "auto":
                    effective_mode = detect_sign_type_simple(features["combined"])
                    if effective_mode in ["alphabet", "number"] and recognizer.static_model is None:
                        effective_mode = "word"

                if effective_mode in ["alphabet", "number"]:
                    result = recognizer.predict_static(frame)
                elif effective_mode == "sentence":
                    feature_seq = buffer.get_feature_sequence()
                    sentence = recognizer.predict_sentence_from_features(feature_seq)
                    await websocket.send_json({
                        "type": "sentence",
                        "text": sentence,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    continue
                else:
                    feature_seq = buffer.get_feature_sequence()
                    result = recognizer.predict_dynamic_from_features(
                        feature_seq, features["landmarks_detected"]
                    )

                await websocket.send_json({
                    "type": "prediction",
                    "label": result.label,
                    "label_hindi": result.label_hindi,
                    "confidence": result.confidence,
                    "mode": result.mode,
                    "model_used": result.model_used,
                    "landmarks_detected": result.landmarks_detected,
                    "alternatives": [
                        {"label": a.label, "label_hindi": a.label_hindi, "confidence": a.confidence}
                        for a in result.alternatives
                    ],
                    "timestamp": asyncio.get_event_loop().time()
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected cleanly")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
