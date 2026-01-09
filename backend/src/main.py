"""PlebChat Backend - FastAPI application for ecash payment handling.

This backend provides endpoints for:
- Receiving and validating ecash tokens from the LangGraph agent
- Storing redeemed tokens in a local wallet
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.wallet import router as wallet_router
from src.services.cashu import CashuService

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Initialize the Cashu wallet service
    print("[Backend] Starting up...")
    cashu_service = CashuService()
    await cashu_service.initialize()
    app.state.cashu_service = cashu_service
    print("[Backend] Cashu wallet service initialized")
    
    yield
    
    # Shutdown
    print("[Backend] Shutting down...")


app = FastAPI(
    title="PlebChat Backend",
    description="Backend service for ecash payment validation and redemption",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
origins = [
    "http://localhost:5173",  # SvelteKit dev server
    "http://localhost:4173",  # SvelteKit preview
    "http://localhost:2024",  # LangGraph dev server
    os.getenv("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(wallet_router, prefix="/api/wallet", tags=["wallet"])


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "service": "plebchat-backend"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the application with uvicorn."""
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
