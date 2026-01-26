"""
FastAPI Application Entry Point

Main application setup with CORS, routers, and health check.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import upload, query

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Intelligent Data Room API",
    description="Multi-agent AI system for data analysis using LangGraph and PandasAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
        "docs": "/docs",
        "health": "/health",
    }
