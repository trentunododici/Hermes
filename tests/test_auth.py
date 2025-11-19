"""Tests for authentication endpoints."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.config import MAX_ACTIVE_TOKENS_PER_USER


class TestRegister:
    """Tests for POST /api/v1/auth/register"""

    def test_register_success(self, client: TestClient, test_user_data):
        """Successfully register a new user."""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "uuid" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self, client: TestClient, test_user, test_user_data):
        """Fail to register with duplicate username."""
        # test_user fixture already created user with same username
        new_user_data = test_user_data.copy()
        new_user_data["email"] = "different@example.com"

        response = client.post("/api/v1/auth/register", json=new_user_data)

        assert response.status_code == 409

    def test_register_duplicate_email(self, client: TestClient, test_user, test_user_data):
        """Fail to register with duplicate email."""
        new_user_data = test_user_data.copy()
        new_user_data["username"] = "differentuser"

        response = client.post("/api/v1/auth/register", json=new_user_data)

        assert response.status_code == 409

    def test_register_invalid_email(self, client: TestClient, test_user_data):
        """Fail to register with invalid email format."""
        test_user_data["email"] = "not-an-email"

        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 422

    def test_register_missing_fields(self, client: TestClient):
        """Fail to register with missing required fields."""
        incomplete_data = {"username": "test"}

        response = client.post("/api/v1/auth/register", json=incomplete_data)

        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client: TestClient, test_user, test_user_data):
        """Successfully login with valid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "uuid" in data
        assert data["token_type"] == "bearer"
        assert data["uuid"] == test_user.uuid

    def test_login_wrong_password(self, client: TestClient, test_user, test_user_data):
        """Fail to login with wrong password."""
        response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": "WrongPassword123!"
        })

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Fail to login with non-existent username."""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "SomePassword123!"
        })

        assert response.status_code == 401

    def test_login_case_insensitive_username(self, client: TestClient, test_user, test_user_data):
        """Login should work with different case username."""
        response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"].upper(),
            "password": test_user_data["password"]
        })

        assert response.status_code == 200

    def test_login_disabled_user(self, client: TestClient, test_user, test_user_data, session: Session):
        """Fail to login with disabled user account."""
        # Disable the user
        test_user.disabled = True
        session.add(test_user)
        session.commit()

        response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })

        assert response.status_code == 401


class TestToken:
    """Tests for POST /api/v1/auth/token (OAuth2 form endpoint)"""

    def test_token_success(self, client: TestClient, test_user, test_user_data):
        """Successfully get token via OAuth2 form."""
        response = client.post("/api/v1/auth/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_token_wrong_credentials(self, client: TestClient, test_user):
        """Fail to get token with wrong credentials."""
        response = client.post("/api/v1/auth/token", data={
            "username": "wronguser",
            "password": "wrongpassword"
        })

        assert response.status_code == 401


class TestRefresh:
    """Tests for POST /api/v1/auth/refresh"""

    def test_refresh_success(self, client: TestClient, test_user_tokens):
        """Successfully refresh tokens."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user_tokens["refresh_token"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different from old ones
        assert data["refresh_token"] != test_user_tokens["refresh_token"]

    def test_refresh_invalid_token(self, client: TestClient):
        """Fail to refresh with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })

        assert response.status_code == 401

    def test_refresh_revoked_token(self, client: TestClient, session: Session, test_user_tokens):
        """Fail to refresh with already revoked token."""
        # First, use the refresh token successfully
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user_tokens["refresh_token"]
        })
        assert response.status_code == 200

        # Try to use the old (now revoked) refresh token again
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user_tokens["refresh_token"]
        })

        assert response.status_code == 401

    def test_refresh_with_access_token(self, client: TestClient, test_user_tokens):
        """Fail to refresh using an access token instead of refresh token."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user_tokens["access_token"]
        })

        assert response.status_code == 401


class TestLogout:
    """Tests for POST /api/v1/auth/logout"""

    def test_logout_success(self, client: TestClient, test_user_tokens):
        """Successfully logout and revoke refresh token."""
        response = client.post("/api/v1/auth/logout", json={
            "refresh_token": test_user_tokens["refresh_token"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_logout_then_refresh_fails(self, client: TestClient, test_user_tokens):
        """After logout, refresh token should be invalid."""
        # Logout
        response = client.post("/api/v1/auth/logout", json={
            "refresh_token": test_user_tokens["refresh_token"]
        })
        assert response.status_code == 200

        # Try to refresh with the revoked token
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user_tokens["refresh_token"]
        })

        assert response.status_code == 401

    def test_logout_invalid_token(self, client: TestClient):
        """Fail to logout with invalid token."""
        response = client.post("/api/v1/auth/logout", json={
            "refresh_token": "invalid.token.here"
        })

        assert response.status_code == 401

    def test_logout_twice_fails(self, client: TestClient, test_user_tokens):
        """Second logout with same token should fail."""
        # First logout
        response = client.post("/api/v1/auth/logout", json={
            "refresh_token": test_user_tokens["refresh_token"]
        })
        assert response.status_code == 200

        # Second logout with same token
        response = client.post("/api/v1/auth/logout", json={
            "refresh_token": test_user_tokens["refresh_token"]
        })

        assert response.status_code == 401


class TestMaxActiveTokens:
    """Tests for maximum active tokens per user limit"""

    def test_max_tokens_revokes_oldest(self, client: TestClient, session: Session, test_user, test_user_data):
        """When max tokens reached, oldest should be revoked."""
        tokens = []

        # Create MAX_ACTIVE_TOKENS_PER_USER + 1 tokens
        for _ in range(MAX_ACTIVE_TOKENS_PER_USER + 1):
            response = client.post("/api/v1/auth/login", json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            })
            assert response.status_code == 200
            tokens.append(response.json()["refresh_token"])

        # Check that we still have only MAX_ACTIVE_TOKENS_PER_USER active
        active_count = RefreshTokenRepository.count_active_tokens_for_user(session, test_user.uuid)
        assert active_count == MAX_ACTIVE_TOKENS_PER_USER
