"""
FastAPI Application Entry Point

Main application setup with CORS, routers, lifecycle events, and health check.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import upload, query


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

    try:
        from app.services.database import get_database, close_database
        await get_database()
        print("✅ Connected to MongoDB Atlas")
        print("✅ Database indexes created")
        print("✅ Application started successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("⚠️ App is running but database features may not work")
        print("⚠️ Please check: MONGODB_URI env var and MongoDB Atlas connectivity")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    try:
        from app.services.database import close_database
        await close_database()
    except Exception as e:
        print(f"⚠️ Error during shutdown: {e}")
    print("👋 Goodbye!")


# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Intelligent Data Room API",
    description="Multi-agent AI system for data analysis using LangGraph and Gemini",
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
