from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup and shutdown preparation"""
    # Startup: logging, vertex ai credentials pre-check, etc.
    print(f"🚀 [Safar 360 Backend] Initializing FastAPI server (v{settings.VERSION})...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print(f"📦 [Safar 360 Backend] Database models synchronized.")

    print(f"📡 [Safar 360 Backend] CORS enabled for: {settings.BACKEND_CORS_ORIGINS}")
    print(f"🧠 [Safar 360 Backend] Vertex AI configuration target: {settings.VERTEX_AI_MODEL} ({settings.VERTEX_AI_LOCATION})")
    yield
    # Shutdown cleanup if needed
    print("🛑 [Safar 360 Backend] Shutting down server gracefully...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS Middleware for seamless Frontend SPA communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Accel-Buffering"],
)

# Register API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    tags=["Root"],
    summary="API Root Information",
    description="Returns service metadata and available API endpoints."
)
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "routes": {
            "characters": f"{settings.API_V1_STR}/characters",
            "chat_completions": f"{settings.API_V1_STR}/chat/completions",
            "health": "/health",
        },
        "vertex_ai_readiness": {
            "project": settings.GOOGLE_CLOUD_PROJECT,
            "location": settings.VERTEX_AI_LOCATION,
            "target_model": settings.VERTEX_AI_MODEL,
            "phase": "Phase 5 (Database & Monetization)"
        }
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check Probe",
    description="Endpoint for container probes and dev-server health monitoring."
)
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
