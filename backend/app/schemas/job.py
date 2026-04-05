from pydantic import BaseModel
from typing import Optional


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    result: Optional[dict] = None
    error: Optional[str] = None
