"""
main.py — CETSure FastAPI Application (F3)

Serves as the main HTTP API server. Wraps the prediction engine
and historical database queries into structured JSON endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import predict, college
import os

# Initialize FastAPI application
app = FastAPI(
    title="CETSure Backend API",
    description="FastAPI backend serving prediction models and historical MHT-CET cutoff searches.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
# NEW

ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "http://localhost:5500"),  # fallback for local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization"],
)
# ---------------------------------------------------------------------------
# Routers registration
# ---------------------------------------------------------------------------
app.include_router(predict.router)
app.include_router(college.router)


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    status_code=200,
    tags=["system"],
    summary="API health status check",
)
async def health_check():
    """Confirms that the FastAPI server is running and responsive."""
    return {
        "status": "ok",
        "message": "CETSure API is running",
    }
