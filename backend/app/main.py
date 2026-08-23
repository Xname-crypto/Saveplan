from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import init_auth_db, router as auth_router
from .config import CORS_ORIGINS
from .conversions import init_conversion_db, router as conversions_router
from .database.session import init_database
from .modules.admin_auth.controller import router as admin_auth_router
from .modules.admin_dashboard.controller import router as admin_dashboard_router
from .modules.admin_auth.service import bootstrap_admin_security
from .modules.broadcasts.controller import public_router as broadcasts_public_router
from .modules.broadcasts.controller import router as admin_broadcasts_router
from .modules.audit_logs.controller import router as audit_logs_router
from .modules.conversions.controller import router as admin_conversions_router
from .modules.orders.controller import router as orders_router
from .modules.rbac.controller import router as rbac_router
from .modules.redeem_codes.controller import public_router as redeem_codes_public_router
from .modules.redeem_codes.controller import router as redeem_codes_router
from .modules.users.controller import router as admin_users_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_database()
    bootstrap_admin_security()
    yield

app = FastAPI(
    title="Save Your Finals API",
    description="Backend API for Saveplan users and the RBAC admin console.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_auth_db()
init_conversion_db()
app.include_router(auth_router)
app.include_router(conversions_router)
app.include_router(orders_router)
app.include_router(admin_auth_router)
app.include_router(admin_dashboard_router)
app.include_router(rbac_router)
app.include_router(admin_users_router)
app.include_router(admin_conversions_router)
app.include_router(audit_logs_router)
app.include_router(redeem_codes_router)
app.include_router(redeem_codes_public_router)
app.include_router(admin_broadcasts_router)
app.include_router(broadcasts_public_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "save-your-finals-api",
    }


@app.get("/api/features")
async def list_features() -> dict[str, list[str]]:
    return {
        "features": [
            "file-upload",
            "ocr-parse",
            "ai-review",
            "app-ready-export",
        ],
    }
