from pydantic import BaseModel
from typing import Optional, List


class PredictionAlternative(BaseModel):
    label: str
    label_hindi: Optional[str] = None
    confidence: float


class PredictionResult(BaseModel):
    label: str
    label_hindi: Optional[str] = None
    confidence: float
    mode: str
    model_used: str
    landmarks_detected: bool
    alternatives: List[PredictionAlternative] = []


class RecognizeImageRequest(BaseModel):
    mode: Optional[str] = "auto"


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    result: Optional[dict] = None
    error: Optional[str] = None
