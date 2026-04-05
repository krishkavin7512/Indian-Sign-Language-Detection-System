"""
Custom sign store — persists user-taught signs as mean feature templates.
Matching uses cosine similarity on the flattened (45×258) sequence.
"""
import json
import numpy as np
from pathlib import Path
from threading import Lock
from loguru import logger

STORE_DIR = Path(__file__).parent.parent.parent / "custom_signs"
STORE_FILE = STORE_DIR / "signs.json"


class CustomSignStore:
    def __init__(self):
        STORE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._signs: dict = {}  # label -> {label_hindi, mean_template ndarray}
        self._load()
        logger.info(f"CustomSignStore: {len(self._signs)} custom sign(s) loaded")

    def _load(self):
        if not STORE_FILE.exists():
            return
        try:
            raw = json.loads(STORE_FILE.read_text(encoding="utf-8"))
            for label, info in raw.items():
                self._signs[label] = {
                    "label_hindi": info.get("label_hindi", ""),
                    "mean_template": np.array(info["mean_template"], dtype=np.float32),
                }
        except Exception as e:
            logger.error(f"Failed to load custom signs: {e}")

    def _persist(self):
        """Write to disk — must be called while holding self._lock."""
        disk = {
            k: {
                "label_hindi": v["label_hindi"],
                "mean_template": v["mean_template"].tolist(),
            }
            for k, v in self._signs.items()
        }
        STORE_FILE.write_text(
            json.dumps(disk, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add_sign(self, label: str, label_hindi: str, templates: list) -> None:
        """Store or overwrite a sign from 2-6 recorded feature sequences."""
        stacked = np.stack(templates, axis=0)          # (N, 45, 258)
        mean_tmpl = stacked.mean(axis=0).astype(np.float32)  # (45, 258)
        with self._lock:
            self._signs[label.upper()] = {
                "label_hindi": label_hindi,
                "mean_template": mean_tmpl,
            }
            self._persist()
        logger.info(f"Custom sign saved: {label.upper()} ({len(templates)} samples)")

    def match(self, feature_seq: np.ndarray, threshold: float = 0.88):
        """
        Compare feature_seq (45, 258) against all stored templates.
        Returns (label, label_hindi, similarity) or None.
        """
        if not self._signs:
            return None
        seq_flat = feature_seq.flatten().astype(np.float32)
        seq_norm = float(np.linalg.norm(seq_flat))
        if seq_norm < 1e-6:
            return None

        best_label, best_hindi, best_sim = None, "", threshold
        for label, info in self._signs.items():
            tmpl_flat = info["mean_template"].flatten()
            tmpl_norm = float(np.linalg.norm(tmpl_flat))
            if tmpl_norm < 1e-6:
                continue
            sim = float(np.dot(seq_flat, tmpl_flat) / (seq_norm * tmpl_norm))
            if sim > best_sim:
                best_sim, best_label, best_hindi = sim, label, info["label_hindi"]

        return (best_label, best_hindi, best_sim) if best_label else None

    def list_signs(self) -> list:
        return [{"label": k, "label_hindi": v["label_hindi"]} for k, v in self._signs.items()]

    def delete_sign(self, label: str) -> bool:
        label = label.upper()
        with self._lock:
            if label not in self._signs:
                return False
            del self._signs[label]
            self._persist()
        logger.info(f"Custom sign deleted: {label}")
        return True


_store: CustomSignStore | None = None


def get_custom_sign_store() -> CustomSignStore:
    global _store
    if _store is None:
        _store = CustomSignStore()
    return _store
