import uuid as uuid_lib
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session
from src.config import SECRET_KEY, ALGORITHM
from src.schemas.user import User
from src.services.user import get_user_by_uuid
from src.database.connection import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="hermes-mobile-app",
            issuer="hermes-api"
        )
        uuid_str: str = payload.get("sub")
        if uuid_str is None:
            raise credentials_exception

        try:
            uuid_lib.UUID(uuid_str)
        except ValueError:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    user = get_user_by_uuid(session, uuid=uuid_str)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user
