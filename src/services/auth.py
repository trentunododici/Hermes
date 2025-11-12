from datetime import datetime, timedelta, timezone
import jwt
from sqlmodel import Session
from src.config import SECRET_KEY, ALGORITHM
from src.utils.security import verify_password
from src.services.user import get_user
from src.schemas.user import User

def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate user and return User WITHOUT password.
    Implements timing attack mitigation by always performing password verification,
    regardless of whether the user exists or not.
    """
    user_with_password = get_user(db, username)

    # Use realistic dummy hash if user doesn't exist to maintain constant timing
    # This prevents attackers from distinguishing "user not found" vs "wrong password"
    # The dummy hash is a real argon2id hash, ensuring verification takes similar time
    hashed_password = (
        user_with_password.hashed_password
        if user_with_password
        else "$argon2id$v=19$m=65536,t=3,p=4$owhEzyl8AD7mt/kgiE9Teg$yr8YHFdTrbvr1TdNYTU0I3bTjKw6BPN4FKqkHPNOxpo"
    )

    # Always verify password, even if user doesn't exist (constant-time operation)
    if not verify_password(password, hashed_password):
        return None

    # If we reach here, password was correct, but user might still not exist
    if not user_with_password:
        return None

    # Convert UserInDB to User using model_validate (excludes hashed_password automatically)
    return User.model_validate(user_with_password, from_attributes=True)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)
    to_encode.update({
        "sub": data.get("sub"),
        "exp": expire,
        "iat": now,
        "iss": "hermes-api",
        "aud": "hermes-mobile-app"
        })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt