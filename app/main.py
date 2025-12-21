from fastapi import FastAPI
from app.api.routes_chat import router as chat_router
from app.api.routes_admin import router as admin_router
from app.api.routes_logs import router as logs_router

app = FastAPI(title="SentinelFlow", version="0.1.0")

app.include_router(chat_router, prefix="")
app.include_router(admin_router, prefix="")
app.include_router(logs_router, prefix="")

@app.get("/health")
def health():
    return {"status": "ok"}
