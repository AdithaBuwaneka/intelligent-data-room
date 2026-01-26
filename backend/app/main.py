"""
FastAPI Application Entry Point

Main application setup with CORS, routers, lifecycle events, and health check.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import upload, query
from app.services.database import get_database, close_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.

    Handles startup and shutdown events:
    - Startup: Connect to MongoDB
    - Shutdown: Close MongoDB connection
    """
    # Startup
    print("🚀 Starting Intelligent Data Room API...")
    await get_database()
    print("✅ Application started successfully")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await close_database()
    print("👋 Goodbye!")


# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Intelligent Data Room API",
    description="Multi-agent AI system for data analysis using LangGraph and PandasAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(query.router, prefix="/api", tags=["query"])


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "intelligent-data-room-api",
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Intelligent Data Room API",
        "description": "AI-powered data analysis with multi-agent system",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "upload": "POST /api/upload",
            "query": "POST /api/query",
            "history": "GET /api/history/{session_id}",
        },
    }
