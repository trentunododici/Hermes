"""Test environment configuration.

These values are defaults for local development.
In CI, environment variables are set by the workflow and take precedence.
"""
import os

# Use setdefault to allow CI workflow env vars to take precedence
os.environ.setdefault("ENV", "testing")
os.environ.setdefault("DATABASE_URL", "postgresql://hermes_user:test_password@localhost:5433/hermes_test")
os.environ.setdefault("SECRET_KEY", "test_secret_key_fallback")
os.environ.setdefault("REFRESH_SECRET_KEY", "test_refresh_secret_key_fallback")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("MAX_ACTIVE_TOKENS_PER_USER", "3")