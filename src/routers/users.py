from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from src.database.connection import get_db
from src.repositories.user_repository import UserRepository
from src.schemas.user import User
from src.services.user import deactivate_user
from sqlmodel import Session
from src.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/me",
            response_model=User,
            summary="Get Current User",
            description="Retrieve information about the currently authenticated user.",
            response_description="Details of the current user")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user

@router.delete("/me",
               status_code=200,
               summary="Deactivate Current User",
               description="Deactivate the account of the currently authenticated user.",
               response_description="Confirmation message of account deactivation")
async def deactivate_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_db)],
    permanent: bool = False # Query parameter to indicate permanent deletion
) -> dict:
    user_db = UserRepository.get_by_uuid(session, current_user.uuid)
    # Should be impossible in normal flow, but fail clearly if it happens
    if user_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if permanent:
        # Hard delete
        # UserRepository.delete(session, user_db)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Permanent deletion is not implemented yet"
        )
    deactivate_user(session=session, user=user_db)
    return {"message": "User account deactivated successfully"}