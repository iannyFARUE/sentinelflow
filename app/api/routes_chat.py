from fastapi import APIRouter

router = APIRouter(tags=["chat"])

@router.post("/chat")
def chat():
    # placeholder: will call orchestrator next
    return {"message": "SentinelFlow chat endpoint is wired. Next: orchestrator."}
