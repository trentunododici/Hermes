from pydantic import BaseModel, field_validator

from src.utils.validators import normalize_username

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def normalize_username_field(cls, v: str) -> str:
        return normalize_username(v)

class AuthResponse(Token):
    uuid: str