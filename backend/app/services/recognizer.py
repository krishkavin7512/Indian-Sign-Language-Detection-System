import numpy as np
import tensorflow as tf
import json
import os
from pathlib import Path
from loguru import logger
from app.config import get_settings
from app.services.feature_extractor import get_feature_extractor
from app.services.translator import translate_to_hindi
from app.schemas.recognize import PredictionResult, PredictionAlternative

settings = get_settings()


class ISLRecognizer:
    def __init__(self):
        self.static_model = None
        self.dynamic_model = None
        self.sentence_model = None
        self.static_label_map = {}
        self.dynamic_label_map = {}
        self.sentence_vocab = {}
        self.models_loaded = False
        self.feature_extractor = get_feature_extractor()

    def load_models(self):
        """Load all trained models. Called at application startup."""
        static_path = Path(settings.static_model_path)
        try:
            if (static_path / "saved_model.pb").exists():
                self.static_model = tf.saved_model.load(str(static_path))
                label_map_path = static_path / "label_map.json"
                if label_map_path.exists():
                    with open(label_map_path) as f:
                        self.static_label_map = json.load(f)
                logger.info(f"Static model loaded. Classes: {len(self.static_label_map)}")
            else:
                logger.warning(f"Static model not found at {static_path}. Skipping.")
        except Exception as e:
            logger.error(f"Error loading static model: {e}")

        dynamic_path = Path(settings.dynamic_model_path)
        try:
            if (dynamic_path / "saved_model.pb").exists():
                self.dynamic_model = tf.saved_model.load(str(dynamic_path))
                label_map_path = dynamic_path / "label_map.json"
                if label_map_path.exists():
                    with open(label_map_path) as f:
                        self.dynamic_label_map = json.load(f)
                logger.info(f"Dynamic model loaded. Classes: {len(self.dynamic_label_map)}")
            else:
                logger.warning(f"Dynamic model not found at {dynamic_path}. Skipping.")
        except Exception as e:
            logger.error(f"Error loading dynamic model: {e}")

        sentence_path = Path(settings.sentence_model_path)
        try:
            if (sentence_path / "saved_model.pb").exists():
                self.sentence_model = tf.saved_model.load(str(sentence_path))
                vocab_path = sentence_path / "vocab.json"
                if vocab_path.exists():
                    with open(vocab_path) as f:
                        self.sentence_vocab = json.load(f)
                logger.info(f"Sentence model loaded. Vocab size: {len(self.sentence_vocab)}")
            else:
                logger.warning(f"Sentence model not found at {sentence_path}. Skipping.")
        except Exception as e:
            logger.error(f"Error loading sentence model: {e}")

        self.models_loaded = (
            self.static_model is not None or
            self.dynamic_model is not None
        )
        logger.info(f"Model loading complete. Ready: {self.models_loaded}")

    def predict_static(self, frame: np.ndarray) -> PredictionResult:
        """Predict alphabet or number from a single frame."""
        features = self.feature_extractor.extract_landmarks(frame)
        landmarks_detected = features["landmarks_detected"]

        if not landmarks_detected or self.static_model is None:
            return PredictionResult(
                label="—", confidence=0.0, mode="alphabet",
                model_used="static_cnn", landmarks_detected=False
            )

        hand_features = np.concatenate([features["left_hand"], features["right_hand"]])
        normalized = self.feature_extractor.normalize_landmarks(hand_features)
        input_tensor = tf.constant(normalized.reshape(1, -1), dtype=tf.float32)

        predictions = self.static_model(input_tensor).numpy()[0]
        top_indices = np.argsort(predictions)[::-1][:3]

        label = self.static_label_map.get(str(top_indices[0]), "Unknown")
        confidence = float(predictions[top_indices[0]])

        alternatives = [
            PredictionAlternative(
                label=self.static_label_map.get(str(i), "?"),
                label_hindi=translate_to_hindi(self.static_label_map.get(str(i), "?")),
                confidence=float(predictions[i])
            )
            for i in top_indices[1:3]
        ]

        return PredictionResult(
            label=label,
            label_hindi=translate_to_hindi(label),
            confidence=confidence,
            mode="alphabet" if label.isalpha() and len(label) == 1 else "number",
            model_used="static_cnn",
            landmarks_detected=True,
            alternatives=alternatives
        )

    def predict_dynamic(self, frame_sequence: list) -> PredictionResult:
        """Predict word or phrase from a sequence of 45 frames."""
        if self.dynamic_model is None or len(frame_sequence) < 10:
            return PredictionResult(
                label="—", confidence=0.0, mode="word",
                model_used="dynamic_lstm", landmarks_detected=False
            )

        feature_seq = []
        landmarks_detected = False
        for frame in frame_sequence:
            features = self.feature_extractor.extract_landmarks(frame)
            if features["landmarks_detected"]:
                landmarks_detected = True
            feature_seq.append(features["combined"])

        if not landmarks_detected:
            return PredictionResult(
                label="—", confidence=0.0, mode="word",
                model_used="dynamic_lstm", landmarks_detected=False
            )

        # Pad or trim to exactly 45 frames
        target_len = 45
        seq_array = np.array(feature_seq)
        if len(seq_array) < target_len:
            pad = np.zeros((target_len - len(seq_array), 258))
            seq_array = np.vstack([seq_array, pad])
        else:
            indices = np.linspace(0, len(seq_array) - 1, target_len, dtype=int)
            seq_array = seq_array[indices]

        input_tensor = tf.constant(seq_array.reshape(1, 45, 258), dtype=tf.float32)
        predictions = self.dynamic_model(input_tensor).numpy()[0]
        top_indices = np.argsort(predictions)[::-1][:3]

        label = self.dynamic_label_map.get(str(top_indices[0]), "Unknown")
        confidence = float(predictions[top_indices[0]])

        alternatives = [
            PredictionAlternative(
                label=self.dynamic_label_map.get(str(i), "?"),
                label_hindi=translate_to_hindi(self.dynamic_label_map.get(str(i), "?")),
                confidence=float(predictions[i])
            )
            for i in top_indices[1:3]
        ]

        return PredictionResult(
            label=label,
            label_hindi=translate_to_hindi(label),
            confidence=confidence,
            mode="word",
            model_used="dynamic_lstm",
            landmarks_detected=True,
            alternatives=alternatives
        )

    def predict_dynamic_from_features(self, feature_seq: np.ndarray, landmarks_detected: bool) -> PredictionResult:
        """Predict from pre-extracted feature sequence — no MediaPipe re-processing."""
        if self.dynamic_model is None:
            return PredictionResult(
                label="—", confidence=0.0, mode="word",
                model_used="dynamic_lstm", landmarks_detected=False
            )
        # Require at least 50% of frames to have actual hand landmarks
        hand_frames = np.sum(np.any(feature_seq[:, :126] != 0, axis=1))
        if hand_frames < len(feature_seq) * 0.5:
            return PredictionResult(
                label="—", confidence=0.0, mode="word",
                model_used="dynamic_lstm", landmarks_detected=False
            )
        # Motion gate — require meaningful temporal variation in hand features
        hand_seq = feature_seq[:, :126]
        active = hand_seq[np.any(hand_seq != 0, axis=1)]
        if len(active) < 5 or float(np.std(active)) < 0.04:
            return PredictionResult(
                label="—", confidence=0.0, mode="word",
                model_used="dynamic_lstm", landmarks_detected=True
            )

        seq = feature_seq[:45] if len(feature_seq) >= 45 else np.vstack([
            feature_seq, np.zeros((45 - len(feature_seq), 258))
        ])

        # Custom sign check — user-taught signs take priority over BiLSTM
        from app.services.custom_sign_store import get_custom_sign_store
        match = get_custom_sign_store().match(seq)
        if match:
            c_label, c_hindi, c_sim = match
            return PredictionResult(
                label=c_label, label_hindi=c_hindi,
                confidence=float(c_sim), mode="word",
                model_used="custom_taught", landmarks_detected=True
            )

        input_tensor = tf.constant(seq.reshape(1, 45, 258), dtype=tf.float32)
        raw = self.dynamic_model(input_tensor, training=False).numpy()[0]

        # Temperature scaling (T=3) — corrects overconfidence from no label smoothing
        T = 3.0
        scaled = np.power(raw + 1e-10, 1.0 / T)
        predictions = scaled / scaled.sum()

        top_indices = np.argsort(predictions)[::-1][:3]
        label = self.dynamic_label_map.get(str(top_indices[0]), "Unknown")
        confidence = float(predictions[top_indices[0]])
        alternatives = [
            PredictionAlternative(
                label=self.dynamic_label_map.get(str(i), "?"),
                label_hindi=translate_to_hindi(self.dynamic_label_map.get(str(i), "?")),
                confidence=float(predictions[i])
            )
            for i in top_indices[1:3]
        ]
        return PredictionResult(
            label=label, label_hindi=translate_to_hindi(label),
            confidence=confidence, mode="word", model_used="dynamic_lstm",
            landmarks_detected=True, alternatives=alternatives
        )

    def predict_sentence_from_features(self, feature_seq: np.ndarray) -> str:
        """Predict sentence from pre-extracted feature sequence."""
        if self.dynamic_model is None:
            return ""
        words = []
        chunk = 45
        for i in range(0, len(feature_seq) - chunk + 1, chunk // 2):
            result = self.predict_dynamic_from_features(feature_seq[i:i+chunk], True)
            if result.confidence > 0.7 and result.label != "—":
                if not words or words[-1] != result.label:
                    words.append(result.label)
        return " ".join(words)

    def predict_sentence(self, frame_sequence: list) -> str:
        """Recognize continuous ISL sentence from a long frame sequence."""
        if self.sentence_model is None:
            return ""
        # Accumulate word predictions with deduplication
        words = []
        chunk_size = 45
        for i in range(0, len(frame_sequence) - chunk_size + 1, chunk_size // 2):
            chunk = frame_sequence[i:i + chunk_size]
            result = self.predict_dynamic(chunk)
            if result.confidence > 0.7 and result.label != "—":
                if not words or words[-1] != result.label:
                    words.append(result.label)
        return " ".join(words)


# Singleton
_recognizer_instance = None


def get_recognizer() -> ISLRecognizer:
    global _recognizer_instance
    if _recognizer_instance is None:
        _recognizer_instance = ISLRecognizer()
    return _recognizer_instance
