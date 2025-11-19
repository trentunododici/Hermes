"""Unit tests for security utilities (src/utils/security.py)."""

from src.utils.security import get_password_hash, verify_password, hash_token


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_hash(self):
        """Hash should return a non-empty string different from input."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (salt)."""
        password = "SecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert verify_password("WrongPassword456!", hashed) is False

    def test_verify_password_empty(self):
        """Empty password should fail verification."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert verify_password("", hashed) is False

    def test_hash_contains_algorithm_identifier(self):
        """Hash should contain argon2id identifier."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert "$argon2" in hashed


class TestTokenHashing:
    """Tests for token hashing function."""

    def test_hash_token_returns_hex(self):
        """Token hash should return hex string."""
        token = "some.jwt.token"
        hashed = hash_token(token)

        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 produces 64 hex characters

    def test_hash_token_deterministic(self):
        """Same token should produce same hash."""
        token = "some.jwt.token"
        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2

    def test_hash_token_different_tokens(self):
        """Different tokens should produce different hashes."""
        hash1 = hash_token("token1")
        hash2 = hash_token("token2")

        assert hash1 != hash2
