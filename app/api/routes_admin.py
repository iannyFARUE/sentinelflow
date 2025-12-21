from fastapi import APIRouter

router = APIRouter(tags=["admin"])

@router.post("/admin/seed")
def seed():
    return {"status": "todo: seed synthetic data"}
