"""PlebChat Backend - FastAPI application for ecash payment handling.

This backend provides endpoints for:
- Receiving and validating ecash tokens from the LangGraph agent
- Storing redeemed tokens in a local wallet
- Admin operations (stats, withdrawal, sweep) with NIP-98 authentication
- Automatic periodic payouts to Lightning address

REQUIRED Environment Variables:
- WALLET_MNEMONIC: BIP39 mnemonic for the Cashu wallet (12 or 24 words)
- ADMIN_NPUBS: Comma-separated list of admin npubs or hex pubkeys

OPTIONAL Environment Variables:
- CASHU_MINT_URL: URL of the Cashu mint (default: https://mint.minibits.cash/Bitcoin)
- TRUSTED_MINTS: Comma-separated list of additional trusted mint URLs
- PAYOUT_LN_ADDRESS: Lightning address for automatic payouts (e.g., user@getalby.com)
- PAYOUT_THRESHOLD_SATS: Minimum balance to trigger payout (default: 1000)
- PAYOUT_INTERVAL_SECONDS: Payout check interval (default: 300 = 5 min)
- FRONTEND_URL: URL of the frontend for CORS
- HOST: Host to bind to (default: 0.0.0.0)
- PORT: Port to bind to (default: 8000)
"""

import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.routes.wallet import router as wallet_router
from src.routes.admin import router as admin_router
from src.services.cashu import CashuService, CashuServiceError
from src.auth.nip98 import get_admin_pubkeys

# Load environment variables
load_dotenv()


def validate_configuration() -> list[str]:
    """Validate all required configuration on startup.
    
    Returns:
        List of error messages (empty if all valid)
    """
    errors = []
    
    # Check WALLET_MNEMONIC
    mnemonic = os.getenv("WALLET_MNEMONIC", "").strip()
    if not mnemonic:
        errors.append(
            "WALLET_MNEMONIC is required. Generate one with:\n"
            "  python -c \"from mnemonic import Mnemonic; print(Mnemonic('english').generate())\""
        )
    else:
        word_count = len(mnemonic.split())
        if word_count not in (12, 24):
            errors.append(f"WALLET_MNEMONIC should be 12 or 24 words, got {word_count}")
    
    # Check ADMIN_NPUBS
    admin_npubs = get_admin_pubkeys()
    if not admin_npubs:
        errors.append(
            "ADMIN_NPUBS is required. Set it to a comma-separated list of admin npubs:\n"
            "  ADMIN_NPUBS=npub1abc...,npub1xyz..."
        )
    
    return errors


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    logger.info("[Backend] Starting up...")
    
    # Validate configuration BEFORE starting
    config_errors = validate_configuration()
    if config_errors:
        logger.error("[Backend] Configuration errors detected:")
        for error in config_errors:
            logger.error(f"  - {error}")
        logger.error("[Backend] Please fix the configuration and restart.")
        sys.exit(1)
    
    # Log admin configuration
    admin_npubs = get_admin_pubkeys()
    logger.info(f"[Backend] Configured {len(admin_npubs)} admin pubkey(s)")
    for npub in admin_npubs[:3]:  # Show first 3
        if npub.startswith("npub"):
            logger.info(f"[Backend]   - {npub[:24]}...")
        else:
            logger.info(f"[Backend]   - {npub[:16]}...")
    if len(admin_npubs) > 3:
        logger.info(f"[Backend]   ... and {len(admin_npubs) - 3} more")
    
    # Initialize the Cashu wallet service
    try:
        cashu_service = CashuService(require_mnemonic=True)
        await cashu_service.initialize()
        app.state.cashu_service = cashu_service
        logger.info("[Backend] Cashu wallet service initialized")
        
        # Start periodic payout task if configured
        await cashu_service.start_payout_task()
        
    except CashuServiceError as e:
        logger.error(f"[Backend] Failed to initialize Cashu service: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("[Backend] Shutting down...")
    
    # Stop periodic payout task
    if hasattr(app.state, 'cashu_service') and app.state.cashu_service:
        await app.state.cashu_service.stop_payout_task()


app = FastAPI(
    title="PlebChat Backend",
    description="Backend service for ecash payment validation, redemption, and admin operations",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
origins = [
    "http://localhost:5173",  # SvelteKit dev server
    "http://localhost:4173",  # SvelteKit preview
    "http://localhost:5174",  # Admin frontend dev server
    "http://localhost:5175",  # Admin frontend dev server (fallback port)
    "http://localhost:2024",  # LangGraph dev server
    os.getenv("FRONTEND_URL", ""),
    os.getenv("ADMIN_FRONTEND_URL", ""),
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
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])


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
    
    # Validate configuration before starting
    config_errors = validate_configuration()
    if config_errors:
        print("\n[ERROR] Configuration errors detected:\n")
        for error in config_errors:
            print(f"  ✗ {error}\n")
        print("Please fix the configuration and restart.\n")
        sys.exit(1)
    
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
