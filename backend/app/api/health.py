from fastapi import APIRouter
from app.services.recognizer import get_recognizer

router = APIRouter()


@router.get("/health")
async def health_check():
    recognizer = get_recognizer()
    return {
        "status": "ok",
        "models_loaded": recognizer.models_loaded,
        "static_model": recognizer.static_model is not None,
        "dynamic_model": recognizer.dynamic_model is not None,
        "sentence_model": recognizer.sentence_model is not None,
        "version": "1.0.0"
    }
