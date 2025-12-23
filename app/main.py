from fastapi import FastAPI
from app.core.logging import configure_logging
from app.api.routes_chat import router as chat_router
from app.api.routes_admin import router as admin_router
from app.api.routes_logs import router as logs_router
from app.api.routes_products import router as products_router
from app.api.routes_admin_planner import router as admin_planner_router
from app.api.routes_users import router as users_router
from app.api.routes_sessions import router as sessions_router
from app.api.routes_traces import router as traces_router
from app.api.routes_audit import router as audit_router
from app.api.routes_frontend import router as frontend_router
from app.api.routes_observability import router as observability_router
from app.api.routes_ui_timeline import router as ui_timeline_router
from app.api.routes_ui_audit import router as ui_audit_router
from app.api.routes_ui_users import router as ui_users_router

configure_logging()
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="SentinelFlow", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(logs_router)
app.include_router(products_router)
app.include_router(admin_planner_router)
app.include_router(users_router)
app.include_router(sessions_router)
app.include_router(traces_router)
app.include_router(audit_router)
app.include_router(frontend_router)
app.include_router(observability_router)
app.include_router(ui_timeline_router)
app.include_router(ui_audit_router)
app.include_router(ui_users_router)

@app.get("/health")
def health():
    return {"status": "ok"}
