from pydantic import BaseModel, field_validator
from enum import Enum

from src.utils.validators import normalize_username

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"

class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def normalize_username_field(cls, v: str) -> str:
        return normalize_username(v)

class AuthResponse(Token):
    uuid: str

class RefreshRequest(BaseModel):
    refresh_token: str

class MessageResponse(BaseModel):
    message: str