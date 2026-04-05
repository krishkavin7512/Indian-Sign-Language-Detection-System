"""
WebSocket endpoint for interactive sign teaching.

Protocol (text = JSON, binary = JPEG frame):
  C→S  config:  {"label": "NAMASTE", "label_hindi": "नमस्ते", "samples": 4}
  S→C  ready:   {"type": "teach_ready", "label": "...", "total_samples": 4}

  For each sample i in 1..N:
    C→S  ctrl:   {"type": "begin_sample"}   (user clicks Start)
    S→C  status: {"type": "recording", "current": i, "total": N}
    C→S  <binary JPEG frames × 45>
    S→C  result: {"type": "sample_captured", "count": i, "total": N, "landmark_frames": k}
                 OR {"type": "sample_failed", "reason": "..."}

  After all samples saved:
    S→C  done:   {"type": "teaching_complete", "label": "...", "label_hindi": "...", "samples_recorded": N}
"""
import json
import numpy as np
import cv2
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from app.services.feature_extractor import get_feature_extractor
from app.services.custom_sign_store import get_custom_sign_store

FRAMES_PER_SAMPLE = 45
MIN_LANDMARK_FRAMES = 15   # out of 45 — hands must be visible at least 1/3 of the time


async def teach_session_endpoint(websocket: WebSocket):
    await websocket.accept()
    extractor = get_feature_extractor()
    store = get_custom_sign_store()

    try:
        # ── Config ────────────────────────────────────────────────────────────
        raw = await websocket.receive_text()
        cfg = json.loads(raw)
        label = cfg.get("label", "CUSTOM").strip().upper()
        label_hindi = cfg.get("label_hindi", "").strip()
        total_samples = int(max(2, min(cfg.get("samples", 4), 6)))

        logger.info(f"Teach session start: label={label}, samples={total_samples}")
        await websocket.send_json({
            "type": "teach_ready",
            "label": label,
            "total_samples": total_samples,
        })

        templates = []

        # ── Sample loop ───────────────────────────────────────────────────────
        while len(templates) < total_samples:
            # Wait for user "begin_sample" signal
            while True:
                msg = await websocket.receive()
                if msg.get("text"):
                    ctrl = json.loads(msg["text"])
                    if ctrl.get("type") == "begin_sample":
                        break
                # discard stale binary frames while waiting

            current_num = len(templates) + 1
            await websocket.send_json({
                "type": "recording",
                "current": current_num,
                "total": total_samples,
            })

            # ── Collect FRAMES_PER_SAMPLE frames ─────────────────────────────
            frame_features = []
            landmark_count = 0

            while len(frame_features) < FRAMES_PER_SAMPLE:
                msg = await websocket.receive()
                raw_bytes = msg.get("bytes")
                if not raw_bytes:
                    continue
                nparr = np.frombuffer(raw_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                feat = extractor.extract_landmarks(frame)
                frame_features.append(feat["combined"])
                if feat["landmarks_detected"]:
                    landmark_count += 1
                # Stream landmarks for overlay visualisation
                if feat["landmark_data"]:
                    await websocket.send_json({"type": "landmark", "data": feat["landmark_data"]})

            seq = np.array(frame_features, dtype=np.float32)  # (45, 258)

            if landmark_count < MIN_LANDMARK_FRAMES:
                await websocket.send_json({
                    "type": "sample_failed",
                    "current": current_num,
                    "total": total_samples,
                    "landmark_frames": landmark_count,
                    "reason": f"Only {landmark_count}/45 frames had visible hands. Keep hands in frame.",
                })
                # Don't count this sample — loop will ask again
                continue

            templates.append(seq)
            await websocket.send_json({
                "type": "sample_captured",
                "count": len(templates),
                "total": total_samples,
                "landmark_frames": landmark_count,
            })

        # ── Finalize ──────────────────────────────────────────────────────────
        store.add_sign(label, label_hindi, templates)
        await websocket.send_json({
            "type": "teaching_complete",
            "label": label,
            "label_hindi": label_hindi,
            "samples_recorded": len(templates),
        })
        logger.info(f"Teach session complete: {label}")

    except WebSocketDisconnect:
        logger.info("Teach WebSocket disconnected")
    except Exception as e:
        logger.error(f"Teach session error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
