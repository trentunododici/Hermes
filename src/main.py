from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from src.routers import auth, users
from src.database.connection import create_db_and_tables, get_db
from src.database.models import UserDB  # Ensure models are imported
from src.config import ENV
from sqlmodel import Session, literal, select
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.routers.auth import limiter
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan function to handle startup and shutdown events."""
    create_db_and_tables()
    yield
    # Here you can add code to run on application shutdown

app = FastAPI(
    title="Hermes API",
    description="API for Hermes application",
    version="1.0.0",
    lifespan=lifespan
)

# Security Middlewares
# Only enforce HTTPS in production to allow local development
if ENV == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    print("HTTPS enforcement enabled (production mode)")

    # Optionally add TrustedHostMiddleware to prevent host header attacks
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
    if allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
        print(f"✓ Trusted host middleware enabled: {allowed_hosts}")

# Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore[arg-type]

app.include_router(auth.router)
app.include_router(users.router)

@app.exception_handler(HTTPException)
async def global_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.get("/health", tags=["monitoring"], summary="Health Check", description="Check the health status of the API.")
async def health_check(session: Session = Depends(get_db)):
    try:
        # Simple query to check database connectivity
        session.exec(select(literal(1)))
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service unavailable") from e
