from typing import Annotated
from fastapi import APIRouter, Depends
from src.schemas.user import User
from src.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/me",
            response_model=User,
            summary="Get Current User",
            description="Retrieve information about the currently authenticated user.",
            response_description="Details of the current user")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user
