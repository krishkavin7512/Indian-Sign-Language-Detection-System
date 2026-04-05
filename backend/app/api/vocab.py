from fastapi import APIRouter, Query
from pathlib import Path
import json

router = APIRouter()

VOCAB_PATH = Path("../ml/models/dynamic_classifier/label_map.json")


@router.get("/vocab")
async def get_vocabulary(
    category: str = Query(None),
    search: str = Query(None),
    limit: int = Query(100)
):
    vocab = []
    if VOCAB_PATH.exists():
        with open(VOCAB_PATH) as f:
            label_map = json.load(f)
        vocab = [{"id": k, "label": v, "category": "general"} for k, v in label_map.items()]
    if search:
        vocab = [w for w in vocab if search.lower() in w["label"].lower()]
    if category:
        vocab = [w for w in vocab if w["category"] == category]
    return {"total": len(vocab), "words": vocab[:limit]}
