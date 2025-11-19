"""Unit tests for dependencies (src/utils/dependencies.py)."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from fastapi import HTTPException

from src.utils.dependencies import get_current_user, get_current_active_user
from src.services.auth import create_access_token, create_refresh_token
from src.schemas.user import User


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    @patch('src.utils.dependencies.get_user_by_uuid')
    async def test_get_current_user_success(self, mock_get_user):
        """Should return user when token is valid."""
        mock_session = Mock()
        mock_user = User(
            id=1,
            uuid="550e8400-e29b-41d4-a716-446655440000",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            disabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user

        # Create valid access token
        token = create_access_token(data={"sub": "550e8400-e29b-41d4-a716-446655440000"})

        result = await get_current_user(token=token, session=mock_session)

        assert result == mock_user
        mock_get_user.assert_called_once_with(mock_session, uuid="550e8400-e29b-41d4-a716-446655440000")

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Should raise 401 for invalid token."""
        mock_session = Mock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalid.token.here", session=mock_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_refresh_token_rejected(self):
        """Should raise 401 when using refresh token instead of access token."""
        mock_session = Mock()

        # Create refresh token (wrong type)
        refresh_token, _, _ = create_refresh_token(data={"sub": "550e8400-e29b-41d4-a716-446655440000"})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=refresh_token, session=mock_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub(self):
        """Should raise 401 when token has no subject."""
        mock_session = Mock()

        # Create token without sub
        token = create_access_token(data={})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, session=mock_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_uuid_format(self):
        """Should raise 401 when UUID format is invalid."""
        mock_session = Mock()

        # Create token with invalid UUID
        token = create_access_token(data={"sub": "not-a-valid-uuid"})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, session=mock_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch('src.utils.dependencies.get_user_by_uuid')
    async def test_get_current_user_user_not_found(self, mock_get_user):
        """Should raise 401 when user doesn't exist."""
        mock_session = Mock()
        mock_get_user.return_value = None

        token = create_access_token(data={"sub": "550e8400-e29b-41d4-a716-446655440000"})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, session=mock_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """Should raise 401 for expired token."""
        mock_session = Mock()

        # Create expired token
        from datetime import timedelta
        token = create_access_token(
            data={"sub": "550e8400-e29b-41d4-a716-446655440000"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, session=mock_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_wrong_signature(self):
        """Should raise 401 for token with wrong signature."""
        mock_session = Mock()

        # Create token and tamper with it
        token = create_access_token(data={"sub": "550e8400-e29b-41d4-a716-446655440000"})
        # Modify the signature part
        parts = token.split('.')
        parts[2] = 'tampered_signature'
        tampered_token = '.'.join(parts)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=tampered_token, session=mock_session)

        assert exc_info.value.status_code == 401


class TestGetCurrentActiveUser:
    """Tests for get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self):
        """Should return user when user is active."""
        mock_user = User(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            disabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        result = await get_current_active_user(current_user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_active_user_disabled(self):
        """Should raise 403 when user is disabled."""
        mock_user = User(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            disabled=True,  # User is disabled
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=mock_user)

        assert exc_info.value.status_code == 403
        assert "Inactive user" in exc_info.value.detail
