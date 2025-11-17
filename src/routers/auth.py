from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from src.database.connection import get_db
from src.services.user import add_user
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas.auth import AuthResponse, Token, LoginRequest
from src.schemas.user import UserCreate
from src.services.auth import authenticate_user, create_access_token
from src.config import ACCESS_TOKEN_EXPIRE_MINUTES
from src.rate_limiter import limiter

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
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.uuid},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

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
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.uuid},
        expires_delta=access_token_expires
    )

    return AuthResponse(
        access_token=access_token,
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
    },
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
    access_token = create_access_token(
        data={"sub": user.uuid},
        expires_delta=access_token_expires
    )

    user_response = AuthResponse(
        uuid=user.uuid,
        access_token=access_token,
        token_type="bearer"
    )
    return user_response
