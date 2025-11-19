"""Unit tests for user repository (src/repositories/user_repository.py)."""
from unittest.mock import Mock
from datetime import datetime, timezone

from src.repositories.user_repository import UserRepository
from src.database.models import UserDB


class TestUserRepositoryGetByUsername:
    """Tests for UserRepository.get_by_username."""

    def test_get_by_username_found(self):
        """Should return user when found."""
        mock_db = Mock()
        mock_user = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_db.exec.return_value.first.return_value = mock_user

        result = UserRepository.get_by_username(mock_db, "testuser")

        assert result == mock_user
        mock_db.exec.assert_called_once()

    def test_get_by_username_not_found(self):
        """Should return None when user not found."""
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None

        result = UserRepository.get_by_username(mock_db, "nonexistent")

        assert result is None


class TestUserRepositoryGetByEmail:
    """Tests for UserRepository.get_by_email."""

    def test_get_by_email_found(self):
        """Should return user when found."""
        mock_db = Mock()
        mock_user = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_db.exec.return_value.first.return_value = mock_user

        result = UserRepository.get_by_email(mock_db, "test@example.com")

        assert result == mock_user

    def test_get_by_email_not_found(self):
        """Should return None when email not found."""
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None

        result = UserRepository.get_by_email(mock_db, "notfound@example.com")

        assert result is None


class TestUserRepositoryGetByUuid:
    """Tests for UserRepository.get_by_uuid."""

    def test_get_by_uuid_found(self):
        """Should return user when found."""
        mock_db = Mock()
        mock_user = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_db.exec.return_value.first.return_value = mock_user

        result = UserRepository.get_by_uuid(mock_db, "test-uuid")

        assert result == mock_user

    def test_get_by_uuid_not_found(self):
        """Should return None when uuid not found."""
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None

        result = UserRepository.get_by_uuid(mock_db, "nonexistent-uuid")

        assert result is None


class TestUserRepositoryGetById:
    """Tests for UserRepository.get_by_id."""

    def test_get_by_id_found(self):
        """Should return user when found."""
        mock_db = Mock()
        mock_user = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_db.exec.return_value.first.return_value = mock_user

        result = UserRepository.get_by_id(mock_db, 1)

        assert result == mock_user

    def test_get_by_id_not_found(self):
        """Should return None when id not found."""
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None

        result = UserRepository.get_by_id(mock_db, 999)

        assert result is None


class TestUserRepositoryCreate:
    """Tests for UserRepository.create."""

    def test_create_user(self):
        """Should add user to database and return it."""
        mock_db = Mock()
        user = UserDB(
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
            hashed_password="hashed",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )

        result = UserRepository.create(mock_db, user)

        mock_db.add.assert_called_once_with(user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(user)
        assert result == user


class TestUserRepositoryUpdate:
    """Tests for UserRepository.update."""

    def test_update_user(self):
        """Should update user and set updated_at."""
        mock_db = Mock()
        user = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )

        result = UserRepository.update(mock_db, user)

        assert user.updated_at is not None
        mock_db.add.assert_called_once_with(user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(user)
        assert result == user


class TestUserRepositoryDelete:
    """Tests for UserRepository.delete."""

    def test_delete_user(self):
        """Should delete user from database."""
        mock_db = Mock()
        user = UserDB(
            id=1,
            uuid="test-uuid",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed",
            disabled=False,
            created_at=datetime.now(timezone.utc)
        )

        UserRepository.delete(mock_db, user)

        mock_db.delete.assert_called_once_with(user)
        mock_db.commit.assert_called_once()
