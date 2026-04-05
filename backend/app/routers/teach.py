from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.custom_sign_store import get_custom_sign_store

router = APIRouter()


class DeleteRequest(BaseModel):
    label: str


@router.get("/teach/signs")
def list_custom_signs():
    """List all user-taught custom signs."""
    store = get_custom_sign_store()
    return {"signs": store.list_signs(), "count": len(store.list_signs())}


@router.delete("/teach/signs/{label}")
def delete_custom_sign(label: str):
    """Delete a user-taught custom sign."""
    store = get_custom_sign_store()
    if not store.delete_sign(label):
        raise HTTPException(status_code=404, detail=f"Sign '{label}' not found")
    return {"message": f"Sign '{label}' deleted successfully"}
