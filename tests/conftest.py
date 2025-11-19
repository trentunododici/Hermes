import tests.test_config  # noqa: F401 - must be first
import os
import pytest
import subprocess
import time
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from src.config import DATABASE_URL, ENV
from src.main import app
from src.database.connection import get_db
from src.services.user import add_user
from src.services.auth import create_and_store_tokens
from datetime import timedelta


def is_ci_environment():
    """Check if running in CI environment."""
    return os.getenv("CI") or os.getenv("GITHUB_ACTIONS")


@pytest.fixture(scope="session", autouse=True)
def docker_compose_up():
    """Start test database before tests, stop after.

    Skips docker-compose in CI where database is provided by service container.
    """
    # Skip in CI - database is provided by GitHub Actions service container
    if is_ci_environment():
        yield
        return

    # Local development: start docker-compose
    subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yaml", "up", "-d"],
        check=True
    )

    # Wait for database to be ready
    max_retries = 30
    for i in range(max_retries):
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yaml", "exec", "-T",
             "postgres-test", "pg_isready", "-U", "hermes_user", "-d", "hermes_test"],
            capture_output=True
        )
        if result.returncode == 0:
            break
        time.sleep(1)
    else:
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yaml", "down", "-v"])
        raise RuntimeError("Database did not become ready in time")

    yield

    subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yaml", "down", "-v"],
        check=True
    )


@pytest.fixture(name="engine", scope="module")
def engine_fixture():
    engine = create_engine(
        DATABASE_URL,
        echo=ENV == "development",
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    """Create a new database session for each test with transaction isolation."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with overridden database dependency."""
    def get_session_override():
        return session

    app.dependency_overrides[get_db] = get_session_override

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(name="test_user_data")
def test_user_data_fixture():
    """Standard test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePassword123!"
    }


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session, test_user_data):
    """Create a test user in the database."""
    user = add_user(
        session=session,
        username=test_user_data["username"],
        email=test_user_data["email"],
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
        password=test_user_data["password"]
    )
    return user


@pytest.fixture(name="test_user_tokens")
def test_user_tokens_fixture(session: Session, test_user):
    """Create access and refresh tokens for test user."""
    access_token, refresh_token = create_and_store_tokens(
        db=session,
        user_uuid=test_user.uuid,
        access_expires=timedelta(minutes=15),
        refresh_expires=timedelta(days=7)
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": test_user
    }


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user_tokens):
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {test_user_tokens['access_token']}"}


@pytest.fixture(name="second_user_data")
def second_user_data_fixture():
    """Data for a second test user."""
    return {
        "username": "seconduser",
        "email": "second@example.com",
        "first_name": "Second",
        "last_name": "User",
        "password": "AnotherSecure456!"
    }
