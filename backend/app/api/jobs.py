from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.job import ProcessingJob
import json

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result_data = None
    if job.result_json:
        result_data = json.loads(job.result_json)
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "result": result_data,
        "error": job.error_message
    }
