from datetime import datetime, timedelta, timezone
import uuid
import jwt
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session
from src.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_SECRET_KEY, SECRET_KEY, ALGORITHM, JWT_ISSUER, JWT_AUDIENCE, MAX_ACTIVE_TOKENS_PER_USER, REFRESH_TOKEN_EXPIRE_DAYS
from src.schemas.auth import TokenType
from src.utils.security import verify_password, hash_token
from src.utils.validators import normalize_username
from src.services.user import get_user, get_user_by_uuid
from src.schemas.user import User
from src.repositories.refresh_token_repository import RefreshTokenRepository


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate user and return User WITHOUT password.
    Implements timing attack mitigation by always performing password verification,
    regardless of whether the user exists or not.
    Normalizes username to ensure consistent behavior across /login and /token endpoints.
    """
    try:
        normalized_username = normalize_username(username)
        user_with_password = get_user(db, normalized_username)
    except ValueError:
        user_with_password = None

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
    
    if user_with_password.disabled:
        return None

    # Convert UserInDB to User using model_validate (excludes hashed_password automatically)
    return User.model_validate(user_with_password, from_attributes=True)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "type": TokenType.ACCESS,
        "exp": expire,
        "iat": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE
        })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> tuple[str, str, datetime]:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid.uuid4())
    to_encode.update({
        "type": TokenType.REFRESH,
        "jti": jti,
        "exp": expire,
        "iat": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE
        })
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire

def verify_refresh_token(db: Session, token: str) -> tuple[User, str] | None:
    """
    Verify a refresh token and return the associated user.

    Validates:
    - JWT signature and expiration
    - Token type (must be REFRESH)
    - JTI exists in database
    - Token is not revoked
    - Token hash matches
    - User exists and is active

    Returns User and jti if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            REFRESH_SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER
        )
    except InvalidTokenError:
        return None

    if payload.get("type") != TokenType.REFRESH:
        return None

    user_uuid: str = payload.get("sub")
    jti: str = payload.get("jti")

    if not user_uuid or not jti:
        return None

    # Verify token exists in database and is valid (not revoked, not expired)
    token_record = RefreshTokenRepository.get_valid_token_by_jti(db, jti)
    if not token_record:
        return None
        
    # Ensure the DB record belongs to the same user as the JWT subject
    if token_record.user_uuid != user_uuid:
        return None

    # Verify token hash matches (prevents token theft from DB)
    token_hash_calculated = hash_token(token)
    if token_record.token_hash != token_hash_calculated:
        return None

    # Verify user exists and is active
    user = get_user_by_uuid(db, user_uuid)
    if not user or user.disabled:
        return None

    return user, jti

    
    
def create_and_store_tokens(
        db: Session,
        user_uuid: str,
        access_expires: timedelta,
        refresh_expires: timedelta
    ) -> tuple[str, str]:

    active_count = RefreshTokenRepository.count_active_tokens_for_user(db, user_uuid)
    if active_count >= MAX_ACTIVE_TOKENS_PER_USER:
        RefreshTokenRepository.revoke_oldest_tokens(db, user_uuid)

    access_token = create_access_token(
        data={"sub": user_uuid},
        expires_delta=access_expires
    )
    refresh_token, jti, expire = create_refresh_token(
        data={"sub": user_uuid},
        expires_delta=refresh_expires
    )

    # Store hashed token in database
    token_hash = hash_token(refresh_token)
    RefreshTokenRepository.create(
        db=db,
        user_uuid=user_uuid,
        jti=jti,
        token_hash=token_hash,
        expires_at=expire
    )

    return access_token, refresh_token