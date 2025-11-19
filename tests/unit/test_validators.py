"""Unit tests for validators (src/utils/validators.py)."""
import pytest

from src.utils.validators import normalize_username, validate_username, validate_password


class TestNormalizeUsername:
    """Tests for username normalization."""

    def test_normalize_lowercase(self):
        """Username should be lowercased."""
        assert normalize_username("TestUser") == "testuser"
        assert normalize_username("ALLCAPS") == "allcaps"

    def test_normalize_strips_whitespace(self):
        """Username should have whitespace stripped."""
        assert normalize_username("  testuser  ") == "testuser"
        assert normalize_username("\ttestuser\n") == "testuser"

    def test_normalize_empty_raises(self):
        """Empty username should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_username("")
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_username("   ")

    def test_normalize_too_short_raises(self):
        """Username shorter than 3 chars should raise ValueError."""
        with pytest.raises(ValueError, match="between 3 and 50"):
            normalize_username("ab")

    def test_normalize_too_long_raises(self):
        """Username longer than 50 chars should raise ValueError."""
        with pytest.raises(ValueError, match="between 3 and 50"):
            normalize_username("a" * 51)

    def test_normalize_valid_lengths(self):
        """Usernames at boundary lengths should be valid."""
        assert normalize_username("abc") == "abc"  # min length
        assert normalize_username("a" * 50) == "a" * 50  # max length


class TestValidateUsername:
    """Tests for username validation."""

    def test_validate_valid_username(self):
        """Valid usernames should pass."""
        assert validate_username("testuser") == "testuser"
        assert validate_username("test_user") == "test_user"
        assert validate_username("test.user") == "test.user"
        assert validate_username("test-user") == "test-user"
        assert validate_username("user123") == "user123"

    def test_validate_invalid_characters(self):
        """Usernames with invalid characters should raise ValueError."""
        with pytest.raises(ValueError, match="can only contain"):
            validate_username("test@user")
        with pytest.raises(ValueError, match="can only contain"):
            validate_username("test user")
        with pytest.raises(ValueError, match="can only contain"):
            validate_username("test#user")

    def test_validate_reserved_usernames(self):
        """Reserved usernames should raise ValueError."""
        with pytest.raises(ValueError, match="reserved"):
            validate_username("admin")
        with pytest.raises(ValueError, match="reserved"):
            validate_username("root")
        with pytest.raises(ValueError, match="reserved"):
            validate_username("superuser")
        with pytest.raises(ValueError, match="reserved"):
            validate_username("system")

    def test_validate_reserved_case_insensitive(self):
        """Reserved usernames should be caught regardless of case."""
        with pytest.raises(ValueError, match="reserved"):
            validate_username("ADMIN")
        with pytest.raises(ValueError, match="reserved"):
            validate_username("Root")


class TestValidatePassword:
    """Tests for password validation."""

    def test_validate_valid_password(self):
        """Valid passwords should pass."""
        assert validate_password("SecurePass1!") == "SecurePass1!"
        assert validate_password("MyP@ssw0rd") == "MyP@ssw0rd"
        assert validate_password("Complex-Password123") == "Complex-Password123"

    def test_validate_too_short(self):
        """Password shorter than 8 chars should raise ValueError."""
        with pytest.raises(ValueError, match="at least 8"):
            validate_password("Short1!")

    def test_validate_too_long(self):
        """Password longer than 128 chars should raise ValueError."""
        with pytest.raises(ValueError, match="at most 128"):
            validate_password("A1!" + "a" * 126)

    def test_validate_missing_uppercase(self):
        """Password without uppercase should raise ValueError."""
        with pytest.raises(ValueError, match="uppercase"):
            validate_password("lowercase1!")

    def test_validate_missing_lowercase(self):
        """Password without lowercase should raise ValueError."""
        with pytest.raises(ValueError, match="lowercase"):
            validate_password("UPPERCASE1!")

    def test_validate_missing_digit(self):
        """Password without digit should raise ValueError."""
        with pytest.raises(ValueError, match="digit"):
            validate_password("NoDigits!")

    def test_validate_missing_special(self):
        """Password without special character should raise ValueError."""
        with pytest.raises(ValueError, match="special"):
            validate_password("NoSpecial1")

    def test_validate_boundary_lengths(self):
        """Passwords at boundary lengths should work correctly."""
        # Exactly 8 characters
        assert validate_password("Abcdef1!") == "Abcdef1!"
        # Exactly 128 characters
        long_pass = "A1!" + "a" * 125
        assert validate_password(long_pass) == long_pass
