from fastapi import APIRouter

router = APIRouter(tags=["logs"])

@router.get("/logs/{trace_id}")
def get_logs(trace_id: str):
    return {"trace_id": trace_id, "status": "todo: return trace details"}
