from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.model import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_clerk_id(self, clerk_user_id: str) -> User | None:
        statement = select(User).where(User.clerk_user_id == clerk_user_id)
        return await self._session.scalar(statement)

    async def get_or_create(self, clerk_user_id: str) -> User:
        statement = (
            insert(User)
            .values(clerk_user_id=clerk_user_id)
            .on_conflict_do_nothing(index_elements=[User.clerk_user_id])
            .returning(User)
        )
        created_user = await self._session.scalar(statement)
        if created_user is not None:
            return created_user

        existing_user = await self.get_by_clerk_id(clerk_user_id)
        if existing_user is None:
            raise RuntimeError("Could not find the user after an insert conflict.")

        return existing_user