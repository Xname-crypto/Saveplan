from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import init_auth_db, router as auth_router
from .config import CORS_ORIGINS
from .conversions import init_conversion_db, router as conversions_router

app = FastAPI(
    title="Save Your Finals API",
    description="Backend API scaffold for the Vue frontend.",
    version="0.1.0",
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
