"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings

# Import routers
from app.api import auth, accounts, categories, transactions, dashboard, budgets, reports, contacts, loans, recurring_transactions, tags, goals


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing needed, DB tables created via migrations
    yield
    # Shutdown: nothing needed
    pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal Finance Manager API",
    lifespan=lifespan
)

# CORS middleware
def _cors_origins():
    if settings.CORS_ORIGINS:
        return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    # Safe defaults for local UI dev hitting deployed API (bearer-token auth, no cookies)
    return ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(budgets.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(contacts.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")
app.include_router(recurring_transactions.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(goals.router, prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AIOA - Personal Finance Manager",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
