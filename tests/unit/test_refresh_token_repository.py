"""Unit tests for refresh token repository (src/repositories/refresh_token_repository.py)."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.database.models import RefreshTokenDB


class TestRefreshTokenRepositoryGetByJti:
    """Tests for RefreshTokenRepository.get_by_jti."""

    def test_get_by_jti_found(self):
        """Should return token when found."""
        mock_db = Mock()
        mock_token = RefreshTokenDB(
            id=1,
            jti="test-jti",
            token_hash="hash",
            user_uuid="user-uuid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=False
        )
        mock_db.exec.return_value.first.return_value = mock_token

        result = RefreshTokenRepository.get_by_jti(mock_db, "test-jti")

        assert result == mock_token
        mock_db.exec.assert_called_once()

    def test_get_by_jti_not_found(self):
        """Should return None when token not found."""
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None

        result = RefreshTokenRepository.get_by_jti(mock_db, "nonexistent")

        assert result is None


class TestRefreshTokenRepositoryGetValidTokenByJti:
    """Tests for RefreshTokenRepository.get_valid_token_by_jti."""

    def test_get_valid_token_found(self):
        """Should return token when valid (not expired, not revoked)."""
        mock_db = Mock()
        mock_token = RefreshTokenDB(
            id=1,
            jti="test-jti",
            token_hash="hash",
            user_uuid="user-uuid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=False
        )
        mock_db.exec.return_value.first.return_value = mock_token

        result = RefreshTokenRepository.get_valid_token_by_jti(mock_db, "test-jti")

        assert result == mock_token

    def test_get_valid_token_not_found(self):
        """Should return None when no valid token found."""
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None

        result = RefreshTokenRepository.get_valid_token_by_jti(mock_db, "test-jti")

        assert result is None


class TestRefreshTokenRepositoryCreate:
    """Tests for RefreshTokenRepository.create."""

    def test_create_token(self):
        """Should create and return new token."""
        mock_db = Mock()
        expires = datetime.now(timezone.utc) + timedelta(days=7)

        result = RefreshTokenRepository.create(
            mock_db,
            jti="new-jti",
            token_hash="hash",
            user_uuid="user-uuid",
            expires_at=expires
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result.jti == "new-jti"
        assert result.user_uuid == "user-uuid"


class TestRefreshTokenRepositoryRevoke:
    """Tests for RefreshTokenRepository.revoke."""

    def test_revoke_token(self):
        """Should set revoked=True and revoked_at."""
        mock_db = Mock()
        token = RefreshTokenDB(
            id=1,
            jti="test-jti",
            token_hash="hash",
            user_uuid="user-uuid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=False
        )

        result = RefreshTokenRepository.revoke(mock_db, token)

        assert token.revoked is True
        assert token.revoked_at is not None
        mock_db.add.assert_called_once_with(token)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(token)


class TestRefreshTokenRepositoryRevokeByJti:
    """Tests for RefreshTokenRepository.revoke_by_jti."""

    @patch.object(RefreshTokenRepository, 'get_by_jti')
    def test_revoke_by_jti_success(self, mock_get):
        """Should revoke token and return True."""
        mock_db = Mock()
        token = RefreshTokenDB(
            id=1,
            jti="test-jti",
            token_hash="hash",
            user_uuid="user-uuid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=False
        )
        mock_get.return_value = token

        result = RefreshTokenRepository.revoke_by_jti(mock_db, "test-jti")

        assert result is True
        assert token.revoked is True
        mock_db.add.assert_called_once_with(token)
        mock_db.commit.assert_called_once()

    @patch.object(RefreshTokenRepository, 'get_by_jti')
    def test_revoke_by_jti_not_found(self, mock_get):
        """Should return False when token not found."""
        mock_db = Mock()
        mock_get.return_value = None

        result = RefreshTokenRepository.revoke_by_jti(mock_db, "nonexistent")

        assert result is False
        mock_db.add.assert_not_called()

    @patch.object(RefreshTokenRepository, 'get_by_jti')
    def test_revoke_by_jti_already_revoked(self, mock_get):
        """Should return False when token already revoked."""
        mock_db = Mock()
        token = RefreshTokenDB(
            id=1,
            jti="test-jti",
            token_hash="hash",
            user_uuid="user-uuid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=True  # Already revoked
        )
        mock_get.return_value = token

        result = RefreshTokenRepository.revoke_by_jti(mock_db, "test-jti")

        assert result is False
        mock_db.add.assert_not_called()


class TestRefreshTokenRepositoryRevokeAllForUser:
    """Tests for RefreshTokenRepository.revoke_all_for_user."""

    def test_revoke_all_for_user(self):
        """Should revoke all tokens and return count."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.rowcount = 3
        mock_db.exec.return_value = mock_result

        result = RefreshTokenRepository.revoke_all_for_user(mock_db, "user-uuid")

        assert result == 3
        mock_db.exec.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_revoke_all_for_user_none(self):
        """Should return 0 when no tokens to revoke."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_db.exec.return_value = mock_result

        result = RefreshTokenRepository.revoke_all_for_user(mock_db, "user-uuid")

        assert result == 0


class TestRefreshTokenRepositoryDeleteExpiredTokens:
    """Tests for RefreshTokenRepository.delete_expired_tokens."""

    def test_delete_expired_tokens(self):
        """Should delete expired tokens and return count."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.rowcount = 5
        mock_db.exec.return_value = mock_result

        result = RefreshTokenRepository.delete_expired_tokens(mock_db)

        assert result == 5
        mock_db.exec.assert_called_once()
        mock_db.commit.assert_called_once()


class TestRefreshTokenRepositoryCountActiveTokensForUser:
    """Tests for RefreshTokenRepository.count_active_tokens_for_user."""

    def test_count_active_tokens(self):
        """Should return count of active tokens."""
        mock_db = Mock()
        mock_db.exec.return_value.one.return_value = 3

        result = RefreshTokenRepository.count_active_tokens_for_user(mock_db, "user-uuid")

        assert result == 3

    def test_count_active_tokens_zero(self):
        """Should return 0 when no active tokens."""
        mock_db = Mock()
        mock_db.exec.return_value.one.return_value = 0

        result = RefreshTokenRepository.count_active_tokens_for_user(mock_db, "user-uuid")

        assert result == 0


class TestRefreshTokenRepositoryRevokeOldestTokens:
    """Tests for RefreshTokenRepository.revoke_oldest_tokens."""

    def test_revoke_oldest_token_success(self):
        """Should revoke oldest token and return True."""
        mock_db = Mock()
        oldest_token = RefreshTokenDB(
            id=1,
            jti="oldest-jti",
            token_hash="hash",
            user_uuid="user-uuid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=False
        )
        mock_db.exec.return_value.first.return_value = oldest_token

        result = RefreshTokenRepository.revoke_oldest_tokens(mock_db, "user-uuid")

        assert result is True
        assert oldest_token.revoked is True
        mock_db.add.assert_called_once_with(oldest_token)
        mock_db.commit.assert_called_once()

    def test_revoke_oldest_token_none_found(self):
        """Should return False when no active tokens found."""
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None

        result = RefreshTokenRepository.revoke_oldest_tokens(mock_db, "user-uuid")

        assert result is False
        mock_db.add.assert_not_called()
