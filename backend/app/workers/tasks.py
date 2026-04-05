import cv2
import numpy as np
import json
from loguru import logger
from app.workers.celery_app import celery_app
from app.services.recognizer import get_recognizer
from app.services.translator import translate_to_hindi


@celery_app.task(bind=True, max_retries=3)
def process_video_task(self, job_id: str, file_path: str, mode: str):
    from app.database import AsyncSessionLocal
    from app.models.job import ProcessingJob
    from sqlalchemy import select
    import asyncio

    async def _process():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                return
            job.status = "processing"
            await db.commit()
            try:
                cap = cv2.VideoCapture(file_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                sample_every = max(1, int(fps / 15))
                recognizer = get_recognizer()
                transcript = []
                frame_buffer = []
                frame_count = 0
                processed = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame_count += 1
                    if frame_count % sample_every == 0:
                        frame_buffer.append(frame)
                        processed += 1
                        if len(frame_buffer) == 45:
                            result_pred = recognizer.predict_dynamic(frame_buffer)
                            if result_pred.confidence > 0.65 and result_pred.label != "—":
                                timestamp_ms = int((frame_count / fps) * 1000)
                                transcript.append({
                                    "timestamp_ms": timestamp_ms,
                                    "timestamp_str": f"{timestamp_ms // 60000}:{(timestamp_ms % 60000) // 1000:02d}",
                                    "label": result_pred.label,
                                    "label_hindi": result_pred.label_hindi or translate_to_hindi(result_pred.label),
                                    "confidence": result_pred.confidence
                                })
                            frame_buffer = frame_buffer[22:]
                        progress = min(0.99, processed / max(1, total_frames / sample_every))
                        job.progress = progress
                        await db.commit()
                cap.release()
                job.status = "completed"
                job.progress = 1.0
                job.result_json = json.dumps({"transcript": transcript, "total_signs": len(transcript)})
                await db.commit()
            except Exception as e:
                logger.error(f"Video processing failed: {e}")
                job.status = "failed"
                job.error_message = str(e)
                await db.commit()
                raise

    asyncio.run(_process())
