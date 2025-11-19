"""Test environment configuration.

These values match the CI workflow fallbacks for parity between local and CI runs.
"""
import os

os.environ["ENV"] = "testing"
os.environ["DATABASE_URL"] = "postgresql://hermes_user:test_password@localhost:5433/hermes_test"
os.environ["SECRET_KEY"] = "test_secret_key_fallback"
os.environ["REFRESH_SECRET_KEY"] = "test_refresh_secret_key_fallback"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["MAX_ACTIVE_TOKENS_PER_USER"] = "3"