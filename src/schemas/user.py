from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

from src.utils.validators import validate_password, validate_username

class UserCreate(BaseModel):
    """Schema for creating a new user (includes password and validations)"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str

    @field_validator('username')
    @classmethod
    def validate_username_field(cls, value) -> str:
        return validate_username(value)

    @field_validator('password')
    @classmethod
    def validate_password_field(cls, value) -> str:
        return validate_password(value)

class UserInDB(BaseModel):
    """Schema for user with hashed password - ONLY for internal authentication"""
    id: int
    uuid: str
    username: str
    email: str
    full_name: Optional[str] = None
    hashed_password: str
    disabled: bool

    class Config:
        from_attributes = True

class User(BaseModel):
    """Schema for user WITHOUT password - safe for dependencies and internal use"""
    id: int
    uuid: str
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: bool

    class Config:
        from_attributes = True
