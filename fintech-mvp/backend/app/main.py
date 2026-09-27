from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
import os
from .routers import auth_router, transactions, analytics, planning, experimental

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Personal Finance Platform — v1")

# CORS: comma-separated allowlist in prod, "*" only in local dev.
# ALLOWED_ORIGINS=https://yourapp.com,https://staging.yourapp.com
_origins_env = os.getenv("ALLOWED_ORIGINS")
allow_origins = _origins_env.split(",") if _origins_env else (
    ["*"] if os.getenv("ENV", "development") == "development" else []
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(planning.router)

# Phase 5 is opt-in: off by default, matching the roadmap's gating.
# Set ENABLE_EXPERIMENTAL=true to mount it.
if os.getenv("ENABLE_EXPERIMENTAL", "false").lower() == "true":
    app.include_router(experimental.router)


@app.get("/health")
def health():
    return {"status": "ok"}
