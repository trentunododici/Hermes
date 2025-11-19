import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

def get_required_env_var(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise ValueError("Configuration error - check logs")
    return value
DATABASE_URL = get_required_env_var("DATABASE_URL")
ENV = os.getenv("ENV", "development")
SECRET_KEY = get_required_env_var("SECRET_KEY")
REFRESH_SECRET_KEY = get_required_env_var("REFRESH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_ACTIVE_TOKENS_PER_USER = int(os.getenv("MAX_ACTIVE_TOKENS_PER_USER", "5"))
# JWT Claims
JWT_ISSUER = os.getenv("JWT_ISSUER", "hermes-api")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "hermes-mobile-app")
