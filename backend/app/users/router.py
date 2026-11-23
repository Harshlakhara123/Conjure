from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.access import require_application_user
from app.auth.clerk import require_clerk_user
from app.db_session import get_db_session
from app.users.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    user = await require_application_user(session, clerk_user_id)
    return UserResponse.model_validate(user)
