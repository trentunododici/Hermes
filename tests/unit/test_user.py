"""Unit tests for user service (src/services/user.py)."""
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from src.services.user import get_user, get_user_by_uuid, add_user, deactivate_user
from src.database.models import UserDB
from src.schemas.user import User, UserInDB


class TestGetUser:
    """Tests for get_user function."""

    @patch('src.services.user.UserRepository')
    def test_get_user_found(self, mock_repo):
        """Should return UserInDB when user exists."""
        mock_db = Mock()
        mock_user_db = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_repo.get_by_username.return_value = mock_user_db

        result = get_user(mock_db, "testuser")

        assert result is not None
        assert isinstance(result, UserInDB)
        assert result.username == "testuser"
        assert result.hashed_password == "hashed_password"
        mock_repo.get_by_username.assert_called_once_with(mock_db, "testuser")

    @patch('src.services.user.UserRepository')
    def test_get_user_not_found(self, mock_repo):
        """Should return None when user doesn't exist."""
        mock_db = Mock()
        mock_repo.get_by_username.return_value = None

        result = get_user(mock_db, "nonexistent")

        assert result is None
        mock_repo.get_by_username.assert_called_once_with(mock_db, "nonexistent")


class TestGetUserByUuid:
    """Tests for get_user_by_uuid function."""

    @patch('src.services.user.UserRepository')
    def test_get_user_by_uuid_found(self, mock_repo):
        """Should return User (without password) when user exists."""
        mock_db = Mock()
        mock_user_db = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_repo.get_by_uuid.return_value = mock_user_db

        result = get_user_by_uuid(mock_db, "test-uuid")

        assert result is not None
        assert isinstance(result, User)
        assert result.uuid == "test-uuid"
        assert 'hashed_password' not in result.model_dump()
        mock_repo.get_by_uuid.assert_called_once_with(mock_db, "test-uuid")

    @patch('src.services.user.UserRepository')
    def test_get_user_by_uuid_not_found(self, mock_repo):
        """Should return None when user doesn't exist."""
        mock_db = Mock()
        mock_repo.get_by_uuid.return_value = None

        result = get_user_by_uuid(mock_db, "nonexistent-uuid")

        assert result is None
        mock_repo.get_by_uuid.assert_called_once_with(mock_db, "nonexistent-uuid")


class TestAddUser:
    """Tests for add_user function."""

    @patch('src.services.user.UserRepository')
    @patch('src.services.user.get_password_hash')
    def test_add_user_success(self, mock_hash, mock_repo):
        """Should create user and return UserDB."""
        mock_db = Mock()
        mock_hash.return_value = "hashed_password"

        # Mock the created user
        created_user = UserDB(
            id=1,
            uuid="new-uuid",
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
            hashed_password="hashed_password",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_repo.create.return_value = created_user

        result = add_user(
            session=mock_db,
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
            password="SecurePass123!"
        )

        assert result is not None
        assert result.username == "newuser"
        assert result.hashed_password == "hashed_password"
        mock_hash.assert_called_once_with("SecurePass123!")
        mock_repo.create.assert_called_once()

    @patch('src.services.user.UserRepository')
    @patch('src.services.user.get_password_hash')
    def test_add_user_duplicate_returns_none(self, mock_hash, mock_repo):
        """Should return None when username/email already exists."""
        mock_db = Mock()
        mock_hash.return_value = "hashed_password"
        mock_repo.create.side_effect = IntegrityError(None, None, None)

        result = add_user(
            session=mock_db,
            username="existinguser",
            email="existing@example.com",
            first_name="Existing",
            last_name="User",
            password="SecurePass123!"
        )

        assert result is None
        mock_db.rollback.assert_called_once()

    @patch('src.services.user.UserRepository')
    @patch('src.services.user.get_password_hash')
    def test_add_user_custom_created_at(self, mock_hash, mock_repo):
        """Should use custom created_at when provided."""
        mock_db = Mock()
        mock_hash.return_value = "hashed_password"
        custom_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        created_user = UserDB(
            id=1,
            uuid="new-uuid",
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
            hashed_password="hashed_password",
            disabled=False,
            created_at=custom_time
        )
        mock_repo.create.return_value = created_user

        result = add_user(
            session=mock_db,
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
            password="SecurePass123!",
            created_at=custom_time
        )

        assert result is not None
        # Verify the UserDB was created with custom time
        call_args = mock_repo.create.call_args
        created_db_user = call_args[0][1]
        assert created_db_user.created_at == custom_time

    @patch('src.services.user.UserRepository')
    @patch('src.services.user.get_password_hash')
    def test_add_user_sets_disabled_false(self, mock_hash, mock_repo):
        """New users should be created with disabled=False."""
        mock_db = Mock()
        mock_hash.return_value = "hashed_password"

        created_user = UserDB(
            id=1,
            uuid="new-uuid",
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
            hashed_password="hashed_password",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_repo.create.return_value = created_user

        add_user(
            session=mock_db,
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
            password="SecurePass123!"
        )

        # Verify disabled is False
        call_args = mock_repo.create.call_args
        created_db_user = call_args[0][1]
        assert created_db_user.disabled is False


class TestDeactivateUser:
    """Tests for deactivate_user function."""

    @patch('src.services.user.UserRepository')
    def test_deactivate_user_success(self, mock_repo):
        """Should set disabled=True and update user."""
        mock_db = Mock()
        user = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_repo.update.return_value = user

        deactivate_user(mock_db, user)

        assert user.disabled is True
        mock_repo.update.assert_called_once_with(mock_db, user)

    @patch('src.services.user.UserRepository')
    def test_deactivate_user_already_disabled(self, mock_repo):
        """Should skip DB write if user already disabled."""
        mock_db = Mock()
        user = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
            disabled=True,  # Already disabled
            created_at=datetime.now(timezone.utc)
        )

        result = deactivate_user(mock_db, user)

        assert result == user
        mock_repo.update.assert_not_called()
