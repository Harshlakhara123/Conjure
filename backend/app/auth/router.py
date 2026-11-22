from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import require_clerk_user
from app.db_session import get_db_session
from app.users.repository import UserRepository
from app.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/bootstrap", response_model=UserResponse)
async def bootstrap_user(
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    repository = UserRepository(session)

    async with session.begin():
        user = await repository.get_or_create(clerk_user_id)

    return UserResponse.model_validate(user)