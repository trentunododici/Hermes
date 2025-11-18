from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from src.database.connection import get_db
from src.services.user import add_user
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas.auth import AuthResponse, Token, LoginRequest, RefreshRequest, MessageResponse
from src.schemas.user import UserCreate
from src.services.auth import authenticate_user, verify_refresh_token, create_and_store_tokens 
from src.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from src.rate_limiter import limiter
from src.repositories.refresh_token_repository import RefreshTokenRepository

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/token",
            response_model=Token,
            summary="Get access token",
            description="Obtain an access token by providing valid user credentials."
                        "Primarily intended for internal use and Swagger UI documentation."
                        "Mobile clients should use the /login endpoint instead.",
)
@limiter.limit("10/minute")
async def get_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token, refresh_token = create_and_store_tokens(
        db=session,
        user_uuid=user.uuid,
        refresh_expires=refresh_token_expires,
        access_expires=access_token_expires
    )

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/login",
            status_code=status.HTTP_200_OK,
            response_model=AuthResponse,
            summary="User Login",
            description="Authenticate user and obtain an access token.",
            response_description="Returns access token and user UUID",
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "Incorrect username or password"},
                status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"}
            }
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    session: Session = Depends(get_db)
) -> AuthResponse:
    user = authenticate_user(session, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token, refresh_token = create_and_store_tokens(
        db=session,
        user_uuid=user.uuid,
        refresh_expires=refresh_token_expires,
        access_expires=access_token_expires
    )

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        uuid=user.uuid
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthResponse,
    summary="User Registration",
    description="Register a new user in the system.",
    response_description="Returns access token and user UUID",
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "User already exists"
            },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded"
            }    
    }
)
@limiter.limit("10/hour")
async def register(
    request: Request,
    user_create: UserCreate,
    session: Session = Depends(get_db),
) -> AuthResponse:
    user = add_user(session=session, **user_create.model_dump())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token, refresh_token = create_and_store_tokens(
        db=session,
        user_uuid=user.uuid,
        refresh_expires=refresh_token_expires,
        access_expires=access_token_expires
    )

    return AuthResponse(
        uuid=user.uuid,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    summary="Refresh Access Token",
    description="Obtain a new access token using a valid refresh token. "
                "The old refresh token will be revoked and a new one issued (token rotation).",
    response_description="Returns new access token and refresh token",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired refresh token"
            },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded"
            }
    }
)
@limiter.limit("10/minute")
async def refresh_token_endpoint(
    request: Request,
    refresh_request: RefreshRequest,
    session: Session = Depends(get_db),
) -> Token:
    result = verify_refresh_token(session, refresh_request.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "bearer"},
        )
    user, old_jti = result

    RefreshTokenRepository.revoke_by_jti(session, old_jti)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token, new_refresh_token = create_and_store_tokens(
        db=session,
        user_uuid=user.uuid,
        refresh_expires=refresh_token_expires,
        access_expires=access_token_expires
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="User Logout",
    description="Revoke the refresh token to invalidate the session.",
    response_description="Confirmation message of successful logout",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired refresh token"
            },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded"
            }
    }
)
@limiter.limit("10/minute")
async def logout(
    request: Request,
    refresh_request: RefreshRequest,
    session: Session = Depends(get_db),
) -> MessageResponse:
    # Verify refresh token is valid
    result = verify_refresh_token(session, refresh_request.refresh_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "bearer"},
        )
    _, jti = result
    
    RefreshTokenRepository.revoke_by_jti(session, jti)

    return MessageResponse(
        message="User logged out successfully"
    )
