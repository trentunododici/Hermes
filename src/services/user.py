from src.database.models import UserDB
from src.repositories.user_repository import UserRepository
from src.utils.security import get_password_hash
from src.schemas.user import User, UserInDB
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

def get_user(db: Session, username: str) -> UserInDB | None:
    """Get user with hashed password - for authentication only"""
    user = UserRepository.get_by_username(db, username)
    if user:
        return UserInDB.model_validate(user.model_dump())
    return None

def get_user_by_uuid(db: Session, uuid: str) -> User | None:
    """Get user without password - safe for general use"""
    user = UserRepository.get_by_uuid(db, uuid)
    if user:
        return User.model_validate(user.model_dump())
    return None

def add_user(
        session: Session,
        username: str,
        email: str,
        full_name: str,
        password: str
    ) -> UserDB | None:
    """
    Create a new user in the database.

    Returns None if user already exists (duplicate username or email).
    Relies on database unique constraints for data integrity,
    preventing race conditions through database-level enforcement.
    """
    try:
        hashed_password = get_password_hash(password)
        db_user = UserDB(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            disabled=False
        )

        return UserRepository.create(session, db_user)
    except IntegrityError:
        # Unique constraint violation (username or email already exists)
        # Rollback is handled automatically by SQLModel
        session.rollback()
        return None