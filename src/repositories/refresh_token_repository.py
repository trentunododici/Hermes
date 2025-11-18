from sqlmodel import Session, col, select
from src.database.models import RefreshTokenDB
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import func

class RefreshTokenRepository:
    """Repository for CRUD operations on refresh tokens"""

    @staticmethod
    def get_by_jti(db: Session, jti: str) -> Optional[RefreshTokenDB]:
        """Get a refresh token by JTI (JWT ID)"""
        statement = select(RefreshTokenDB).where(RefreshTokenDB.jti == jti)
        return db.exec(statement).first()
    
    @staticmethod
    def get_valid_token_by_jti(db: Session, jti: str) -> Optional[RefreshTokenDB]:
        """Get a valid (not expired, not revoked) refresh token by JTI (JWT ID)"""
        now = datetime.now(timezone.utc)
        statement = select(RefreshTokenDB).where(
            RefreshTokenDB.jti == jti,
            RefreshTokenDB.revoked == False,
            RefreshTokenDB.expires_at > now
        )
        return db.exec(statement).first()

    @staticmethod
    def create(db: Session, jti: str, token_hash: str, user_uuid: str, expires_at: datetime) -> RefreshTokenDB:
        """Create a new refresh token for a user in the database"""
        refresh_token = RefreshTokenDB(
            jti=jti,
            token_hash=token_hash,
            user_uuid=user_uuid,
            expires_at=expires_at,
        )
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        return refresh_token

    @staticmethod
    def revoke(db: Session, refresh_token: RefreshTokenDB) -> RefreshTokenDB:
        """Revoke a refresh token (soft delete)"""
        refresh_token.revoked = True
        refresh_token.revoked_at = datetime.now(timezone.utc)
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        return refresh_token
    
    @staticmethod
    def revoke_by_jti(db: Session, jti: str) -> bool:
        """Revoke a refresh token by its JTI (JWT ID)"""
        token = RefreshTokenRepository.get_by_jti(db, jti)
        if token and not token.revoked:
            token.revoked = True
            token.revoked_at = datetime.now(timezone.utc)
            db.add(token)
            db.commit()
            return True
        return False
    
    @staticmethod
    def revoke_all_for_user(db: Session, user_uuid: str) -> int:
        """Revoke all refresh tokens for a specific user. Returns the count of revoked tokens."""
        statement = select(RefreshTokenDB).where(
            RefreshTokenDB.user_uuid == user_uuid,
            RefreshTokenDB.revoked == False
        )
        tokens = db.exec(statement).all()
        
        revoked_count = 0
        for token in tokens:
            token.revoked = True
            token.revoked_at = datetime.now(timezone.utc)
            db.add(token)
            revoked_count += 1
        db.commit()
        return revoked_count
    
    @staticmethod
    def delete_expired_tokens(db: Session) -> int:
        """Delete all expired refresh tokens from the database. Returns the count of deleted tokens."""
        now = datetime.now(timezone.utc)
        statement = select(RefreshTokenDB).where(
            RefreshTokenDB.expires_at < now
        )
        expired_tokens = db.exec(statement).all()
        
        deleted_count = len(expired_tokens)
        for token in expired_tokens:
            db.delete(token)

        db.commit()
        return deleted_count
    
    @staticmethod
    def count_active_tokens_for_user(db: Session, user_uuid: str) -> int:
        """Count the number of active (not revoked, not expired) refresh tokens for a specific user."""
        now = datetime.now(timezone.utc)
        statement = select(func.count()).select_from(RefreshTokenDB).where(
            RefreshTokenDB.user_uuid == user_uuid,
            RefreshTokenDB.revoked == False,
            RefreshTokenDB.expires_at > now
        )

        result = db.exec(statement).one()
        return result
    
    @staticmethod
    def revoke_oldest_tokens(db: Session, user_uuid: str) -> bool:
        """Revoke the oldest active token for a user."""
        statement = select(RefreshTokenDB).where(
            RefreshTokenDB.user_uuid == user_uuid,
            RefreshTokenDB.revoked == False
        ).order_by(col(RefreshTokenDB.created_at)).limit(1)

        oldest = db.exec(statement).first()
        if oldest:
            oldest.revoked = True
            oldest.revoked_at = datetime.now(timezone.utc)
            db.add(oldest)
            db.commit()
            return True
        return False
    