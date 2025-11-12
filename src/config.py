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
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
