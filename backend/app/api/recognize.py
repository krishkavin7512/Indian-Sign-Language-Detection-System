import cv2
import numpy as np
import uuid
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.database import get_db
from app.services.recognizer import get_recognizer
from app.models.job import ProcessingJob
from app.workers.tasks import process_video_task
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/recognize/image")
async def recognize_image(
    file: UploadFile = File(...),
    mode: str = Form("auto"),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=422, detail="Only JPEG, PNG, WebP images accepted")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large. Max 5MB")
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=422, detail="Could not decode image")
    recognizer = get_recognizer()
    if mode in ["alphabet", "number", "auto"]:
        result = recognizer.predict_static(frame)
    else:
        raise HTTPException(status_code=400, detail="Use /recognize/video for video-based modes")
    return result


@router.post("/recognize/video")
async def recognize_video(
    file: UploadFile = File(...),
    mode: str = Form("auto"),
    db: AsyncSession = Depends(get_db)
):
    allowed_types = ["video/mp4", "video/avi", "video/mov", "video/webm", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=422, detail="Only MP4, AVI, MOV, WebM accepted")
    contents = await file.read()
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(status_code=413, detail=f"Video too large. Max {settings.max_upload_size_mb}MB")
    os.makedirs(settings.upload_dir, exist_ok=True)
    job_id = str(uuid.uuid4())
    file_path = os.path.join(settings.upload_dir, f"{job_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(contents)
    job = ProcessingJob(id=job_id, file_path=file_path, status="queued")
    db.add(job)
    await db.commit()
    process_video_task.delay(job_id, file_path, mode)
    return {"job_id": job_id, "status": "queued", "message": "Video is being processed"}
