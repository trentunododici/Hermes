from sqlmodel import Session, select
from src.database.models import UserDB
from typing import Optional

class UserRepository:
    """Repository for CRUD operations on users"""

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[UserDB]:
        """Search for a user by username"""
        statement = select(UserDB).where(UserDB.username == username)
        return db.exec(statement).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[UserDB]:
        """Search for a user by email"""
        statement = select(UserDB).where(UserDB.email == email)
        return db.exec(statement).first()

    @staticmethod
    def get_by_uuid(db: Session, uuid: str) -> Optional[UserDB]:
        """Search for a user by UUID"""
        statement = select(UserDB).where(UserDB.uuid == uuid)
        return db.exec(statement).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[UserDB]:
        """Search for a user by ID"""
        statement = select(UserDB).where(UserDB.id == user_id)
        return db.exec(statement).first()

    @staticmethod
    def create(db: Session, user: UserDB) -> UserDB:
        """Create a new user in the database"""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: UserDB) -> UserDB:
        """Update an existing user"""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user: UserDB) -> None:
        """Delete a user from the database"""
        db.delete(user)
        db.commit()
