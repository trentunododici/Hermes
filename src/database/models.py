from sqlmodel import SQLModel, Field
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
    full_name: Optional[str] = Field(default=None, max_length=255)
    hashed_password: str = Field(max_length=255)
    disabled: bool = Field(default=False)
