"""Tests for user endpoints."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.repositories.user_repository import UserRepository


class TestGetCurrentUser:
    """Tests for GET /api/v1/users/me"""

    def test_get_me_success(self, client: TestClient, auth_headers, test_user):
        """Successfully get current user info."""
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == test_user.uuid
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "hashed_password" not in data

    def test_get_me_no_token(self, client: TestClient):
        """Fail to get user info without token."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401

    def test_get_me_invalid_token(self, client: TestClient):
        """Fail to get user info with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401

    def test_get_me_refresh_token_rejected(self, client: TestClient, test_user_tokens):
        """Fail when using refresh token instead of access token."""
        headers = {"Authorization": f"Bearer {test_user_tokens['refresh_token']}"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401


class TestDeactivateUser:
    """Tests for DELETE /api/v1/users/me"""

    def test_deactivate_success(self, client: TestClient, session: Session, auth_headers, test_user):
        """Successfully deactivate current user."""
        response = client.delete("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verify user is disabled in database
        user_db = UserRepository.get_by_uuid(session, test_user.uuid)
        assert user_db is not None
        assert user_db.disabled is True

    def test_deactivate_no_token(self, client: TestClient):
        """Fail to deactivate without token."""
        response = client.delete("/api/v1/users/me")

        assert response.status_code == 401

    def test_deactivate_then_login_fails(self, client: TestClient, auth_headers, test_user_data):
        """After deactivation, login should fail."""
        # Deactivate
        response = client.delete("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200

        # Try to login
        response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })

        # Should fail because user is disabled
        assert response.status_code == 401

    def test_deactivate_then_get_me_fails(self, client: TestClient, auth_headers):
        """After deactivation, access token should be rejected."""
        # Deactivate
        response = client.delete("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200

        # Try to get user info with same token
        response = client.get("/api/v1/users/me", headers=auth_headers)

        # Should fail because user is disabled
        assert response.status_code == 403

    def test_permanent_delete_not_implemented(self, client: TestClient, auth_headers):
        """Permanent deletion returns 501."""
        response = client.delete("/api/v1/users/me", headers=auth_headers, params={"permanent": True})

        assert response.status_code == 501


class TestUserDataPrivacy:
    """Tests for user data privacy and security"""

    def test_password_not_returned(self, client: TestClient, auth_headers):
        """User response should never include password."""
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

    def test_cannot_access_other_users(self, client: TestClient, session: Session, auth_headers, second_user_data):
        """Users cannot access other users' data directly."""
        from src.services.user import add_user

        # Create second user
        second_user = add_user(session=session, **second_user_data)
        assert second_user is not None
        # Get /me only returns current user's data
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Should return first user's data, not second
        assert data["uuid"] != second_user.uuid


class TestHealthCheck:
    """Tests for health check endpoint"""

    def test_health_check(self, client: TestClient):
        """Health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
