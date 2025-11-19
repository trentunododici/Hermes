"""Unit tests for auth service (src/services/auth.py)."""
import random
import pytest
import jwt
from unittest.mock import Mock, patch
from datetime import timedelta, datetime, timezone

from src.services.auth import create_access_token, create_refresh_token, authenticate_user, verify_refresh_token
from src.config import SECRET_KEY, REFRESH_SECRET_KEY, ALGORITHM, JWT_ISSUER, JWT_AUDIENCE
from src.schemas.auth import TokenType
from src.schemas.user import User, UserInDB
from src.database.models import RefreshTokenDB


class TestCreateAccessToken:
    """Tests for access token creation."""

    def test_create_access_token_returns_string(self):
        """Access token should be a non-empty string."""
        token = create_access_token(data={"sub": "user-uuid"})

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_is_valid_jwt(self):
        """Access token should be a valid JWT."""
        token = create_access_token(data={"sub": "user-uuid"})

        # Should not raise
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload is not None

    def test_create_access_token_contains_sub(self):
        """Access token should contain subject claim."""
        user_uuid = "test-user-uuid"
        token = create_access_token(data={"sub": user_uuid})

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload["sub"] == user_uuid

    def test_create_access_token_contains_type(self):
        """Access token should have type 'access'."""
        token = create_access_token(data={"sub": "user-uuid"})

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload["type"] == TokenType.ACCESS

    def test_create_access_token_contains_expiration(self):
        """Access token should have expiration claim."""
        token = create_access_token(data={"sub": "user-uuid"})

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert "exp" in payload
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_create_access_token_custom_expiration(self):
        """Access token should respect custom expiration delta."""
        expires = timedelta(minutes=5)
        token = create_access_token(data={"sub": "user-uuid"}, expires_delta=expires)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)

        # Expiration should be approximately 5 minutes from now
        expected_exp = datetime.now(timezone.utc) + expires
        actual_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        # Allow 2 seconds tolerance
        assert abs((expected_exp - actual_exp).total_seconds()) < 2

    def test_create_access_token_contains_iat(self):
        """Access token should have issued-at claim."""
        token = create_access_token(data={"sub": "user-uuid"})

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert "iat" in payload

    def test_create_access_token_contains_issuer(self):
        """Access token should have issuer claim."""
        token = create_access_token(data={"sub": "user-uuid"})

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload["iss"] == JWT_ISSUER

    def test_create_access_token_contains_audience(self):
        """Access token should have audience claim."""
        token = create_access_token(data={"sub": "user-uuid"})

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload["aud"] == JWT_AUDIENCE

    def test_create_access_token_wrong_key_fails(self):
        """Access token should not decode with wrong key."""
        token = create_access_token(data={"sub": "user-uuid"})

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong-key", algorithms=[ALGORITHM], audience=JWT_AUDIENCE)


class TestCreateRefreshToken:
    """Tests for refresh token creation."""

    def test_create_refresh_token_returns_tuple(self):
        """Refresh token should return (token, jti, expire)."""
        result = create_refresh_token(data={"sub": "user-uuid"})

        assert isinstance(result, tuple)
        assert len(result) == 3

        token, jti, expire = result
        assert isinstance(token, str)
        assert isinstance(jti, str)
        assert isinstance(expire, datetime)

    def test_create_refresh_token_is_valid_jwt(self):
        """Refresh token should be a valid JWT."""
        token, _, _ = create_refresh_token(data={"sub": "user-uuid"})

        # Should not raise
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload is not None

    def test_create_refresh_token_contains_jti(self):
        """Refresh token should contain unique jti claim."""
        token, jti, _ = create_refresh_token(data={"sub": "user-uuid"})

        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload["jti"] == jti
        assert len(jti) > 0

    def test_create_refresh_token_jti_is_unique(self):
        """Each refresh token should have unique jti."""
        _, jti1, _ = create_refresh_token(data={"sub": "user-uuid"})
        _, jti2, _ = create_refresh_token(data={"sub": "user-uuid"})

        assert jti1 != jti2

    def test_create_refresh_token_contains_type(self):
        """Refresh token should have type 'refresh'."""
        token, _, _ = create_refresh_token(data={"sub": "user-uuid"})

        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload["type"] == TokenType.REFRESH

    def test_create_refresh_token_uses_different_key(self):
        """Refresh token should use different secret key than access token."""
        token, _, _ = create_refresh_token(data={"sub": "user-uuid"})

        # Should fail with access token key
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)

        # Should succeed with refresh token key
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload is not None

    def test_create_refresh_token_custom_expiration(self):
        """Refresh token should respect custom expiration delta."""
        expires = timedelta(days=1)
        token, _, expire = create_refresh_token(data={"sub": "user-uuid"}, expires_delta=expires)

        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)

        # Expiration should be approximately 1 day from now
        expected_exp = datetime.now(timezone.utc) + expires

        # Allow 2 seconds tolerance
        assert abs((expected_exp - expire).total_seconds()) < 2

    def test_create_refresh_token_contains_issuer(self):
        """Refresh token should have issuer claim."""
        token, _, _ = create_refresh_token(data={"sub": "user-uuid"})

        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        assert payload["iss"] == JWT_ISSUER


class TestTokenTypesSeparation:
    """Tests to ensure access and refresh tokens are properly separated."""

    def test_access_token_cannot_decode_with_refresh_key(self):
        """Access token should not decode with refresh secret key."""
        access_token = create_access_token(data={"sub": "user-uuid"})

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(access_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)

    def test_refresh_token_cannot_decode_with_access_key(self):
        """Refresh token should not decode with access secret key."""
        refresh_token, _, _ = create_refresh_token(data={"sub": "user-uuid"})

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)

    def test_tokens_have_different_types(self):
        """Access and refresh tokens should have different type claims."""
        access_token = create_access_token(data={"sub": "user-uuid"})
        refresh_token, _, _ = create_refresh_token(data={"sub": "user-uuid"})

        access_payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
        refresh_payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)

        assert access_payload["type"] == TokenType.ACCESS
        assert refresh_payload["type"] == TokenType.REFRESH
        assert access_payload["type"] != refresh_payload["type"]


class TestAuthenticateUser:
    """Tests for authenticate_user function."""

    @patch('src.services.auth.verify_password')
    @patch('src.services.auth.get_user')
    @patch('src.services.auth.normalize_username')
    def test_authenticate_user_success(self, mock_normalize, mock_get_user, mock_verify):
        """Should return User when credentials are valid."""
        mock_db = Mock()
        mock_normalize.return_value = "testuser"
        mock_user = UserInDB(
            id=random.randint(1, 1000),
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
            disabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_verify.return_value = True

        result = authenticate_user(mock_db, "testuser", "password123")

        assert result is not None
        assert result.username == "testuser"
        mock_verify.assert_called_once_with("password123", "hashed_password")

    @patch('src.services.auth.verify_password')
    @patch('src.services.auth.get_user')
    @patch('src.services.auth.normalize_username')
    def test_authenticate_user_wrong_password(self, mock_normalize, mock_get_user, mock_verify):
        """Should return None when password is wrong."""
        mock_db = Mock()
        mock_normalize.return_value = "testuser"
        mock_user = UserInDB(
            id=random.randint(1, 1000),
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
            disabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_verify.return_value = False

        result = authenticate_user(mock_db, "testuser", "wrongpassword")

        assert result is None

    @patch('src.services.auth.verify_password')
    @patch('src.services.auth.get_user')
    @patch('src.services.auth.normalize_username')
    def test_authenticate_user_not_found(self, mock_normalize, mock_get_user, mock_verify):
        """Should return None when user doesn't exist."""
        mock_db = Mock()
        mock_normalize.return_value = "nonexistent"
        mock_get_user.return_value = None
        mock_verify.return_value = False  # Dummy hash verification

        result = authenticate_user(mock_db, "nonexistent", "password123")

        assert result is None
        # Should still verify password (timing attack mitigation)
        mock_verify.assert_called_once()

    @patch('src.services.auth.verify_password')
    @patch('src.services.auth.get_user')
    @patch('src.services.auth.normalize_username')
    def test_authenticate_user_invalid_username(self, mock_normalize, mock_get_user, mock_verify):
        """Should return None when username is invalid."""
        mock_db = Mock()
        mock_normalize.side_effect = ValueError("Invalid username")
        mock_verify.return_value = False

        result = authenticate_user(mock_db, "ab", "password123")

        assert result is None


class TestVerifyRefreshToken:
    """Tests for verify_refresh_token function."""

    @patch('src.services.auth.get_user_by_uuid')
    @patch('src.services.auth.hash_token')
    @patch('src.services.auth.RefreshTokenRepository')
    def test_verify_refresh_token_success(self, mock_repo, mock_hash, mock_get_user):
        """Should return User and jti when token is valid."""
        mock_db = Mock()

        # Create a valid refresh token
        token, jti, _ = create_refresh_token(data={"sub": "test-uuid"})

        # Mock token record
        mock_token_record = Mock()
        mock_token_record.user_uuid = "test-uuid"
        mock_token_record.token_hash = "calculated_hash"
        mock_repo.get_valid_token_by_jti.return_value = mock_token_record

        # Mock hash calculation
        mock_hash.return_value = "calculated_hash"

        # Mock user
        mock_user = User(
            id=random.randint(1, 1000),
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            disabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user

        result = verify_refresh_token(mock_db, token)

        assert result is not None
        user, returned_jti = result
        assert user.uuid == "test-uuid"
        assert returned_jti == jti

    @patch('src.services.auth.RefreshTokenRepository')
    def test_verify_refresh_token_invalid_jwt(self, mock_repo):
        """Should return None for invalid JWT."""
        mock_db = Mock()

        result = verify_refresh_token(mock_db, "invalid.token.here")

        assert result is None
        mock_repo.get_valid_token_by_jti.assert_not_called()

    @patch('src.services.auth.RefreshTokenRepository')
    def test_verify_refresh_token_wrong_type(self, mock_repo):
        """Should return None when using access token."""
        mock_db = Mock()

        # Create an access token instead of refresh
        access_token = create_access_token(data={"sub": "test-uuid"})

        result = verify_refresh_token(mock_db, access_token)

        assert result is None

    @patch('src.services.auth.RefreshTokenRepository')
    def test_verify_refresh_token_not_in_database(self, mock_repo):
        """Should return None when token not found in database."""
        mock_db = Mock()
        token, _, _ = create_refresh_token(data={"sub": "test-uuid"})
        mock_repo.get_valid_token_by_jti.return_value = None

        result = verify_refresh_token(mock_db, token)

        assert result is None

    @patch('src.services.auth.hash_token')
    @patch('src.services.auth.RefreshTokenRepository')
    def test_verify_refresh_token_hash_mismatch(self, mock_repo, mock_hash):
        """Should return None when token hash doesn't match."""
        mock_db = Mock()
        token, _, _ = create_refresh_token(data={"sub": "test-uuid"})

        mock_token_record = Mock()
        mock_token_record.user_uuid = "test-uuid"
        mock_token_record.token_hash = "stored_hash"
        mock_repo.get_valid_token_by_jti.return_value = mock_token_record

        mock_hash.return_value = "different_hash"

        result = verify_refresh_token(mock_db, token)

        assert result is None

    @patch('src.services.auth.get_user_by_uuid')
    @patch('src.services.auth.hash_token')
    @patch('src.services.auth.RefreshTokenRepository')
    def test_verify_refresh_token_user_not_found(self, mock_repo, mock_hash, mock_get_user):
        """Should return None when user doesn't exist."""
        mock_db = Mock()
        token, _, _ = create_refresh_token(data={"sub": "test-uuid"})

        mock_token_record = Mock()
        mock_token_record.user_uuid = "test-uuid"
        mock_token_record.token_hash = "hash"
        mock_repo.get_valid_token_by_jti.return_value = mock_token_record

        mock_hash.return_value = "hash"
        mock_get_user.return_value = None

        result = verify_refresh_token(mock_db, token)

        assert result is None

    @patch('src.services.auth.get_user_by_uuid')
    @patch('src.services.auth.hash_token')
    @patch('src.services.auth.RefreshTokenRepository')
    def test_verify_refresh_token_user_disabled(self, mock_repo, mock_hash, mock_get_user):
        """Should return None when user is disabled."""
        mock_db = Mock()
        token, _, _ = create_refresh_token(data={"sub": "test-uuid"})

        mock_token_record = Mock()
        mock_token_record.user_uuid = "test-uuid"
        mock_token_record.token_hash = "hash"
        mock_repo.get_valid_token_by_jti.return_value = mock_token_record

        mock_hash.return_value = "hash"

        mock_user = User(
            id=random.randint(1, 1000),
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            disabled=True,  # User is disabled
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user

        result = verify_refresh_token(mock_db, token)

        assert result is None

    @patch('src.services.auth.RefreshTokenRepository')
    def test_verify_refresh_token_uuid_mismatch(self, mock_repo):
        """Should return None when JWT subject doesn't match DB record."""
        mock_db = Mock()
        token, _, _ = create_refresh_token(data={"sub": "test-uuid"})

        mock_token_record = Mock()
        mock_token_record.user_uuid = "different-uuid"  # Different from JWT
        mock_repo.get_valid_token_by_jti.return_value = mock_token_record

        result = verify_refresh_token(mock_db, token)

        assert result is None
