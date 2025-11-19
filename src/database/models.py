from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Index
from typing import Optional
import uuid as uuid_lib

class UserDB(SQLModel, table=True):
    """
    Database model for the users table.
    Represents the structure of the table in the database.
    """
    __tablename__ = "users"  # type: ignore[assignment]:

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(
        default_factory=lambda: str(uuid_lib.uuid4()),
        unique=True,
        index=True,
        max_length=36
    )
    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(unique=True, max_length=255)
    first_name: Optional[str] = Field(default=None, max_length=255)
    last_name: Optional[str] = Field(default=None, max_length=255)
    hashed_password: str = Field(max_length=255)
    disabled: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

class RefreshTokenDB(SQLModel, table=True):
    """
    Database model for the refresh_tokens table.
    Represents the structure of the table in the database.
    """
    __tablename__ = "refresh_tokens"  # type: ignore[assignment]:
    __table_args__ = (
          Index('ix_refresh_tokens_user_revoked', 'user_uuid', 'revoked'),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    jti: str = Field(unique=True, index=True, max_length=36)
    token_hash: str = Field(index=True, max_length=64)
    user_uuid: str = Field(
        foreign_key="users.uuid", 
        index=True,
        max_length=36
    )
    expires_at: datetime = Field(nullable=False, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    revoked: bool = Field(default=False)
    revoked_at: Optional[datetime] = Field(default=None, index=True)
